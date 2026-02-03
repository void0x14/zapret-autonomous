"""
BTK Blocked Sites Scraper
Fetches blocked domain lists from multiple sources
"""
import sqlite3
import logging
import dns.resolver
from typing import List, Set
from intelligence.sources import SOURCES, load_fallback_list
from core.db import StrategyDB

class BTKScraper:
    def __init__(self, db_path: str = "strategies.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Extend existing DB with blocked domains table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocked_domains (
                domain TEXT PRIMARY KEY,
                source TEXT,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                validated BOOLEAN DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()
    
    def fetch_all_sources(self) -> Set[str]:
        """Fetch domains from all sources and deduplicate."""
        all_domains = set()
        
        # Fetch from online sources
        for source in SOURCES:
            domains = source.fetch()
            for domain in domains:
                all_domains.add(domain.lower())
        
        # Add fallback list
        fallback = load_fallback_list()
        for domain in fallback:
            all_domains.add(domain.lower())
        
        logging.info(f"Total unique domains: {len(all_domains)}")
        return all_domains
    
    def validate_domain(self, domain: str) -> bool:
        """Check if domain actually exists via DNS."""
        try:
            dns.resolver.resolve(domain, 'A')
            return True
        except:
            return False
    
    def save_domains(self, domains: Set[str], validate: bool = False):
        """Save domains to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for domain in domains:
            is_valid = self.validate_domain(domain) if validate else False
            cursor.execute('''
                INSERT INTO blocked_domains (domain, source, validated)
                VALUES (?, 'aggregated', ?)
                ON CONFLICT(domain) DO UPDATE SET
                    last_seen = CURRENT_TIMESTAMP,
                    validated = excluded.validated
            ''', (domain, is_valid))
        
        conn.commit()
        conn.close()
        logging.info(f"Saved {len(domains)} domains to database")
    
    def get_all_blocked_domains(self) -> List[str]:
        """Retrieve all known blocked domains."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT domain FROM blocked_domains")
        domains = [row[0] for row in cursor.fetchall()]
        conn.close()
        return domains
    
    def run(self, validate: bool = False):
        """Main scraper workflow."""
        logging.info("Starting BTK scraper...")
        domains = self.fetch_all_sources()
        self.save_domains(domains, validate=validate)
        logging.info("✓ Scraper complete")

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - [BTK-SCRAPER] - %(message)s'
    )
    
    scraper = BTKScraper()
    scraper.run(validate=False)  # Set True for DNS validation
