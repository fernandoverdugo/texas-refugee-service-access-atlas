from pathlib import Path
import pandas as pd

from src.analysis.accessibility import calculate_accessibility
from src.analysis.network import build_multimodal_graph, build_walking_transfer_edges, nearest_stops
from src.ingestion.geocoding import geocode_provider_inventory
from src.ingestion.geography import build_tract_points, download_texas_tracts, join_acs_to_tracts, load_study_tract_geometries
from src.ingestion.gtfs import DART_GTFS_URL
from src.ingestion.multimodal_gtfs import TRINITY_GTFS_URL, build_combined_transit_layer, download_zip
from src.ingestion.providers import load_provider_inventory

PROCESSED = Path("data/processed")

def main() -> None:
    acs = pd.read_csv(PROCESSED / "acs_dfw_tracts.csv", dtype={"geoid": str})
    providers = load_provider_inventory(PROCESSED / "provider_inventory.csv")

    tracts = load_study_tract_geometries(download_texas_tracts())
    tract_points = build_tract_points(tracts)
    tract_context = join_acs_to_tracts(tracts, acs)
    tract_context.to_file(PROCESSED / "tracts_dfw.geojson", driver="GeoJSON")
    tract_points.drop(columns="geometry").to_csv(PROCESSED / "tract_points_dfw.csv", index=False)

    cache_path = PROCESSED / "provider_locations.csv"
    cache = pd.read_csv(cache_path) if cache_path.exists() else None
    geocoded = geocode_provider_inventory(providers, cache=cache)
    if not geocoded["matched"].all():
        failed = geocoded.loc[~geocoded["matched"], "provider_id"].tolist()
        raise RuntimeError(f"Provider geocoding failed for: {failed}")
    geocoded.to_csv(PROCESSED / "provider_locations.csv", index=False)

    feeds = {
        "dart": download_zip(DART_GTFS_URL),
        "trinity": download_zip(TRINITY_GTFS_URL),
    }
    stops, transit_edges = build_combined_transit_layer(feeds)
    transfer_edges = build_walking_transfer_edges(stops)

    origin_connectors = nearest_stops(
        tract_points.drop(columns="geometry"), stops, "geoid", max_walk_km=1.0, max_stops=3
    )
    provider_connectors = nearest_stops(
        geocoded[["provider_id", "latitude", "longitude"]], stops, "provider_id", max_walk_km=1.0, max_stops=3
    )

    graph = build_multimodal_graph(transit_edges, transfer_edges)
    accessibility = calculate_accessibility(
        graph,
        origin_connectors,
        provider_connectors,
        all_geoids=tract_points["geoid"].astype(str).tolist(),
    )
    accessibility = accessibility.merge(
        acs[["geoid", "county_name", "population", "foreign_born_population", "population_below_poverty", "households_no_vehicle"]],
        on="geoid",
        how="left",
        validate="one_to_one",
    )

    stops.to_csv(PROCESSED / "combined_transit_stops.csv", index=False)
    transit_edges.to_csv(PROCESSED / "transit_edges.csv", index=False)
    transfer_edges.to_csv(PROCESSED / "transfer_edges.csv", index=False)
    origin_connectors.to_csv(PROCESSED / "tract_stop_connectors.csv", index=False)
    provider_connectors.to_csv(PROCESSED / "provider_stop_connectors.csv", index=False)
    accessibility.to_csv(PROCESSED / "tract_service_accessibility.csv", index=False)

    summary = {
        "tracts": len(tract_points),
        "providers": len(geocoded),
        "transit_stops": len(stops),
        "transit_edges": len(transit_edges),
        "walking_transfer_edges": len(transfer_edges),
        "tracts_with_stop_connector": origin_connectors["geoid"].nunique(),
        "providers_with_stop_connector": provider_connectors["provider_id"].nunique(),
        "tracts_reaching_any_provider": int((accessibility["reachable_providers"] > 0).sum()),
    }
    pd.DataFrame([summary]).to_csv(PROCESSED / "accessibility_summary.csv", index=False)
    print(summary)

if __name__ == "__main__":
    main()
