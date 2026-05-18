"""
app/config/constants.py
Business logic constants and enums. These never change between environments.
"""
from enum import Enum


class TourStyle(str, Enum):
    """Intrepid Travel tour styles."""
    BASIX = "Basix"
    ORIGINAL = "Original"
    COMFORT = "Comfort"
    PREMIUM = "Premium"


class TourTheme(str, Enum):
    """Intrepid Travel tour themes."""
    EXPLORER = "Explorer"
    ACTIVE = "Active"
    SAILING = "Sailing"
    POLAR = "Polar"
    FAMILY = "Family"
    FOOD = "Food"
    CYCLING = "Cycling"
    WALKING = "Walking & Hiking"
    FESTIVALS = "Festivals & Events"
    WILDLIFE = "Wildlife"


class ChunkType(str, Enum):
    """RAG chunk categories for metadata filtering."""
    TOUR_OVERVIEW = "tour_overview"
    ITINERARY_DAY = "itinerary_day"
    PRACTICAL_INFO = "practical_info"
    FAQ = "faq"


class Meal(str, Enum):
    BREAKFAST = "Breakfast"
    LUNCH = "Lunch"
    DINNER = "Dinner"


# Scraper constants
ASIA_DESTINATIONS = [
    "armenia", "azerbaijan", "bali", "bhutan", "borneo", "cambodia",
    "china", "georgia", "hong-kong", "india", "indonesia", "japan",
    "kazakhstan", "kyrgyzstan", "laos", "malaysia", "maldives",
    "mongolia", "nepal", "pakistan", "philippines", "singapore",
    "south-korea", "sri-lanka", "taiwan", "tajikistan", "thailand",
    "tibet", "timor-leste", "turkmenistan", "uzbekistan", "vietnam",
]

# Default RAG parameters
DEFAULT_TOP_K = 3
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50