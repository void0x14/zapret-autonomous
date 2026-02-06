import sqlite3
import threading
import logging
from typing import Optional, Dict

class StrategyDB:
    def __init__(self, db_path: str = "strategies.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS domains (
                    domain TEXT PRIMARY KEY,
                    strategy TEXT NOT NULL,
                    isp TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    success_count INTEGER DEFAULT 1
                )
            ''')
            conn.commit()
            conn.close()

    def get_strategy(self, domain: str) -> Optional[str]:
        """Retrieve the known working strategy for a domain."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT strategy FROM domains WHERE domain = ?", (domain,))
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else None

    def save_strategy(self, domain: str, strategy: str, isp: str = "Unknown"):
        """Save a working strategy for a domain."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO domains (domain, strategy, isp, success_count)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(domain) DO UPDATE SET
                    strategy=excluded.strategy,
                    last_updated=CURRENT_TIMESTAMP,
                    success_count=success_count + 1
            ''', (domain, strategy, isp))
            conn.commit()
            conn.close()
            logging.info(f"Saved strategy for {domain}: {strategy}")

    def delete_strategy(self, domain: str):
        """Delete a saved strategy for a domain."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM domains WHERE domain = ?", (domain,))
            conn.commit()
            conn.close()
