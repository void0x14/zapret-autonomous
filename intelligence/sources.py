"""
Data Source Definitions for Global Blocked Sites
Supports multiple intelligence sources (Global & Regional)
"""
from typing import List
import requests
import logging
import csv
import io

class DataSource:
    def __init__(self, name: str, url: str, parser_func, region: str = "global"):
        self.name = name
        self.url = url
        self.parser = parser_func
        self.region = region  # 'global', 'tr', 'ru', 'ir', etc.
    
    def fetch(self) -> List[str]:
        """Fetch and parse domains from this source."""
        try:
            logging.info(f"Fetching {self.region.upper()} list from {self.name}...")
            response = requests.get(self.url, timeout=15)
            response.raise_for_status()
            domains = self.parser(response.text)
            logging.info(f"✓ {self.name}: Found {len(domains)} domains")
            return domains
        except Exception as e:
            logging.error(f"Failed to fetch {self.name}: {e}")
            return []

def parse_simple_list(content: str) -> List[str]:
    """Parse simple domain lists (one per line, # for comments)."""
    domains = []
    for line in content.split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            # Extract domain (handle various formats)
            domain = line.split('://')[-1].split('/')[0]
            domains.append(domain)
    return domains

def parse_citizenlab_csv(content: str) -> List[str]:
    """Parse Citizen Lab CSV format (url, category_code, ...)."""
    domains = []
    try:
        f = io.StringIO(content)
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get('url', '')
            if url:
                domain = url.split('://')[-1].split('/')[0]
                domains.append(domain)
    except Exception as e:
        logging.error(f"CSV Parse error: {e}")
    return domains

# Global Data Sources Registry
SOURCES = [
    # --- GLOBAL LISTS ---
    DataSource(
        name="Citizen Lab Global",
        url="https://raw.githubusercontent.com/citizenlab/test-lists/master/lists/global.csv",
        parser_func=parse_citizenlab_csv,
        region="global"
    ),
    
    # --- TURKEY (TR) ---
    DataSource(
        name="Turkey Blocks (Community)",
        url="https://raw.githubusercontent.com/turkeyblocks/tracking/master/domains.txt",
        parser_func=parse_simple_list,
        region="tr"
    ),
    DataSource(
        name="Engelli Web (TR)",
        url="https://raw.githubusercontent.com/engelsiz/blocked-sites/main/list.txt",
        parser_func=parse_simple_list,
        region="tr"
    ),
    
    # --- RUSSIA (RU) ---
    DataSource(
        name="Antizapret (Rublacklist)",
        url="https://raw.githubusercontent.com/zapret-info/z-i/master/dump.csv",
        parser_func=lambda c: [line.split(';')[1] for line in c.split('\n') if ';' in line], # Simplified parser for massive RU list
        region="ru"
    ),
    
    # --- IRAN (IR) ---
    DataSource(
        name="Iran Blocklist (Community)",
        url="https://raw.githubusercontent.com/bootmortis/iran-hosted-domains/main/domains.txt", 
        # Note: Need a better source for "Blocked in Iran", this is usually "Hosted in Iran". 
        # Using a placeholder for architecture demonstration.
        parser_func=parse_simple_list,
        region="ir"
    )
]

def load_fallback_list() -> List[str]:
    """Load manual fallback list."""
    try:
        with open('intelligence/fallback_domains.txt', 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        return []
