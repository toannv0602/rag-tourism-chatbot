
# Collect all tour URLs and basic info from listing pages.


import requests
from bs4 import BeautifulSoup
import json
import time
import re
import os

# import instant
from app.config.settings import settings
from app.config.constants import ASIA_DESTINATIONS

# At the top of the file, after imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- CONFIG ---
BASE_URL = "https://www.intrepidtravel.com"

# All Asia destinations from the Intrepid website
ASIA_DESTINATIONS = ["vietnam"]

HEADER = {
    "User-Agent": settings.scraper_user_agent
}

DELAY_SECONDS = 3 # Deplay time

TIME_OUT = 3

def fetch_page(url: str) -> BeautifulSoup | None:
    try:
        response = requests.get(url, headers=HEADER, timeout= TIME_OUT)
        response.raise_for_status() # Raises exception for 4xx/5xx
        return BeautifulSoup(response.text, "lxml")
    except requests.RequestException as e:
        print(f"[ERROR] fetch_page function error fetch {url}: {e}")
        return None
    
def extract_tour_links(soup: BeautifulSoup, destination: str) -> list[dict]:
    """
    Extract tour URLs and basic info from a destination listing page.

    Strategy: Find all <a> tags whose href matches the tour detail 
    URL pattern: /en/{destination}/{tour-slug}-{numeric-id}
    """

    tours = []
    seen_urls = set() # Avoid duplicates

    # Pattern: URL ends with a numeric ID (e.g., -167234)
    tour_url_pattern = re.compile(
        rf"/en/[\w-]+/[\w-]+-(\d{{5,7}})$"
    )

    for link in soup.find_all("a", href=True):
        href = link["href"]
        print("Href=", href)
        #make absolute URL if relative

        if href.startswith("/"):
            href = BASE_URL + href

        # Check if this looks like a tour detail page
        match = tour_url_pattern.search(href)
        if not match:
            continue

        # Skip duplicates
        if href in seen_urls:
            continue
        seen_urls.add(href)
        
        # Extract the tour id  from the URL
        tour_id = match.group(1)

        # Get the text content of the link (contains tour name, price, etc.)
        card_text = link.get_text(separator="\n", strip=True)

        # Parse what we can from the card text
        tour_info =parse_card_text(card_text, href, tour_id, destination)
        if tour_info:
            tours.append(tour_info)
        
    return tours

"""
Parse the visible text of a tour card into structured data.
The text typically looks like:
    "Sale now on\nVietnam Express Southbound\n10 days..."
"""

def parse_card_text(text: str, url: str, tour_id: str, destination: str) -> dict | None:
    # split each line by \m
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if len(lines) < 3:
        return None  # Not enough content to be a tour card
    
    # skip non-tour links (Explore tailor-made trips)
    if any(skip_word in text.lower() for skip_word in ["tailor-made", "build your dream"]):
        return None
    
    tour = {
        "tour_id": tour_id,
        "url": url,
        "destination": destination,
        "on_sale": False,
        "is_new": False,
    }

    # walk through lines and extract
    for i, line in enumerate(lines):
        ### Detect sale/new badges
        if line.lower() == "sale now on":
            tour["on_sale"] = True
            continue
        if line.lower() == "new":
            tour["is_new"] = True
            continue

        ### Duration line: "10 days Vietnam" or "18 days Cambodia, Vietnam +1"
        # define pattern
        duration_match = re.match(r"(\d+)\s+days?\s*·\s*(.+)", line)
        if duration_match:
            tour["duration_days"] = int(duration_match.group(1))
            tour["countries"] = duration_match.group(2).strip()
            continue

        # Style line (one of the know styles)
        if line in ["Original", "Basix", "Comfort", "Premium"]:
            tour["style"] = line
            continue

        ### Price lines
        price_match = re.search(r"^\$([0-9,]+)$", line)
        if price_match:
            print("price: ", price_match)
            price = int(price_match.group(1).replace(",",""))
            if "Was" in lines[max(0, i-2):i+1] or "Was" in line:
                print("original_price_usd", price)
                tour["original_price_usd"] = price
            elif "Now" in lines[max(0, i-2):i+1] or "Now" in line:
                tour["sale_price_usd"] = price
            elif "price_usd" not in tour:
                tour["price_usd"] = price
            continue

        # Tour name
        # put it in the final step, because it is not belong any case above
        # this is likely it (first meaningful non-badge, non-price, non-duration line)
        if "tour_name" not in tour and len(line) > 3 and not line.startswith("Map of"):
            if not any(kw in line.lower() for kw in ["save up to","lowest price", "from" ]):
                tour["tour_name"] = line
    
    # Normalize pricing
    if "sale_price_usd" in tour:
        print("Normalize pricin from sale price")
        tour["price_usd"] = tour["sale_price_usd"]

    # must contain tour name
    if "tour_name" not in tour:
        return None
    
    return tour

def scrape_all_asia_listings() -> list[dict]:
    """
        Scrape tour listings for all Asia destinations.
    """

    all_tours = []
    for i, dest in enumerate(ASIA_DESTINATIONS):
        url = f"{settings.scraper_base_url}/en/{dest}"
        print(f"[LOGGING] [Scrape data] [{i+1}/{len(ASIA_DESTINATIONS)}] Scraping {dest}...")
        
        soup = fetch_page(url=url)
        if not soup:
            continue

        tours = extract_tour_links(soup, dest)

        # Deduplicate against what we already have (tours appear on multiple pages)
        new_tours = []
        existing_ids = {t["tour_id"] for t in all_tours}
        for tour in tours:
            if tour["tour_id"] not in existing_ids:
                    new_tours.append(tour)
                    existing_ids.add(tour["tour_id"])
        
        all_tours.extend(new_tours)
        print(f"  Found {len(tours)} tours ({len(new_tours)} new)")
        
        time.sleep(DELAY_SECONDS)  # Be polite
    
    return all_tours

if __name__ == "__main__":
    print("=" * 50)
    print("Intrepid Travel — Asia Tour Listings Scraper")
    print("=" * 50)
    
    # # Create output directory
    # os.makedirs(os.path.join(PROJECT_ROOT, "data", "raw"), exist_ok=True)

    
    tours = scrape_all_asia_listings()
    
    # # # Save results
    output_path = settings.raw_data_dir / "asia_tour_listings.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(tours, f, indent=2, ensure_ascii=False)
    
    print(f"\nDone! Saved {len(tours)} unique tours to {output_path}")
    
    # Print summary
    destinations = set(t["destination"] for t in tours)
    print(f"Destinations covered: {len(destinations)}")
    for dest in sorted(destinations):
        count = sum(1 for t in tours if t["destination"] == dest)
        print(f"  {dest}: {count} tours")