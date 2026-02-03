"""
Data Source Definitions for Turkey Blocked Sites
Supports multiple intelligence sources
"""
from typing import List, Dict
import requests
import logging

class DataSource:
    def __init__(self, name: str, url: str, parser_func):
        self.name = name
        self.url = url
        self.parser = parser_func
    
    def fetch(self) -> List[str]:
        """Fetch and parse domains from this source."""
        try:
            logging.info(f"Fetching from {self.name}...")
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
            domains = self.parser(response.text)
            logging.info(f"✓ {self.name}: Found {len(domains)} domains")
            return domains
        except Exception as e:
            logging.error(f"Failed to fetch {self.name}: {e}")
            return []

def parse_github_list(content: str) -> List[str]:
    """Parse GitHub-style domain lists (one per line, # for comments)."""
    domains = []
    for line in content.split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            # Extract domain (handle various formats)
            if '://' in line:
                domain = line.split('://')[1].split('/')[0]
            else:
                domain = line.split()[0]
            domains.append(domain)
    return domains

def parse_usom_json(content: str) -> List[str]:
    """Parse USOM JSON format (if they provide one)."""
    import json
    try:
        data = json.loads(content)
        # Adjust based on actual USOM API structure
        return data.get('blocked_domains', [])
    except:
        return []

# Data Sources Registry
SOURCES = [
    DataSource(
        name="Community List (turkeyblocks)",
        url="https://raw.githubusercontent.com/turkeyblocks/tracking/master/domains.txt",
        parser_func=parse_github_list
    ),
    DataSource(
        name="Engelli Web",
        url="https://raw.githubusercontent.com/engelsiz/blocked-sites/main/list.txt",
        parser_func=parse_github_list
    ),
    # Add USOM when/if they provide public API
    # DataSource(
    #     name="USOM Official",
    #     url="https://usom.gov.tr/api/blocked",
    #     parser_func=parse_usom_json
    # ),
]

def load_fallback_list() -> List[str]:
    """Load manual fallback list."""
    try:
        with open('intelligence/fallback_domains.txt', 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        return []
