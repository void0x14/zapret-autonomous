#!/usr/bin/env python3
"""
Zapret Stats - CLI Viewer
Professional text-based statistics dashboard
"""
import sys
import os
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telemetry.stats_tracker import StatsTracker

def format_header(title: str) -> str:
    """Format a header box."""
    width = 45
    padding = (width - len(title) - 2) // 2
    return f"""
╔{'═' * width}╗
║{' ' * padding}{title}{' ' * (width - padding - len(title))}║
╚{'═' * width}╝
"""

def format_stats(stats: dict, days: int) -> str:
    """Format statistics output."""
    output = format_header("ZAPRET AUTONOMOUS - STATISTICS")
    
    output += f"\n📅 Period: Last {days} day(s)\n"
    output += f"🌐 Unique Domains: {stats['unique_domains']}\n"
    output += f"📊 Total Attempts: {stats['total_attempts']}\n"
    output += f"✅ Success Rate: {stats['success_rate']:.1f}%\n"
    output += f"⚡ Avg Latency: {stats['avg_latency']:.1f}ms\n"
    
    # Strategy breakdown
    if stats['strategies']:
        output += f"\n{'─' * 45}\n"
        output += "📈 Top Strategies:\n"
        total_uses = sum(s[1] for s in stats['strategies'])
        for strategy, count in stats['strategies'][:5]:
            percentage = (count / total_uses * 100) if total_uses > 0 else 0
            bar = '█' * int(percentage / 5)
            output += f"  {strategy:15s}: {count:3d} uses ({percentage:4.1f}%) {bar}\n"
    
    # Recent activity
    if stats['recent']:
        output += f"\n{'─' * 45}\n"
        output += "🕒 Recent Bypasses:\n"
        for domain, strategy, success, latency, timestamp in stats['recent'][:5]:
            status = '✓' if success else '✗'
            output += f"  {domain:20s}: {strategy:10s} → {status} ({latency}ms)\n"
    
    return output

def main():
    parser = argparse.ArgumentParser(description='Zapret Autonomous Statistics')
    parser.add_argument('--range', default='7d', help='Time range (e.g., 7d, 30d)')
    parser.add_argument('--by-strategy', action='store_true', help='Show strategy breakdown')
    parser.add_argument('command', nargs='?', default='today', help='Command: today, week, month')
    
    args = parser.parse_args()
    
    # Parse time range
    if args.command == 'today':
        days = 1
    elif args.command == 'week':
        days = 7
    elif args.command == 'month':
        days = 30
    else:
        days = int(args.range.replace('d', ''))
    
    # Fetch stats
    tracker = StatsTracker()
    stats = tracker.get_stats(days=days)
    
    # Display
    print(format_stats(stats, days))

if __name__ == '__main__':
    main()
