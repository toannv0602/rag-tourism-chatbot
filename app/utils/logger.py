"""
Logging configuration for the application.
"""
import logging
import sys
from app.config.settings import settings

def setup_logging():
    settings.log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),  # Print to terminal
            logging.FileHandler(settings.log_dir / "app.log"),  # Also save to file
        ]
    )