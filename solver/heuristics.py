"""
Zapret Strategies & Heuristics - GLOBAL & TURKEY OPTIMIZED
Derived from bol-van/zapret blockcheck.sh and GitHub Issues (2024-2025)
Focus: Superonline, TurkNet, TurkTelekom, and Cloudflare-backed sites.
"""

# Priority order designed for speed and reliability
PRIORITY_LIST = [
    "tr_split_sni",        # Best for Superonline (Split SNI)
    "tr_wssize_fake",      # Forces server fragmentation (Very effective)
    "tr_fake_ttl_low",     # Classic TTL spoofing (TTL=3)
    "tr_disorder",         # Packet reordering
    "global_default",      # Standard Zapret default
    "legacy_badsum",       # For older DPI boxes
    "quic_fake",           # UDP/QUIC specific
]

STRATEGIES = {
    # 1. TR SPLIT SNI (Superonline & TT)
    # Splits SNI at extension start + 1 byte. Fooling with MD5.
    "tr_split_sni": {
        "cmd": "--dpi-desync=split --dpi-desync-split-pos=sniext+1 --dpi-desync-fooling=md5sig",
        "description": "Splits SNI header (Superonline optimized)"
    },

    # 2. WSSIZE + FAKE (Modern HTTPS)
    # Reduces Window Size to 1:6, forcing server to send small packets.
    # Also sends fake packet to confuse stateful DPI.
    "tr_wssize_fake": {
        "cmd": "--wssize=1:6 --dpi-desync=fake --dpi-desync-ttl=4",
        "description": "Window scaling 1:6 + Fake packet"
    },

    # 3. FAKE TTL LOW (Aggressive)
    # Sends fake packet with very low TTL (3).
    # If standard TTL=1 fails, try 3 or 4 for TR ISPs.
    "tr_fake_ttl_low": {
        "cmd": "--dpi-desync=fake,split2 --dpi-desync-ttl=3 --dpi-desync-fooling=md5sig",
        "description": "Fake packet with TTL=3 (TR optimized)"
    },

    # 4. DISORDER (Packet Reordering)
    # Sends packets out of order.
    "tr_disorder": {
        "cmd": "--dpi-desync=disorder2 --dpi-desync-split-pos=1 --dpi-desync-fooling=md5sig",
        "description": "Disorder strategy (reverse packet order)"
    },

    # 5. GLOBAL DEFAULT (General Purpose)
    # Standard fake split strategy.
    "global_default": {
        "cmd": "--dpi-desync=fake,split2 --dpi-desync-ttl=1 --dpi-desync-fooling=md5sig",
        "description": "Standard global strategy"
    },
    
    # 6. LEGACY BADSUM (Old DPIs)
    "legacy_badsum": {
        "cmd": "--dpi-desync=fake --dpi-desync-fooling=badsum",
        "description": "Bad checksum fooling"
    },

    # 7. QUIC/UDP Strategy
    # Using repeats to flood DPI state for UDP.
    "quic_fake": {
        "cmd": "--dpi-desync=fake --dpi-desync-repeats=6",
        "description": "QUIC/UDP fake flooding"
    }
}
