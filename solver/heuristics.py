# Heuristics for Turkey ISPs (BTK/Turk Telekom/Turkcell)
# Based on official zapret documentation from bol-van/zapret
# https://github.com/bol-van/zapret

# nfqws desync modes work in phases:
# Phase 0: syndata, --wssize (connection establishment)
# Phase 1: fake, rst, rstack (fakes sent before original)
# Phase 2: fakedsplit, multisplit, ipfrag2, etc (original sent modified)
# Modes can be combined: phase0,phase1,phase2

STRATEGIES = {
    # === TESTED WORKING FOR TURKEY ===
    "fake_ttl": {
        "cmd": "--dpi-desync=fake --dpi-desync-ttl=1 --dpi-desync-fooling=md5sig",
        "desc": "Fake with TTL=1 + MD5 signature fooling. Works for most BTK blocks."
    },
    "fake_badsum": {
        "cmd": "--dpi-desync=fake --dpi-desync-fooling=badsum",
        "desc": "Fake with bad checksum. Classic method, very compatible."
    },
    "fakedsplit": {
        "cmd": "--dpi-desync=fake,fakedsplit --dpi-desync-ttl=1 --dpi-desync-split-pos=1",
        "desc": "Fake + split at position 1. Good for TLS SNI hiding."
    },
    "multisplit": {
        "cmd": "--dpi-desync=fake,multisplit --dpi-desync-ttl=1 --dpi-desync-split-pos=1,midsld",
        "desc": "Fake + multi-split. Breaks SNI across multiple packets."
    },
    
    # === DISORDER METHODS ===
    "disorder2": {
        "cmd": "--dpi-desync=fake,disorder2 --dpi-desync-ttl=1 --dpi-desync-split-pos=1",
        "desc": "Disorder - sends packets out of order. Confuses stateful DPI."
    },
    
    # === ADVANCED METHODS ===
    "syndata": {
        "cmd": "--dpi-desync=syndata",
        "desc": "Send data in SYN packet. Experimental."
    },
    "fakeknown": {
        "cmd": "--dpi-desync=fakeknown --dpi-desync-ttl=5",
        "desc": "Fake with known protocol signatures."
    },
    
    # === UDP/QUIC ===
    "fake_udp": {
        "cmd": "--dpi-desync=fake --dpi-desync-any-protocol --dpi-desync-ttl=1",
        "desc": "Fake for UDP protocols (QUIC, etc)."
    },
    
    # === COMBO FOR TURKEY ===
    "turkey_combo": {
        "cmd": "--dpi-desync=fake,multisplit --dpi-desync-ttl=3 --dpi-desync-split-pos=1,midsld --dpi-desync-fooling=md5sig",
        "desc": "Optimized combo for Turkish ISPs (Turk Telekom/BTK)."
    }
}

# Priority order for Turkey - based on community feedback
PRIORITY_LIST = [
    "fake_ttl",       # Most reliable for Turkey
    "fake_badsum",    # Classic, very compatible
    "fakedsplit",     # Good for TLS
    "turkey_combo",   # Turkey-specific combo
    "multisplit",     # More aggressive split
    "disorder2",      # Out-of-order packets
    "fakeknown",      # Protocol-aware
    "syndata",        # Experimental
    "fake_udp",       # For QUIC
]
