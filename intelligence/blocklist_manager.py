"""
Global Blocklist Intelligence
Fetches blocked domain lists from global and regional sources.
"""
import sqlite3
import logging
import dns.resolver
import argparse
from typing import List, Set
from intelligence.sources import SOURCES, load_fallback_list

class BlocklistManager:
    def __init__(self, db_path: str = "strategies.db", db_table: str = "blocked_domains"):
        self.db_path = db_path
        self.db_table = db_table
        self._init_db()
    
    def _init_db(self):
        """Extend existing DB with blocked domains table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.db_table} (
                domain TEXT PRIMARY KEY,
                source TEXT,
                region TEXT,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                validated BOOLEAN DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()
    
    def fetch_domains(self, target_region: str = "global") -> Set[str]:
        """
        Fetch domains based on region.
        target_region='global' -> Fetches GLOBAL list only.
        target_region='all' -> Fetches EVERYTHING (Global + TR + RU + IR...).
        target_region='tr' -> Fetches GLOBAL + TR.
        """
        all_domains = set()
        
        logging.info(f"Targeting Region: {target_region.upper()}")
        
        for source in SOURCES:
            # Logic: 
            # If target is 'all', take everything.
            # If target is 'global', take only global.
            # If target is 'tr', take global + tr.
            
            should_fetch = False
            
            if target_region == "all":
                should_fetch = True
            elif target_region == "global" and source.region == "global":
                should_fetch = True
            elif source.region == target_region or source.region == "global":
                should_fetch = True
            
            if should_fetch:
                domains = source.fetch()
                for domain in domains:
                    all_domains.add(domain.lower())
        
        # Always add fallback list
        fallback = load_fallback_list()
        for domain in fallback:
            all_domains.add(domain.lower())
        
        logging.info(f"Total unique domains found: {len(all_domains)}")
        return all_domains
    
    def validate_domain(self, domain: str) -> bool:
        """Check if domain actually exists via DNS."""
        try:
            dns.resolver.resolve(domain, 'A')
            return True
        except:
            return False
    
    def save_domains(self, domains: Set[str], region: str, validate: bool = False):
        """Save domains to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for domain in domains:
            is_valid = self.validate_domain(domain) if validate else False
            cursor.execute(f'''
                INSERT INTO {self.db_table} (domain, source, region, validated)
                VALUES (?, 'scraper', ?, ?)
                ON CONFLICT(domain) DO UPDATE SET
                    last_seen = CURRENT_TIMESTAMP,
                    validated = excluded.validated
            ''', (domain, region, is_valid))
        
        conn.commit()
        conn.close()
        logging.info(f"Saved {len(domains)} domains to database")
    
    def run(self, region: str = "global", validate: bool = False):
        """Main scraper workflow."""
        logging.info("Starting Global Intelligence Scraper...")
        domains = self.fetch_domains(region)
        self.save_domains(domains, region, validate=validate)
        logging.info("✓ Scraper complete")

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - [INTEL] - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description='Zapret Global Intelligence')
    parser.add_argument('--region', default='global', help='Region to fetch (global, tr, ru, ir, all)')
    parser.add_argument('--validate', action='store_true', help='Validate domains via DNS')
    
    args = parser.parse_args()
    
    manager = BlocklistManager()
    manager.run(region=args.region, validate=args.validate)
