import logging
import threading
from netfilterqueue import NetfilterQueue
from scapy.all import IP, TCP, Raw
from scapy.layers.tls.record import TLS
from scapy.layers.tls.handshake import TLSClientHello
from core.db import StrategyDB

# Conf
QUEUE_NUM = 1

class PacketInterceptor:
    def __init__(self, db: StrategyDB, on_new_domain):
        self.db = db
        self.nfqueue = NetfilterQueue()
        self.on_new_domain = on_new_domain  # Callback when a new domain is seen
        self.running = False
        self.thread = None

    def _process_packet(self, packet):
        """
        Callback for NFQueue.
        1. Parse Packet
        2. Extract SNI (Domain)
        3. Check DB -> If exists, let Zapret handle it (ACCEPT)
        4. If not exists -> Trigger Solver (or pass if whitelist)
        """
        try:
            scapy_pkt = IP(packet.get_payload())
            
            # We only care about TCP Syn (Start of connection) to grab SNI
            # Note: SNI is actually in the ACK+PSH usually, or after handshake? 
            # Actually SNI is in ClientHello, which is the first data packet after handshake.
            # Capturing SYN is not enough for SNI. We need to capture ClientHello.
            
            if scapy_pkt.haslayer(TCP) and scapy_pkt.haslayer(Raw):
                # Try to parse TLS
                # This is a simplified check for TLS Client Hello
                payload = scapy_pkt[Raw].load
                if len(payload) > 5 and payload[0] == 0x16: # Handshake
                    # Extract SNI... (Simplified for prototype)
                    # For now, we will assume we can extract it or pass it.
                    # In a real implementation, we need robust SNI parsing.
                    pass
            
            # For specific user requirement: "Fast Solver"
            # We accept everything by default. 
            # We only want to INTERCEPT if we detect a BLOCK.
            # But NFQueue is inline.
            
            # Strategy:
            # We pass everything.
            # But we also start a separate "Sniffer" (Async Sniffer) to detect RST packets coming FROM the server?
            # Or we use NFQueue to drop RST packets?
            
            packet.accept()
            
        except Exception as e:
            logging.error(f"Error processing packet: {e}")
            packet.accept() # Fail open

    def start(self):
        logging.info(f"Starting Interceptor on Queue {QUEUE_NUM}...")
        self.nfqueue.bind(QUEUE_NUM, self._process_packet)
        self.running = True
        self.nfqueue.run() # This blocks, so we run in thread if needed?
        # Actually NetfilterQueue.run() is blocking.

    def start_threaded(self):
        self.thread = threading.Thread(target=self.start)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.running = False
        self.nfqueue.unbind()
