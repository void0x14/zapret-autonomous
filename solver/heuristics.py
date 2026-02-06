"""
Zapret Strategies - TURKNET & NEXTDNS OPTIMIZED
Focus: Lightweight Split, SNI Fragmentation, IPv6/IPv4 Hybrid
"""

PRIORITY_LIST = [
    "turknet_split",       # Simple split (Best for TurkNet)
    "turknet_disorder",    # Out of order
    "desync_wssize",       # Window scaling
    "global_fake",         # Fallback
]

STRATEGIES = {
    # 1. TURKNET SPLIT (No Fake, Just Split)
    # TurkNet usually doesn't need fake packets, just split SNI.
    "turknet_split": {
        "cmd": "--dpi-desync=split --dpi-desync-split-pos=sniext+1 --dpi-desync-fooling=md5sig",
        "description": "Clean SNI split without fake packets (TurkNet optimized)"
    },

    # 2. TURKNET DISORDER
    # Reorders packets. TurkNet DPI allows this but gets confused.
    "turknet_disorder": {
        "cmd": "--dpi-desync=disorder2 --dpi-desync-split-pos=1 --dpi-desync-fooling=md5sig",
        "description": "Packet reordering for TurkNet"
    },
    
    # 3. WSSIZE (Universal)
    "desync_wssize": {
        "cmd": "--wssize=1:6 --dpi-desync=split --dpi-desync-split-pos=1",
        "description": "Window scaling 1:6"
    },
    
    # 4. GLOBAL FAKE (Fallback)
    "global_fake": {
        "cmd": "--dpi-desync=fake,split2 --dpi-desync-ttl=2 --dpi-desync-fooling=md5sig",
        "description": "Aggressive fake packet"
    }
}
