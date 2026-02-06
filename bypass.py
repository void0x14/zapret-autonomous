#!/usr/bin/env python3
"""
ZAPRET BYPASS - STANDALONE SCRIPT
No dependencies on other files, self-contained solution.

Usage:
    sudo python3 bypass.py turbo.cr jpg6.su

This script:
1. Uses DoH to bypass DNS poisoning
2. Applies nfqws with working strategies
3. Keeps bypass running in background
"""
import sys
import os
import subprocess
import shutil
import socket
import time
import shlex
import requests
import urllib3
urllib3.disable_warnings()

# ===== CONFIGURATION =====
NFQUEUE_NUM = 200
NFQWS_PATH = shutil.which('nfqws') or '/usr/bin/nfqws'

# Proven strategies for Turkey ISPs
STRATEGIES = [
    ("fake_ttl", "--dpi-desync=fake --dpi-desync-ttl=1 --dpi-desync-fooling=md5sig"),
    ("fake_badsum", "--dpi-desync=fake --dpi-desync-fooling=badsum"),
    ("split", "--dpi-desync=fake,fakedsplit --dpi-desync-ttl=1 --dpi-desync-split-pos=1"),
    ("disorder", "--dpi-desync=fake,disorder2 --dpi-desync-ttl=1 --dpi-desync-split-pos=1"),
    ("combo", "--dpi-desync=fake,multisplit --dpi-desync-ttl=3 --dpi-desync-split-pos=1,midsld --dpi-desync-fooling=md5sig"),
]

def check_root():
    if os.geteuid() != 0:
        print("❌ Root gerekli: sudo python3 bypass.py <domain>")
        sys.exit(1)

def resolve_via_doh(domain: str) -> str:
    """Cloudflare DoH ile gerçek IP'yi al."""
    print(f"[DoH] {domain} için gerçek IP alınıyor...")
    
    try:
        # Cloudflare DoH
        resp = requests.get(
            "https://cloudflare-dns.com/dns-query",
            params={"name": domain, "type": "A"},
            headers={"Accept": "application/dns-json"},
            timeout=10,
            verify=False
        )
        data = resp.json()
        
        if "Answer" in data:
            for ans in data["Answer"]:
                if ans.get("type") == 1:
                    ip = ans.get("data")
                    if ip and not ip.startswith("0.") and ip != "127.0.0.1":
                        print(f"[DoH] ✓ {domain} -> {ip}")
                        return ip
    except Exception as e:
        print(f"[DoH] Cloudflare failed: {e}")
    
    try:
        # Google DoH fallback
        resp = requests.get(
            "https://dns.google/resolve",
            params={"name": domain, "type": "A"},
            timeout=10,
            verify=False
        )
        data = resp.json()
        
        if "Answer" in data:
            for ans in data["Answer"]:
                if ans.get("type") == 1:
                    ip = ans.get("data")
                    if ip and not ip.startswith("0.") and ip != "127.0.0.1":
                        print(f"[DoH] ✓ {domain} -> {ip} (Google)")
                        return ip
    except Exception as e:
        print(f"[DoH] Google failed: {e}")
    
    # Last resort: normal DNS
    try:
        ip = socket.gethostbyname(domain)
        if not ip.startswith("0."):
            return ip
    except:
        pass
    
    print(f"[DoH] ❌ IP alınamadı!")
    return None

def cleanup():
    """Eski kuralları temizle."""
    print("[CLEANUP] Eski kurallar temizleniyor...")
    subprocess.run(['pkill', '-9', 'nfqws'], capture_output=True)
    subprocess.run(['iptables', '-t', 'mangle', '-F', 'POSTROUTING'], capture_output=True)
    subprocess.run(['iptables', '-t', 'mangle', '-F', 'OUTPUT'], capture_output=True)

def add_iptables_rules(target_ip: str):
    """NFQUEUE kuralları ekle."""
    print(f"[IPTABLES] Kurallar ekleniyor ({target_ip})...")
    
    # POSTROUTING için (genel)
    subprocess.run([
        'iptables', '-t', 'mangle', '-A', 'POSTROUTING',
        '-p', 'tcp', '-m', 'multiport', '--dports', '80,443',
        '-m', 'connbytes', '--connbytes-dir=original', '--connbytes-mode=packets', '--connbytes', '1:6',
        '-m', 'mark', '!', '--mark', '0x40000000/0x40000000',
        '-j', 'NFQUEUE', '--queue-num', str(NFQUEUE_NUM), '--queue-bypass'
    ], capture_output=True)
    
    # OUTPUT için (spesifik IP)
    subprocess.run([
        'iptables', '-t', 'mangle', '-A', 'OUTPUT',
        '-p', 'tcp', '--dport', '443', '-d', target_ip,
        '-j', 'NFQUEUE', '--queue-num', str(NFQUEUE_NUM), '--queue-bypass'
    ], capture_output=True)
    
    print("[IPTABLES] ✓ Kurallar eklendi")

def test_connection(domain: str, ip: str) -> bool:
    """Bağlantıyı test et."""
    try:
        resp = requests.get(
            f"https://{ip}",
            headers={"Host": domain, "User-Agent": "Mozilla/5.0"},
            timeout=8,
            verify=False,
            allow_redirects=True
        )
        return resp.status_code < 400
    except:
        return False

def start_nfqws(strategy_args: str) -> subprocess.Popen:
    """nfqws başlat."""
    cmd = [NFQWS_PATH, f'--qnum={NFQUEUE_NUM}'] + shlex.split(strategy_args)
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )
    return proc

def find_working_strategy(domain: str, ip: str) -> str:
    """Çalışan stratejiyi bul."""
    print(f"\n[PROBE] Stratejiler test ediliyor...")
    
    for name, args in STRATEGIES:
        print(f"  [{name}] Test ediliyor...", end=" ", flush=True)
        
        # nfqws başlat
        proc = start_nfqws(args)
        time.sleep(0.5)
        
        # Test et
        if test_connection(domain, ip):
            print("✓ ÇALIŞIYOR!")
            return name, args, proc
        else:
            print("✗")
            proc.terminate()
            try:
                proc.wait(timeout=1)
            except:
                proc.kill()
    
    return None, None, None

def main():
    if len(sys.argv) < 2:
        print("Kullanım: sudo python3 bypass.py <domain> [domain2] ...")
        sys.exit(1)
    
    check_root()
    domains = sys.argv[1:]
    
    print("="*50)
    print("  ZAPRET BYPASS - STANDALONE")
    print("="*50)
    
    # Temizlik
    cleanup()
    
    for domain in domains:
        print(f"\n[TARGET] {domain}")
        
        # 1. DNS çöz (DoH ile)
        ip = resolve_via_doh(domain)
        if not ip:
            print(f"❌ {domain} için IP alınamadı, atlanıyor...")
            continue
        
        # 2. iptables kuralları ekle
        add_iptables_rules(ip)
        
        # 3. Çalışan stratejiyi bul
        name, args, proc = find_working_strategy(domain, ip)
        
        if proc:
            print(f"\n{'='*50}")
            print(f"  ✓ BYPASS AKTİF!")
            print(f"  Domain: {domain}")
            print(f"  IP: {ip}")
            print(f"  Strateji: {name}")
            print(f"  nfqws PID: {proc.pid}")
            print(f"{'='*50}")
            print("\nTerminal serbest, nfqws arka planda çalışıyor.")
            print("Durdurmak için: sudo pkill nfqws && sudo iptables -t mangle -F")
            break
        else:
            print(f"❌ {domain} için çalışan strateji bulunamadı")
    else:
        print("\n❌ Hiçbir domain için bypass aktif edilemedi!")
        cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main()
