"""
    Converts raw scraped tour data into RAG-ready chunks with metadata.
    Reads from data/raw/asia_tour_details.json
    Writes to data/processed/chunks.json
"""
import json
import os
from app.config.settings import settings
from app.config.constants import ChunkType

"""
    Create a single overview chunk for a tour.
    Contains everything a user needs to decide if they're interested.
"""
def create_tour_overview_chunk(tour: dict) -> dict:

    parts = []

    name = tour.get("tour_name", "Unknown Tour")
    parts.append(f"{name}.")

    if tour.get("trip_code"):
        parts.append(f"Trip code: {tour['trip_code']}.")

    if tour.get("description"):
        parts.append(tour['description'])

    details = []
    if tour.get("duration_days"):
        details.append(f"{tour['duration_days']} days")
    if tour.get("style"):
        details.append(f"{tour['style']} style")
    if tour.get("theme"):
        details.append(f"{tour['theme']} theme")
    if tour.get("group_size_min") and tour.get("group_size_max"):
        details.append(f"group size {tour['group_size_min']}-{tour['group_size_max']}")
    if tour.get("min_age"):
        details.append(f"minimum age {tour['min_age']}")
    if details:
        parts.append(", ".join(details) + ".")

    if tour.get("start_location") and tour.get("end_location"):
        parts.append(f"Starts in {tour['start_location']}, ends in {tour['end_location']}.")

    if tour.get("price_usd"):
        parts.append(f"Price: USD ${tour['price_usd']}.")

    if tour.get("rating"):
        rating_str = f"Rating: {tour['rating']}/5"
        if tour.get("review_count"):
            rating_str += f" ({tour['review_count']} reviews)"
        parts.append(rating_str + ".")

    if tour.get("highlights"):
        parts.append("Highlights: " + " | ".join(tour["highlights"]))

    content = " ".join(parts)

    metadata = {
        "type": ChunkType.TOUR_OVERVIEW.value,
        "tour_name": name,
        "trip_code": tour.get("trip_code", ""),
        "destination": tour.get("destination", ""),
        "duration_days": tour.get("duration_days", 0),
        "price_usd": tour.get("price_usd", 0),
        "style": tour.get("style", ""),
        "theme": tour.get("theme", ""),
        "rating": tour.get("rating", 0),
        "source_url": tour.get("url", ""),
    }

    return {"content": content, "metadata": metadata}


"""
    Create one chunk per day of the itinerary.
    Each day is self-contained with location, activities, meals, accommodation.
"""
def create_itinerary_chunks(tour: dict) -> list[dict]:
    chunks = []
    tour_name = tour.get("tour_name", "Unknown Tour")
    trip_code = tour.get("trip_code", "")

    for day in tour.get("itinerary", []):
        parts = []

        parts.append(f"{tour_name} - Day {day['day']}: {day.get('location', '')}.")
        if day.get("description"):
            parts.append(day["description"])
        
        if day.get("accommodation"):
            parts.append(f"Accommodation: {day['accommodation']}.")

        if day.get("meals"):
            parts.append(f"Meals included: {', '.join(day['meals'])}.")
        else:
            parts.append("No meals included this day.")

        if day.get("included_activities"):
            parts.append("Included activities: " + ", ".join(day["included_activities"]) + ".")

        if day.get("optional_activities"):
            parts.append("Optional activities: " + ", ".join(day["optional_activities"]) + ".")

        if day.get("special_info"):
            parts.append(f"Note: {day['special_info']}")

        content = " ".join(parts)

        metadata = {
            "type": ChunkType.ITINERARY_DAY.value,
            "tour_name": tour_name,
            "trip_code": trip_code,
            "destination": tour.get("destination", ""),
            "day_number": day["day"],
            "location": day.get("location", ""),
            "source_url": tour.get("url", ""),
        }

        chunks.append({"content": content, "metadata": metadata})
    
    return chunks

"""
    Create a summary chunk with practical travel info:
    transport, accommodation types, total meals, all included activities.
"""
def create_practical_info_chunk(tour: dict) -> dict | None:
    tour_name = tour.get("tour_name", "Unknown Tour")
    parts = [f"{tour_name} - Practical information."]

    if tour.get("meals_summary"):
        parts.append(f"Meals included: {tour['meals_summary']}.")

    if tour.get("transport_summary"):
        parts.append(f"Transport: {tour['transport_summary']}.")

    if tour.get("accommodation_summary"):
        parts.append(f"Accommodation: {tour['accommodation_summary']}.")
    
    # Collect all included activities across all days
    all_included = []

    # Collect all optional activities across all days
    all_optional = []
    for day in tour.get("itinerary", []):
        all_included.extend(day.get("included_activities", []))
        all_optional.extend(day.get("optional_activities", []))
        
    if all_included:
        parts.append("All included activities: " + ", ".join(all_included) + ".")
       
    if all_optional:
        parts.append("All optional activities: " + ", ".join(all_optional) + ".")

    # Not enough info to be useful
    if len(parts) <= 1:
        return None
    
    content = " ".join(parts)

    metadata = {
        "type": ChunkType.PRACTICAL_INFO.value,
        "tour_name": tour_name,
        "trip_code": tour.get("trip_code", ""),
        "destination": tour.get("destination", ""),
        "source_url": tour.get("url", ""),
    }

    return {"content": content, "metadata": metadata}

"""Process all tours into RAG-ready chunks."""
def process_all_tours(tours: list[dict]) -> list[dict]:
    all_chunks = []

    for tour in tours:
        # 1. Tour overview chunk
        overview = create_tour_overview_chunk(tour)
        all_chunks.append(overview)

        # 2. Itinerary day chunks
        day_chunks = create_itinerary_chunks(tour)
        all_chunks.extend(day_chunks)

        # 3. Practical info chunk
        practical = create_practical_info_chunk(tour)
        if practical:
            all_chunks.append(practical)

    return all_chunks

# main function
def main():
    # Load raw scraped data
    input_path = settings.raw_data_dir / "asia_tour_details.json"

    if not input_path.exists():
        print(f"[ERROR] [PREPROCESSING_DATA] {input} not found")
        return
    
    with open(input_path, "r", encoding="utf-8") as f:
        tours = json.load(f)

    print(f"Loaded {len(tours)} tours from raw data.")

    # process into chunks
    chunks = process_all_tours(tours)

    # Add unique IDs
    for i, chunk in enumerate(chunks):
        chunk["id"] = f"chunk_{i:05d}"

    # Save
    settings.processed_data_dir.mkdir(parents=True, exist_ok=True)
    output_path = settings.processed_data_dir / "chunks.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    # print summary
    type_counts = {}
    for chunk in chunks:
        t = chunk["metadata"]["type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    print(f"\nDone! {len(chunks)} chunks saved to {output_path}")
    print(f"\nBreakdown:")
    for chunk_type, count in type_counts.items():
        print(f"{chunk_type}: {count}")
    
    # Show a sample
    print(f"\nSample overview chunk:")
    sample = next(c for c in chunks if c["metadata"]["type"] == ChunkType.TOUR_OVERVIEW.value)
    print(f"  Content: {sample['content'][:200]}...")
    print(f"  Metadata: {sample['metadata']}")

if __name__ == "__main__":
    main()
