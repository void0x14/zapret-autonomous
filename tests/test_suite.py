import unittest
import os
import sys
import sqlite3

# Add project root to PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock dns.resolver if not present
try:
    import dns.resolver
except ImportError:
    from unittest.mock import MagicMock
    mock_dns = MagicMock()
    sys.modules["dns"] = mock_dns
    sys.modules["dns.resolver"] = mock_dns

from installer.distro_detector import DistroDetector
from telemetry.stats_tracker import StatsTracker
from intelligence.blocklist_manager import BlocklistManager
from solver.parallel_prober import ParallelProber

class TestZapretAutonomous(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = "test_strategies.db"
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

    def test_distro_detection(self):
        distro = DistroDetector.detect()
        self.assertIsNotNone(distro, "Distro detection failed")

    def test_stats_tracker(self):
        tracker = StatsTracker(db_path=self.db_path)
        tracker.log_bypass("example.com", "fake", True, 100)
        stats = tracker.get_stats(days=1)
        self.assertEqual(stats['unique_domains'], 1)

    def test_blocklist_manager_init(self):
        manager = BlocklistManager(db_path=self.db_path, db_table="test_blocked")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_blocked'")
        self.assertIsNotNone(cursor.fetchone())
        conn.close()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

if __name__ == '__main__':
    unittest.main()
