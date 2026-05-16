# this code scrape data from url
import requests
from bs4 import BeautifulSoup
import time

# fetch the page
url = "https://www.intrepidtravel.com/en/vietnam"

headers = {
    "User-Agent": "RAGTravelBot/1.0"
}

response = requests.get(url, headers=headers)
print(f"Status: {response.status_code}")    # 200 = success
print(f"Content length: {len(response.text)} characters")
# print(response.text)

# # parse with BeautifulSoup
soup = BeautifulSoup(response.text, "lxml")
# print(soup)

# Step 3: Find all links that look like tour detail pages
# Tour URLs follow pattern: /en/[country]/[tour-slug]-[id]
all_links = soup.find_all("a", href=True)
print("All Link:", len(all_links))
tour_links = []

for link in all_links:
    href = link["href"]
    print("href:", href)
    if "/en/" in href and href.count("/") >= 3 and href != url:
        # Likely a tour detail link
        if any(dest in href for dest in ["/vietnam/", "/cambodia/", "/thailand/"]):
            if href not in tour_links:
                tour_links.append(href)

print(f"\nFound {len(tour_links)} potential tour links:")
for link in tour_links[:25]:
    print(f"{link}")