# Visit each tour detail page and extract full structured data.
# Reads tour URLs from data/raw/asia_tour_listings.json

import requests
from bs4 import BeautifulSoup
import json
import time
import re
import os

# import instant
from app.config.settings import settings
from app.config.constants import ASIA_DESTINATIONS


## fetch the page
HEADER = {
    "User-Agent": settings.scraper_user_agent
}

"""Fetch a URL and return parsed BeautifulSoup."""
def fetch_page(url: str) -> BeautifulSoup | None:
    try:
        response = requests.get(url, headers=HEADER)
        response.raise_for_status()
        # Parse to beautiful soup
        return BeautifulSoup(response.text, "lxml")
    except:
        print(f"[ERROR][SCRAPE_DETAIL] fetch_page function error fetch {url}: {e}")
        return None
    

"""
Extract all structured data from a tour detail page.
"""
def extract_tour_detail(soup: BeautifulSoup, url: str) -> dict | None:
    # Get the full page text, line by line
    text = soup.get_text(separator="\n", strip=True)
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    tour = {"url": url}

    # print("===== data lines: ", lines)

    # --- TOUR NAME ---
    # The <h1> tag contains the tour name
    h1 = soup.find("h1")
    if h1:
        tour["tour_name"] = h1.get_text(strip=True)
    
    for i, line in enumerate(lines):
    
        # Trip code
        if "trip_code" not in tour:
            code_match = re.match(r"Trip code:\s*(\w+)", line)
            if code_match:
                tour["trip_code"] = code_match.group(1)
                continue

        # Start / End
        start_match = re.match(r"Start:\s*(.+)", line)
        if start_match:
            tour["start_location"] = start_match.group(1)
            continue
        end_match = re.match(r"End:\s*(.+)", line)
        if end_match:
            tour["end_location"] = end_match.group(1)
            continue

        # Duration
        if "duration_days" not in tour:
            dur_match = re.match(r"^(\d+)\s*days?$", line)
            if dur_match:
                tour["duration_days"] = int(dur_match.group(1))
                continue

        # Group size
        if "group_size_min" not in tour:
            group_match = re.match(r"^(\d+)\s*to\s*(\d+)$", line)
            if group_match:
                tour["group_size_min"] = int(group_match.group(1))
                tour["group_size_max"] = int(group_match.group(2))
                continue

        # Min age
        if "min_age" not in tour:
            age_match = re.search(r"(\d+)\s*years?\s*old", line)
            if age_match:
                tour["min_age"] = int(age_match.group(1))
                continue

        # Style
        if "style" not in tour and line in ["Basix", "Original", "Comfort", "Premium"]:
            tour["style"] = line
            continue

        # Theme
        if "theme" not in tour and line in [
            "Explorer", "Active", "Sailing", "Polar", "Family",
            "Food", "Cycling", "Walking & Hiking", "Festivals & Events", "Wildlife"
        ]:
            tour["theme"] = line
            continue

        # Rating & reviews
        if "rating" not in tour:
            rating_match = re.match(r"^(\d\.\d)$", line)
            if rating_match:
                tour["rating"] = float(rating_match.group(1))
                if i + 1 < len(lines):
                    rev_match = re.search(r"(\d+)\s*reviews?", lines[i + 1])
                    if rev_match:
                        tour["review_count"] = int(rev_match.group(1))
                continue

        # Price
        if "price_usd" not in tour:
            price_match = re.match(r"^\$([0-9,]+)$", line)
            if price_match and i > 0 and lines[i - 1].strip() == "USD":
                tour["price_usd"] = int(price_match.group(1).replace(",", ""))
                continue

    # --- DESCRIPTION ---
    # The long description paragraph after the tour name
    desc_candidates = [l for l in lines if len(l) > 200 and "cookie" not in l.lower()]
    if desc_candidates:
        tour["description"] = desc_candidates[0]
    
    # --- HIGHLIGHTS (Why you'll love this trip) ---
    tour["highlights"] = extract_highlights(lines)
    
    # --- ITINERARY ---
    tour["itinerary"] = extract_itinerary(lines)
    
    # --- SUMMARY SECTIONS ---
    tour["meals_summary"] = extract_after_label(lines, "Meals")
    tour["transport_summary"] = extract_after_label(lines, "Transport")
    tour["accommodation_summary"] = extract_after_label(lines, "Accommodation")
    
    return tour

"""Extract the 'Why you'll love this trip' bullet points."""
def extract_highlights(lines: list[str]) -> list[str]: 
    highlights = []
    in_section = False
    
    for line in lines:
        if "why you" in line.lower() and "love" in line.lower():
            in_section = True
            continue
        if in_section:
            # Highlights are usually longer sentences
            if line.lower().startswith("itinerary") or line.lower().startswith("map of"):
                break
            if len(line) > 30:
                highlights.append(line)
    
    return highlights


def extract_tour_links(soup: BeautifulSoup, destination: str) -> list[dict]:
    """
    Extract tour URLs and basic info from a destination listing page.
    
    Strategy: Find all <a> tags whose href matches the tour detail 
    URL pattern: /en/{destination}/{tour-slug}-{numeric-id}
    """
    tours = []
    seen_urls = set()  # Avoid duplicates
    
    # Pattern: URL ends with a numeric ID (e.g., -167234)
    tour_url_pattern = re.compile(
        rf"/en/[\w-]+/[\w-]+-(\d{{5,7}})$"
    )
    
    for link in soup.find_all("a", href=True):
        href = link["href"]
        
        # Make absolute URL if relative
        if href.startswith("/"):
            href = settings.scraper_base_url + href
        
        # Check if this looks like a tour detail page
        match = tour_url_pattern.search(href)
        if not match:
            continue
            
        # Skip duplicates
        if href in seen_urls:
            continue
        seen_urls.add(href)
        
        # Extract the tour ID from the URL
        tour_id = match.group(1)
        
        # Get the text content of the link (contains tour name, price, etc.)
        card_text = link.get_text(separator="\n", strip=True)
        
        # Parse what we can from the card text
        tour_info = parse_card_text(card_text, href, tour_id, destination)
        if tour_info:
            tours.append(tour_info)
    
    return tours


def parse_card_text(text: str, url: str, tour_id: str, destination: str) -> dict | None:
    """
    Parse the visible text of a tour card into structured data.
    
    The text typically looks like:
    "Sale now on\nVietnam Express Southbound\n10 days · Vietnam\nOriginal\n
     From Was\nUSD $1,490\nNow\nUSD $1,118\nSave up to USD $372**"
    """
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    
    if len(lines) < 3:
        return None  # Not enough content to be a tour card
    
    # Skip non-tour links (like "Explore tailor-made trips")
    if any(skip in text.lower() for skip in ["tailor-made", "build your dream"]):
        return None
    
    tour = {
        "tour_id": tour_id,
        "url": url,
        "destination": destination,
        "on_sale": False,
        "is_new": False,
    }
    
    # Walk through lines and extract what we can
    for i, line in enumerate(lines):
        # Detect sale/new badges
        if line.lower() == "sale now on":
            tour["on_sale"] = True
            continue
        if line.lower() == "new":
            tour["is_new"] = True
            continue
        
        # Duration line: "10 days · Vietnam" or "18 days · Cambodia, Vietnam +1"
        duration_match = re.match(r"(\d+)\s+days?\s*·\s*(.+)", line)
        if duration_match:
            tour["duration_days"] = int(duration_match.group(1))
            tour["countries"] = duration_match.group(2).strip()
            continue
        
        # Style line (one of the known styles)
        if line in ["Original", "Basix", "Comfort", "Premium"]:
            tour["style"] = line
            continue
        
        # Price lines
        price_match = re.search(r"USD\s*\$([0-9,]+)", line)
        if price_match:
            price = int(price_match.group(1).replace(",", ""))
            if "Was" in lines[max(0, i-1):i+1] or "Was" in line:
                tour["original_price_usd"] = price
            elif "Now" in lines[max(0, i-1):i+1] or "Now" in line:
                tour["sale_price_usd"] = price
            elif "price_usd" not in tour:
                tour["price_usd"] = price
            continue
        
        # If we haven't found the tour name yet, this is likely it
        # (first meaningful non-badge, non-price, non-duration line)
        if "tour_name" not in tour and len(line) > 3 and not line.startswith("Map of"):
            if not any(kw in line.lower() for kw in ["save up to", "lowest price", "from"]):
                tour["tour_name"] = line
    
    # Normalize pricing
    if "sale_price_usd" in tour:
        tour["price_usd"] = tour["sale_price_usd"]
    
    # Must have at least a name and URL to be valid
    if "tour_name" not in tour:
        return None
    
    return tour


def extract_highlights(lines: list[str]) -> list[str]:
    """Extract the 'Why you'll love this trip' bullet points."""
    highlights = []
    in_section = False
    
    for line in lines:
        if "why you" in line.lower() and "love" in line.lower():
            in_section = True
            continue
        if in_section:
            # Highlights are usually longer sentences
            if line.lower().startswith("itinerary") or line.lower().startswith("map of"):
                break
            if len(line) > 30:
                highlights.append(line)
    
    return highlights


def extract_itinerary(lines: list[str]) -> list[dict]:
    """
    Extract the day-by-day itinerary.

    Each day follows this pattern:
    "Day 4  • "
    [description paragraphs]
    "Accommodation" -> type
    "Meals" -> list or "There are no meals..."
    "Included activities" -> list
    "Optional activities" -> list with prices
    "Special information" -> text
    """

    days = []
    current_day = None
    current_section = None  # tracks which subsection we're in

    day_pattern = re.compile(r"Day\s+(\d+)\s*•\s*$")

    # Flag to know if the previous line was a Day header, meaning the NEXT line is the location
    expecting_location = False

    print("========== extract_itinerary============")

    for line in lines:
        # Check for a new day header
        day_match = day_pattern.match(line)
        if day_match:
            # Save previous day if exists
            if current_day:
                days.append(current_day)
            
            current_day = {
                "day": int(day_match.group(1)),
                "location": "",
                "description": "",
                "accommodation": "",
                "meals": [],
                "included_activities": [],
                "optional_activities": [],
                "special_info": ""
            }

            # Set the flag! The very next line processed will be saved as the location
            expecting_location = True
            current_section = "description"
            continue
        
        #Grab the location from the line immediately following the Day header
        if expecting_location:
            if current_day:
                current_day["location"] = line.strip()
            expecting_location = False # Reset flag so it doesn't overwrite it
            continue

        if not current_day:
            continue
            
        # Detect section headers
        line_lower = line.lower().strip()
        if line_lower == "accommodation":
            current_section = "accommodation"
            continue
        elif line_lower == "meals":
            current_section = "meals"
            continue
        elif line_lower == "included activities":
            current_section = "included_activities"
            continue
        elif line_lower == "optional activities":
            current_section = "optional_activities"
            continue
        elif line_lower == "special information":
            current_section = "special_info"
            continue
            
        # Check if we've hit the next major page section
        if line.lower().startswith("inclusions and activities"):
            if current_day:
                days.append(current_day)
            break
        if line.lower().startswith("explore trip in reverse"):
            if current_day:
                days.append(current_day)
            break
            
        # Append content to the current section
        if current_section == "description":
            if current_day["description"]:
                current_day["description"] += " " + line
            else:
                current_day["description"] = line
                
        elif current_section == "accommodation":
            if line and not line.startswith("("):
                current_day["accommodation"] = line
                
        elif current_section == "meals":
            if "no meals included" in line.lower():
                current_day["meals"] = []
            elif line in ["Breakfast", "Lunch", "Dinner"]:
                current_day["meals"].append(line)
                
        elif current_section == "included_activities":
            if line and len(line) > 3:
                current_day["included_activities"].append(line)
                
        elif current_section == "optional_activities":
            if line and len(line) > 3:
                current_day["optional_activities"].append(line)
                
        elif current_section == "special_info":
            if current_day["special_info"]:
                current_day["special_info"] += " " + line
            else:
                current_day["special_info"] = line

    # Don't forget the last day
    if current_day and current_day not in days:
        days.append(current_day)
    
    return days

def extract_after_label(lines: list[str], label: str) -> str:
    """Extract the content that appears after a summary label."""
    for i, line in enumerate(lines):
        if line.strip() == label and i + 1 < len(lines):
            return lines[i + 1]
    return ""

def main():
    # Load tour URLs from Phase 1
    listings_path = os.path.join(settings.raw_data_dir, "asia_tour_listings.json")
    if not os.path.exists(listings_path):
        print(f"ERROR: {listings_path} not found.")
        print("Run scrape_listings.py first (Phase 1).")
        return
    
    with open(listings_path, "r", encoding="utf-8") as f:
        listings = json.load(f)
    
    print(f"Loaded {len(listings)} tours from listings.")
    print(f"Estimated time: ~{len(listings) * settings.scraper_delay_seconds / 60:.0f} minutes\n")
    
    # Scrape each tour detail page
    detailed_tours = []
    failed = []
    
    for i, listing in enumerate(listings):
        url = listing["url"]
        name = listing.get("tour_name", "Unknown")
        print(f"[{i+1}/{len(listings)}] {name}")
        
        soup = fetch_page(url)
        if not soup:
            failed.append(url)
            time.sleep(settings.scraper_delay_seconds)
            continue
        
        detail = extract_tour_detail(soup, url)
        if detail:
            # Merge listing data (price, destination) with detail data
            merged = {**listing, **detail}
            detailed_tours.append(merged)
            print(f"{len(detail.get('itinerary', []))} days extracted")
        else:
            failed.append(url)
            print(f"Failed to parse")
        
        time.sleep(settings.scraper_delay_seconds)
    
    # Save results
    os.makedirs(os.path.join(settings.raw_data_dir), exist_ok=True)
    output_path = os.path.join(settings.raw_data_dir, "asia_tour_details.json")
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(detailed_tours, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*50}")
    print(f"Done! {len(detailed_tours)} tours saved to {output_path}")
    print(f"Failed: {len(failed)}")
    
    if failed:
        failed_path = os.path.join(settings.settings, "failed_urls.json")
        with open(failed_path, "w") as f:
            json.dump(failed, f, indent=2)
        print(f"Failed URLs saved to {failed_path}")


if __name__ == "__main__":
    main()