"""
Zapret Strategies - FULL BLOCKCHECK.SH EXTRACTION
All strategies from bol-van/zapret blockcheck.sh
Test ALL combinations, use the winner.
"""

# All strategies will be tested - first match wins
PRIORITY_LIST = [
    # WSSIZE combinations
    "wssize_fake",
    "wssize_split",
    "wssize_disorder",
    
    # FAKE variations
    "fake_ttl1",
    "fake_ttl2", 
    "fake_ttl3",
    "fake_ttl4",
    "fake_ttl5",
    "fake_autottl",
    "fake_badsum",
    "fake_badseq",
    "fake_md5sig",
    "fake_datanoack",
    
    # SPLIT variations
    "split_1",
    "split_2",
    "split_sniext1",
    "split_sniext4",
    "split_host1",
    "split_midsld",
    "split_multi",
    
    # DISORDER variations
    "disorder_1",
    "disorder_midsld",
    
    # FAKEDSPLIT combinations
    "fakedsplit_ttl1",
    "fakedsplit_ttl2",
    "fakedsplit_ttl3",
    
    # MULTISPLIT/MULTIDISORDER
    "multisplit_sni",
    "multidisorder_sni",
    
    # HOSTFAKESPLIT
    "hostfakesplit",
    
    # SYNDATA
    "syndata",
    
    # Legacy fallbacks
    "disorder2_badsum",
    "fake_split2_md5",
]

STRATEGIES = {
    # ========== WSSIZE COMBINATIONS ==========
    "wssize_fake": {
        "cmd": "--wssize=1:6 --dpi-desync=fake --dpi-desync-ttl=4",
        "description": "Window scaling 1:6 + fake"
    },
    "wssize_split": {
        "cmd": "--wssize=1:6 --dpi-desync=split --dpi-desync-split-pos=sniext+1",
        "description": "Window scaling 1:6 + split"
    },
    "wssize_disorder": {
        "cmd": "--wssize=1:6 --dpi-desync=disorder2 --dpi-desync-split-pos=1",
        "description": "Window scaling 1:6 + disorder"
    },
    
    # ========== FAKE TTL VARIATIONS ==========
    "fake_ttl1": {
        "cmd": "--dpi-desync=fake --dpi-desync-ttl=1 --dpi-desync-fooling=md5sig",
        "description": "Fake TTL=1"
    },
    "fake_ttl2": {
        "cmd": "--dpi-desync=fake --dpi-desync-ttl=2 --dpi-desync-fooling=md5sig",
        "description": "Fake TTL=2"
    },
    "fake_ttl3": {
        "cmd": "--dpi-desync=fake --dpi-desync-ttl=3 --dpi-desync-fooling=md5sig",
        "description": "Fake TTL=3"
    },
    "fake_ttl4": {
        "cmd": "--dpi-desync=fake --dpi-desync-ttl=4 --dpi-desync-fooling=md5sig",
        "description": "Fake TTL=4"
    },
    "fake_ttl5": {
        "cmd": "--dpi-desync=fake --dpi-desync-ttl=5 --dpi-desync-fooling=md5sig",
        "description": "Fake TTL=5"
    },
    "fake_autottl": {
        "cmd": "--dpi-desync=fake --dpi-desync-autottl --dpi-desync-fooling=md5sig",
        "description": "Fake with auto TTL detection"
    },
    "fake_badsum": {
        "cmd": "--dpi-desync=fake --dpi-desync-fooling=badsum",
        "description": "Fake with bad checksum"
    },
    "fake_badseq": {
        "cmd": "--dpi-desync=fake --dpi-desync-fooling=badseq",
        "description": "Fake with bad sequence"
    },
    "fake_md5sig": {
        "cmd": "--dpi-desync=fake --dpi-desync-fooling=md5sig",
        "description": "Fake with MD5 signature"
    },
    "fake_datanoack": {
        "cmd": "--dpi-desync=fake --dpi-desync-fooling=datanoack",
        "description": "Fake with data no ACK"
    },
    
    # ========== SPLIT VARIATIONS ==========
    "split_1": {
        "cmd": "--dpi-desync=split --dpi-desync-split-pos=1 --dpi-desync-fooling=md5sig",
        "description": "Split at position 1"
    },
    "split_2": {
        "cmd": "--dpi-desync=split --dpi-desync-split-pos=2 --dpi-desync-fooling=md5sig",
        "description": "Split at position 2"
    },
    "split_sniext1": {
        "cmd": "--dpi-desync=split --dpi-desync-split-pos=sniext+1 --dpi-desync-fooling=md5sig",
        "description": "Split at SNI extension +1"
    },
    "split_sniext4": {
        "cmd": "--dpi-desync=split --dpi-desync-split-pos=sniext+4 --dpi-desync-fooling=md5sig",
        "description": "Split at SNI extension +4"
    },
    "split_host1": {
        "cmd": "--dpi-desync=split --dpi-desync-split-pos=host+1 --dpi-desync-fooling=md5sig",
        "description": "Split at host +1"
    },
    "split_midsld": {
        "cmd": "--dpi-desync=split --dpi-desync-split-pos=midsld --dpi-desync-fooling=md5sig",
        "description": "Split at middle of SLD"
    },
    "split_multi": {
        "cmd": "--dpi-desync=split --dpi-desync-split-pos=1,midsld --dpi-desync-fooling=md5sig",
        "description": "Split at multiple positions"
    },
    
    # ========== DISORDER VARIATIONS ==========
    "disorder_1": {
        "cmd": "--dpi-desync=disorder2 --dpi-desync-split-pos=1 --dpi-desync-fooling=md5sig",
        "description": "Disorder at position 1"
    },
    "disorder_midsld": {
        "cmd": "--dpi-desync=disorder2 --dpi-desync-split-pos=midsld --dpi-desync-fooling=md5sig",
        "description": "Disorder at midsld"
    },
    
    # ========== FAKEDSPLIT COMBINATIONS ==========
    "fakedsplit_ttl1": {
        "cmd": "--dpi-desync=fake,split2 --dpi-desync-ttl=1 --dpi-desync-fooling=md5sig",
        "description": "Fake+Split TTL=1"
    },
    "fakedsplit_ttl2": {
        "cmd": "--dpi-desync=fake,split2 --dpi-desync-ttl=2 --dpi-desync-fooling=md5sig",
        "description": "Fake+Split TTL=2"
    },
    "fakedsplit_ttl3": {
        "cmd": "--dpi-desync=fake,split2 --dpi-desync-ttl=3 --dpi-desync-fooling=md5sig",
        "description": "Fake+Split TTL=3"
    },
    
    # ========== MULTISPLIT/MULTIDISORDER ==========
    "multisplit_sni": {
        "cmd": "--dpi-desync=multisplit --dpi-desync-split-pos=1,sniext+1,host+1,midsld --dpi-desync-fooling=md5sig",
        "description": "Multi-split at SNI positions"
    },
    "multidisorder_sni": {
        "cmd": "--dpi-desync=multidisorder --dpi-desync-split-pos=1,midsld --dpi-desync-fooling=md5sig",
        "description": "Multi-disorder at SNI"
    },
    
    # ========== HOSTFAKESPLIT ==========
    "hostfakesplit": {
        "cmd": "--dpi-desync=hostfakesplit --dpi-desync-hostfakesplit-midhost=midsld",
        "description": "Fake host split"
    },
    
    # ========== SYNDATA ==========
    "syndata": {
        "cmd": "--dpi-desync=syndata",
        "description": "SYN with data payload"
    },
    
    # ========== LEGACY FALLBACKS ==========
    "disorder2_badsum": {
        "cmd": "--dpi-desync=disorder2 --dpi-desync-split-pos=1 --dpi-desync-fooling=badsum",
        "description": "Disorder with bad checksum"
    },
    "fake_split2_md5": {
        "cmd": "--dpi-desync=fake,split2 --dpi-desync-ttl=4 --dpi-desync-split-pos=sniext+1 --dpi-desync-fooling=md5sig",
        "description": "Aggressive combo"
    },
}
