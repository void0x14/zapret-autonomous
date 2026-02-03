"""
Telemetry Stats Tracker
Logs bypass attempts and generates statistics
"""
import sqlite3
import logging
from datetime import datetime
from typing import Optional

class StatsTracker:
    def __init__(self, db_path: str = "strategies.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Create telemetry tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bypass_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                domain TEXT NOT NULL,
                strategy TEXT,
                success BOOLEAN,
                latency_ms INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_summary (
                date DATE PRIMARY KEY,
                domains_bypassed INTEGER,
                total_requests INTEGER,
                avg_latency_ms REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_bypass(self, domain: str, strategy: str, success: bool, latency_ms: int):
        """Log a bypass attempt."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO bypass_log (domain, strategy, success, latency_ms)
            VALUES (?, ?, ?, ?)
        ''', (domain, strategy, success, latency_ms))
        
        conn.commit()
        conn.close()
        
        logging.debug(f"Logged: {domain} -> {strategy} ({'✓' if success else '✗'})")
    
    def update_daily_summary(self):
        """Aggregate today's stats into summary table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO daily_summary (date, domains_bypassed, total_requests, avg_latency_ms)
            SELECT 
                DATE(timestamp) as date,
                COUNT(DISTINCT domain) as domains_bypassed,
                COUNT(*) as total_requests,
                AVG(latency_ms) as avg_latency_ms
            FROM bypass_log
            WHERE DATE(timestamp) = DATE('now')
            GROUP BY DATE(timestamp)
        ''')
        
        conn.commit()
        conn.close()
    
    def get_stats(self, days: int = 7) -> dict:
        """Get statistics for the last N days."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Overall stats
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT domain) as unique_domains,
                COUNT(*) as total_attempts,
                SUM(CASE WHEN success THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate,
                AVG(latency_ms) as avg_latency
            FROM bypass_log
            WHERE timestamp >= datetime('now', ? || ' days')
        ''', (f'-{days}',))
        
        overall = cursor.fetchone()
        
        # Strategy breakdown
        cursor.execute('''
            SELECT strategy, COUNT(*) as count
            FROM bypass_log
            WHERE timestamp >= datetime('now', ? || ' days') AND success = 1
            GROUP BY strategy
            ORDER BY count DESC
        ''', (f'-{days}',))
        
        strategies = cursor.fetchall()
        
        # Recent bypasses
        cursor.execute('''
            SELECT domain, strategy, success, latency_ms, timestamp
            FROM bypass_log
            ORDER BY timestamp DESC
            LIMIT 10
        ''')
        
        recent = cursor.fetchall()
        
        conn.close()
        
        return {
            'unique_domains': overall[0] or 0,
            'total_attempts': overall[1] or 0,
            'success_rate': overall[2] or 0,
            'avg_latency': overall[3] or 0,
            'strategies': strategies,
            'recent': recent
        }
