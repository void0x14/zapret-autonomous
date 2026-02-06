"""
Zapret Strategies & Heuristics for Turkey
Officially tuned for: Turk Telekom, Superonline, TurkNet
Based on github.com/bol-van/zapret documentation
"""

# Priority list for auto-mode
PRIORITY_LIST = [
    "desync_split",          # Most reliable (split SNI)
    "desync_fake_ttl",       # Classic fake
    "desync_disorder",       # Packet reordering
    "desync_wssize",         # Window size scaling (ServerHello fragmentation)
    "desync_badsum",         # Bad checksum (older DPIs)
]

STRATEGIES = {
    # 1. SPLIT (reliable)
    "desync_split": {
        "cmd": "--dpi-desync=split --dpi-desync-split-pos=1,midsld --dpi-desync-fooling=md5sig",
        "description": "Splits SNI at predictable positions"
    },
    
    # 2. FAKE TTL (classic)
    "desync_fake_ttl": {
        "cmd": "--dpi-desync=fake,split2 --dpi-desync-ttl=2 --dpi-desync-fooling=md5sig",
        "description": "Sends fake packet with low TTL"
    },
    
    # 3. DISORDER (reordering)
    "desync_disorder": {
        "cmd": "--dpi-desync=disorder2 --dpi-desync-split-pos=1 --dpi-desync-fooling=md5sig",
        "description": "Sends packets out of order"
    },
    
    # 4. WSSIZE (TCP Window Scaling) - Forces server to fragment
    "desync_wssize": {
        "cmd": "--wssize=1:6 --dpi-desync=fake",
        "description": "Forces server to split response using Window Size scaling"
    },
    
    # 5. BADSUM (legacy)
    "desync_badsum": {
        "cmd": "--dpi-desync=fake --dpi-desync-fooling=badsum",
        "description": "Sends packets with bad checksum"
    }
}
