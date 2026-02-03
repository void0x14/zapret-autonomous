# Heuristics for Turkey ISPs
# These are passed to nfqws binaries

STRATEGIES = {
    "fake": {
        "cmd": "--dpi-desync=fake",
        "desc": "Send fake packet with bad checksum/ttl"
    },
    "disorder2": {
        "cmd": "--dpi-desync=disorder2",
        "desc": "Send packets out of order (Seq/Ack manipulation)"
    },
    "split2": {
        "cmd": "--dpi-desync=split2",
        "desc": "Split TCP packet into two at pos 2"
    },
    "combo_1": {
        "cmd": "--dpi-desync=fake,disorder2",
        "desc": "Combo: Fake + Disorder"
    },
    "combo_2": {
        "cmd": "--dpi-desync=fake,split2",
        "desc": "Combo: Fake + Split"
    },
    "syndata": {
        "cmd": "--dpi-desync=syndata",
        "desc": "Send data in SYN packet (may break some implementations)"
    }
}

# The order to try them in (Priority high to low)
PRIORITY_LIST = [
    "fake",
    "disorder2",
    "split2",
    "combo_1",
    "combo_2"
]
