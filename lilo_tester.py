#!/usr/bin/env python3
"""
🦊 LILO TESTER v5.0.0 – Deep DAST Edition (Full Local, Zero AI API)

Gabungan v4.5.0 (Advanced Performance Analytics) + v5.0.0 (Deep DAST)
Mempertahankan seluruh logika asli kedua versi tanpa menambah fitur baru.

Fitur:
- Deep SPA & Headless Crawler (Shadow DOM traversal, interactive element clicking,
  JavaScript bundle & source‑map endpoint extraction)
- Smart Context‑Aware Fuzzer (XSS & SQLi with HTML attribute / script string / comment escape)
- Out‑of‑Band Interaction Engine (Interactsh local / self‑hosted, blind SSRF/RCE/XSS/SQLi detection)
- Multi‑Role IDOR/BOLA Engine (dual session replay attack)
- Advanced Performance Analytics (Web Vitals, resource waterfall, scoring)
- Full‑page Screenshot with watermark (pages, security findings, errors)
- Collapsible HTML Report with new tabs for Deep API, IDOR, Smart Fuzz results

Author: Lilo
"""

import argparse
import asyncio
import base64
import difflib
import hashlib
import json
import os
import platform
import re
import sys
import time
import traceback
import urllib.parse
import webbrowser
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse, parse_qs

import aiohttp
from jinja2 import BaseLoader, Environment, select_autoescape
from PIL import Image, ImageDraw, ImageFont
from playwright.async_api import (
    BrowserContext,
    Page,
    Request,
    Response,
    Route,
    async_playwright,
    Error as PlaywrightError,
)
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    track,
)
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table
from rich.text import Text
from rich.syntax import Syntax

# Interactsh (fully local self-hosted compatible)
try:
    from interactsh import InteractshClient
    HAS_INTERACTSH = True
except ImportError:
    HAS_INTERACTSH = False

console = Console()

APP_NAME = "Lilo Tester"
APP_VERSION = "5.0.0"
DEFAULT_WATERMARK = "Lilo Tester"

# ═══════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════


async def load_payloads(filepath):
    if not filepath or not os.path.exists(filepath):
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                yield line.strip()

COMMON_LOGIN_PATHS = [
    "/login", "/admin/login", "/auth/login", "/signin", "/sign-in",
    "/masuk", "/admin", "/dashboard/login", "/wp-admin", "/wp-login.php",
    "/user/login", "/account/login", "/auth",
]

DASHBOARD_INDICATORS = [
    "dashboard", "admin", "panel", "backend", "control", "manage", "console",
]

NAV_SELECTORS = [
    "nav a[href]", "aside a[href]", ".sidebar a[href]", ".menu a[href]",
    ".drawer a[href]", ".navbar a[href]", ".sidenav a[href]",
    ".main-menu a[href]", ".navigation a[href]",
    "[role='navigation'] a[href]", ".nav-menu a[href]", ".nav a[href]",
    ".menu-item a[href]", ".sidebar-menu a[href]", ".sidebar-nav a[href]",
]

EXPANDABLE_SELECTORS = [
    "[aria-expanded='false']", ".collapsed", ".accordion-button.collapsed",
    "[data-bs-toggle='collapse']", ".dropdown-toggle",
    ".has-submenu > a", ".menu-item-has-children > a",
    ".treeview > a", "summary:not([open])",
]

MICRO_INTERACTIONS = {
    "search_input": {
        "name": "Search Input",
        "selectors": [
            'input[type="search"]', 'input[name*="search" i]',
            'input[placeholder*="search" i]', 'input[placeholder*="cari" i]',
            '.search-input input', '.search-box input',
        ],
        "test_action": "type_test_query",
    },
    "filter_dropdown": {
        "name": "Filter Dropdown",
        "selectors": [
            'select.filter', 'select[name*="filter" i]',
            '.filter-select select', '[data-filter] select',
        ],
        "test_action": "change_select_option",
    },
    "pagination": {
        "name": "Pagination",
        "selectors": [
            '.pagination', '.pager', '[data-pagination]',
            'nav[aria-label*="pagination" i]', '.dataTables_paginate',
        ],
        "test_action": "click_page_2",
    },
    "sort_buttons": {
        "name": "Sort Buttons",
        "selectors": [
            'th.sortable', 'th[aria-sort]', '.sort-icon',
            '[data-sort]', 'th.sorting',
        ],
        "test_action": "click_first_sortable",
    },
    "tab_navigation": {
        "name": "Tab Navigation",
        "selectors": [
            '.nav-tabs a', '.tab-nav a', '[role="tablist"] [role="tab"]',
            '.tabs a', '.tab-button',
        ],
        "test_action": "click_second_tab",
    },
    "modal_buttons": {
        "name": "Modal Buttons",
        "selectors": [
            '[data-toggle="modal"]', '[data-bs-toggle="modal"]',
            '[data-target*="modal" i]', '.modal-trigger',
        ],
        "test_action": "click_and_close_modal",
    },
    "dropdown_menus": {
        "name": "Dropdown Menus",
        "selectors": [
            '.dropdown:not(.open):not(.show)', '.btn-group',
            '[data-dropdown]', '.has-dropdown',
        ],
        "test_action": "toggle_dropdown",
    },
    "accordion": {
        "name": "Accordion",
        "selectors": [
            '.accordion .accordion-button', '[data-toggle="collapse"]',
        ],
        "test_action": "toggle_accordion",
    },
    "form_validation": {
        "name": "Form Validation",
        "selectors": ['form', '.form-container', '.crud-form'],
        "test_action": "test_empty_submission",
    },
    "datepicker": {
        "name": "Datepicker",
        "selectors": [
            'input[type="date"]', 'input.datepicker', '[data-datepicker]',
        ],
        "test_action": "type_date_and_check",
    },
    "checkbox_radio": {
        "name": "Checkbox & Radio",
        "selectors": ['input[type="checkbox"]', 'input[type="radio"]'],
        "test_action": "toggle_checkbox",
    },
    "select_dropdown": {
        "name": "Select Dropdown",
        "selectors": ['select:not([multiple])', '.select2', '.choices'],
        "test_action": "change_option",
    },
    "rich_text_editor": {
        "name": "Rich Text Editor",
        "selectors": [
            '.ql-editor', '.cke_editable', '.tox-edit-area',
            '[contenteditable="true"]',
        ],
        "test_action": "type_in_editor",
    },
    "file_upload": {
        "name": "File Upload",
        "selectors": ['input[type="file"]', '.dropzone', '.file-upload'],
        "test_action": "check_upload_exists",
    },
    "data_table": {
        "name": "Data Table",
        "selectors": [
            'table.dataTable', '.datatable', 'table.table',
            '.table-responsive table', '[role="grid"]',
        ],
        "test_action": "check_table_interactive",
    },
}

COMPONENT_SELECTORS = {
    "DataTable": [".dataTable", ".datatable", "table.data-table"],
    "AG Grid": [".ag-theme-alpine", ".ag-theme-balham"],
    "Select2": [".select2-container", ".select2"],
    "Datepicker": ["input.datepicker", ".datepicker"],
    "CKEditor": [".cke", ".ck-editor"],
    "TinyMCE": [".tox-tinymce", ".mce-tinymce"],
    "ChartJS": ["canvas[id*='chart']"],
    "ApexCharts": [".apexcharts-canvas"],
    "FullCalendar": [".fc", "#calendar"],
    "Dropzone": [".dropzone", ".dz-clickable"],
    "Modal": [".modal", "[role='dialog']"],
}

XSS_PAYLOADS = [
    "<script>window.__LILO_XSS__=true</script>",
    "<img src=x onerror=window.__LILO_XSS__=true>",
    "'\"><svg/onload=window.__LILO_XSS__=true>",
    "javascript:window.__LILO_XSS__=true"
]

SQLI_TEST_STRINGS = [
    "'", "\"", "' OR '1'='1", "' OR 1=1--",
    "1' AND (SELECT * FROM (SELECT(SLEEP(6)))a)--",
    "1'; WAITFOR DELAY '0:0:6'--",
    "1' || pg_sleep(6)--"
]

SENSITIVE_FILES = [
    ".env", ".env.backup", ".env.local", ".env.production",
    ".git/config", ".git/HEAD", "wp-config.php", "wp-config.php.bak",
    "config.php", "config.php.bak", "database.yml", "credentials.json",
    "backup.sql", "backup.zip", "phpinfo.php", "info.php",
    "robots.txt", "sitemap.xml", ".DS_Store", ".htaccess",
    "web.config", "composer.json", "package.json", "Dockerfile",
    "docker-compose.yml", ".travis.yml", ".gitlab-ci.yml",
    "debug.log", "error.log", "readme.html",
    # Active Directory & Endpoint Fuzzing additions
    "api/v1/users", "api/v1/admin", "api/users", "api/admin",
    "graphql", "swagger-ui.html", "api-docs", "v1/api-docs",
    "admin/", "administrator/", "login.php", "admin_login",
    "phpmyadmin/", "pma/", "dbadmin/", "mysqladmin/",
    "server-status", "actuator/health", "actuator/env",
    "test.php", "dev.php", "shell.php", "cmd.php",
    "backup/", "db/", "sql/", "dump.sql", "db.sqlite3"
]

SECURITY_HEADERS = {
    "Strict-Transport-Security": {"description": "HTTP Strict Transport Security (HSTS)", "severity": "medium", "recommendation": "max-age=31536000; includeSubDomains"},
    "Content-Security-Policy": {"description": "Content Security Policy (CSP)", "severity": "high", "recommendation": "default-src 'self'"},
    "X-Frame-Options": {"description": "Clickjacking Protection", "severity": "medium", "recommendation": "DENY or SAMEORIGIN"},
    "X-Content-Type-Options": {"description": "MIME Type Sniffing Protection", "severity": "low", "recommendation": "nosniff"},
    "Referrer-Policy": {"description": "Referrer Information Control", "severity": "low", "recommendation": "strict-origin-when-cross-origin"},
    "Permissions-Policy": {"description": "Browser Feature Permissions", "severity": "low", "recommendation": "camera=(), microphone=(), geolocation=()"},
    "Access-Control-Allow-Origin": {"description": "CORS Policy", "severity": "high", "recommendation": "Should not be *"},
    "Cross-Origin-Resource-Policy": {"description": "Cross-Origin Resource Policy", "severity": "medium", "recommendation": "same-origin"},
}

INFO_DISCLOSURE_PATTERNS = [
    (r'(?:password|passwd|pwd|secret|token|api[_-]?key)\s*[=:]\s*[\'"][^\'"]+[\'"]', "Hardcoded credentials"),
    (r'(?:AWS)_?(?:ACCESS|SECRET|SESSION)_?(?:KEY|TOKEN)', "AWS credentials"),
    (r'(?:-----BEGIN\s(?:RSA|DSA|EC|OPENSSH)\sPRIVATE\sKEY-----)', "Private key"),
    (r'(?:mongodb|mysql|postgresql|redis)://[^/\s]+', "Database connection string"),
    (r'(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}', "GitHub token"),
    (r'sk-[A-Za-z0-9]{32,}', "Stripe API key"),
    (r'AIza[0-9A-Za-z\-_]{35}', "Google API key"),
]

# ═══════════════════════════════════════════
# UTILITY CLASSES & FUNCTIONS
# ═══════════════════════════════════════════

class SystemDetector:
    @staticmethod
    def get_os() -> str:
        system = platform.system().lower()
        if system == "windows": return "windows"
        if system == "darwin": return "macos"
        return "linux"

    @staticmethod
    def get_font_paths() -> List[str]:
        os_type = SystemDetector.get_os()
        if os_type == "windows":
            return ["C:\\Windows\\Fonts\\segoeui.ttf", "C:\\Windows\\Fonts\\Arial.ttf"]
        if os_type == "macos":
            return ["/System/Library/Fonts/SFNS.ttf", "/Library/Fonts/Arial.ttf"]
        return ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]

def normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url

def clean_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        cleaned = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if cleaned.endswith("/") and parsed.path not in ("", "/"):
            cleaned = cleaned.rstrip("/")
        if parsed.query:
            cleaned += f"?{parsed.query}"
        return cleaned
    except Exception:
        return url

def same_domain(base_domain: str, url: str) -> bool:
    try:
        return urlparse(url).netloc == base_domain
    except Exception:
        return False

def truncate(value: Any, length: int = 240) -> str:
    text = str(value or "")
    return text if len(text) <= length else text[: length - 3] + "..."

def format_bytes(size: float) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024: return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

def format_ms(ms: float) -> str:
    if ms < 1000: return f"{ms:.0f}ms"
    return f"{ms/1000:.2f}s"

def get_banner() -> str:
    return f"""
[bold cyan]
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   ██╗     ██╗██╗      ██████╗     ██╗   ██╗██╗  ██╗              ║
║   ██║     ██║██║     ██╔═══██╗    ██║   ██║██║  ██║              ║
║   ██║     ██║██║     ██║   ██║    ██║   ██║███████║              ║
║   ██║     ██║██║     ██║   ██║    ╚██╗ ██╔╝╚════██║              ║
║   ███████╗██║███████╗╚██████╔╝     ╚████╔╝      ██║              ║
║   ╚══════╝╚═╝╚══════╝ ╚═════╝       ╚═══╝       ╚═╝              ║
║                                                                  ║
║             -- The Ultimate Web Security Scanner --              ║
╚══════════════════════════════════════════════════════════════════╝
[/bold cyan]
"""

class WatermarkEngine:
    def __init__(self, text: str = DEFAULT_WATERMARK, opacity: int = 170):
        self.text = text
        self.opacity = opacity
        self.font = self._load_font()

    def _load_font(self):
        for path in SystemDetector.get_font_paths():
            if os.path.exists(path):
                try: return ImageFont.truetype(path, 24)
                except Exception: continue
        return ImageFont.load_default()

    def apply(self, image_path: str) -> bool:
        try:
            img = Image.open(image_path)
            if img.mode != "RGBA": img = img.convert("RGBA")
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            bbox = draw.textbbox((0, 0), self.text, font=self.font)
            text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            x, y = img.width - text_w - 20, img.height - text_h - 20
            draw.rectangle([x-10, y-10, x+text_w+10, y+text_h+10], fill=(0, 0, 0, self.opacity))
            draw.text((x, y), self.text, font=self.font, fill=(255, 255, 255, 255))
            img = Image.alpha_composite(img, overlay)
            img.save(image_path)
            return True
        except Exception:
            return False

class CredentialManager:
    def __init__(self):
        self.creds_dir = Path.home() / ".lilo_tester"
        self.creds_file = self.creds_dir / "credentials.json"
        self.creds_dir.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        if self.creds_file.exists():
            try: self.credentials = json.load(open(self.creds_file, "r"))
            except Exception: self.credentials = {}
        else: self.credentials = {}

    def _save(self):
        with open(self.creds_file, "w") as f:
            json.dump(self.credentials, f, indent=2)

    def get_domain_key(self, url: str) -> str:
        return urlparse(url).netloc

    def get_credentials(self, url: str) -> List[Dict[str, str]]:
        return self.credentials.get(self.get_domain_key(url), [])

    def save_credential(self, url: str, username: str, password: str, label: str = ""):
        domain = self.get_domain_key(url)
        if domain not in self.credentials: self.credentials[domain] = []
        for cred in self.credentials[domain]:
            if cred["username"] == username:
                cred["password"] = password
                cred["label"] = label or username
                cred["saved_at"] = datetime.now().isoformat()
                self._save()
                return
        self.credentials[domain].append({
            "username": username, "password": password, "label": label or username,
            "saved_at": datetime.now().isoformat(), "login_url": url,
        })
        self._save()

    def delete_credential(self, url: str, index: int):
        domain = self.get_domain_key(url)
        if domain in self.credentials and 0 <= index < len(self.credentials[domain]):
            self.credentials[domain].pop(index)
            if not self.credentials[domain]:
                del self.credentials[domain]
            self._save()

    def select_credential_interactive(self, url: str) -> Optional[Dict[str, str]]:
        creds = self.get_credentials(url)
        if not creds: return None
        console.print(f"\n[bold cyan]📋 Saved credentials for {self.get_domain_key(url)}:[/bold cyan]")
        for i, cred in enumerate(creds, 1):
            console.print(f"  ({i}) [green]{cred['label']}[/green] - [dim]{cred['username']}[/dim]")
        console.print(f"  (0) [yellow]Login with new credentials[/yellow]")
        choice = Prompt.ask("\n[bold]Choose option[/bold]", default="1")
        if choice == "0": return None
        idx = int(choice) - 1
        if 0 <= idx < len(creds): return creds[idx]
        return None

class ErrorTracker:
    def __init__(self, output_dir: Path):
        self.errors: List[Dict[str, Any]] = []
        self.output_dir = output_dir
        self.error_screenshots_dir = output_dir / "error_screenshots"
        self.error_screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.error_counter = 0

    def add_error(self, error_type, message, page_url="", component="", selector="", stack_trace="", extra=None):
        self.error_counter += 1
        err = {
            "id": self.error_counter, "type": error_type, "message": str(message)[:500],
            "page_url": page_url, "component": component, "selector": selector,
            "stack_trace": stack_trace[:1000] if stack_trace else "",
            "timestamp": datetime.now().isoformat(), "extra": extra or {}, "screenshot": "",
        }
        self.errors.append(err)
        return err

    async def capture_error_screenshot(self, page: Page, error_id: int) -> Optional[str]:
        try:
            filename = f"error_{error_id}_{datetime.now().strftime('%H%M%S')}.png"
            filepath = self.error_screenshots_dir / filename
            await page.screenshot(path=str(filepath), full_page=True)
            rel = str(filepath.relative_to(self.output_dir))
            for err in self.errors:
                if err["id"] == error_id: err["screenshot"] = rel
            return rel
        except Exception: return None

    def get_summary(self) -> Dict[str, Any]:
        by_type = defaultdict(list)
        by_page = defaultdict(list)
        for e in self.errors:
            by_type[e["type"]].append(e)
            if e.get("page_url"):
                by_page[e["page_url"]].append(e)
        return {
            "total": len(self.errors),
            "by_type": {k: len(v) for k, v in by_type.items()},
            "by_page": {k: len(v) for k, v in by_page.items()},
            "errors": self.errors,
        }

class ResourceTiming:
    def __init__(self): self.url=""; self.type=""; self.start_time=0; self.duration=0; self.size=0; self.transfer_size=0; self.status=0; self.cached=False; self.compressed=False; self.blocking=False; self.third_party=False; self.domain=""
    def to_dict(self): return {"url":self.url,"type":self.type,"duration_ms":round(self.duration,2),"size_bytes":self.size,"size_formatted":format_bytes(self.size),"transfer_size":self.transfer_size,"status":self.status,"cached":self.cached,"compressed":self.compressed,"blocking":self.blocking,"third_party":self.third_party,"domain":self.domain}

class AdvancedPerformanceTracker:
    def __init__(self, domain: str):
        self.domain = domain
        self.resources: List[ResourceTiming] = deque(maxlen=1000)
        self.page_metrics: Dict[str, Any] = {}
        self.page_timings: List[Dict] = []
        self.resource_start_times: Dict[str, float] = {}
        self.slow_threshold_ms = 3000
        self.total_page_size = 0
        self.total_requests = 0
        self.total_js_size = 0
        self.total_css_size = 0
        self.total_image_size = 0
        self.total_font_size = 0
        self.lcp = 0
        self.fcp = 0
        self.ttfb = 0
        self.cls = 0
        self.dom_content_loaded = 0
        self.dom_elements = 0
        self.dom_depth = 0

    def record_resource_start(self, request: Request):
        self.resource_start_times[request.url] = time.time() * 1000

    def record_resource(self, request: Request, response: Response):
        r = ResourceTiming()
        r.url = response.url
        r.status = response.status
        r.domain = urlparse(response.url).netloc
        r.third_party = r.domain != self.domain and r.domain != ""
        content_type = response.headers.get("content-type", "").lower()
        if request.resource_type in ["document","script","stylesheet","image","font","fetch","xhr"]:
            r.type = request.resource_type
        elif "javascript" in content_type: r.type = "script"
        elif "css" in content_type: r.type = "stylesheet"
        elif "image" in content_type: r.type = "image"
        elif "font" in content_type or "woff" in content_type: r.type = "font"
        elif "json" in content_type: r.type = "fetch"
        else: r.type = "other"
        start = self.resource_start_times.get(response.url, 0)
        r.start_time = start
        r.duration = (time.time()*1000) - start if start > 0 else 0
        content_length = response.headers.get("content-length", "0")
        try: r.size = int(content_length) if content_length.isdigit() else 0
        except Exception: r.size = 0
        r.transfer_size = r.size
        cache = response.headers.get("cache-control","").lower()
        r.cached = "no-cache" not in cache and "no-store" not in cache
        r.compressed = response.headers.get("content-encoding","") in ["gzip","br","deflate"]
        if r.type in ["script","stylesheet"]: r.blocking = True
        self.total_requests += 1
        self.total_page_size += r.size
        if r.type=="script": self.total_js_size += r.size
        elif r.type=="stylesheet": self.total_css_size += r.size
        elif r.type=="image": self.total_image_size += r.size
        elif r.type=="font": self.total_font_size += r.size
        self.resources.append(r)

    async def measure_web_vitals(self, page: Page):
        try:
            metrics = await page.evaluate("""() => {
                const result = {};
                const nav = performance.getEntriesByType('navigation')[0];
                if (nav) {
                    result.ttfb = nav.responseStart - nav.requestStart;
                    result.domContentLoaded = nav.domContentLoadedEventEnd - nav.fetchStart;
                    result.domComplete = nav.domComplete - nav.fetchStart;
                }
                const paint = performance.getEntriesByType('paint');
                for (const p of paint) {
                    if (p.name === 'first-contentful-paint') result.fcp = p.startTime;
                    if (p.name === 'first-paint') result.fp = p.startTime;
                }
                const lcpEntries = performance.getEntriesByType('largest-contentful-paint');
                if (lcpEntries.length > 0) {
                    result.lcp = lcpEntries[lcpEntries.length - 1].startTime;
                }
                result.domElements = document.querySelectorAll('*').length;
                let maxDepth = 0;
                function getDepth(el, depth) {
                    if (depth > maxDepth) maxDepth = depth;
                    for (const child of el.children) getDepth(child, depth + 1);
                }
                getDepth(document.body, 0);
                result.domDepth = maxDepth;
                result.scripts = document.querySelectorAll('script').length;
                result.stylesheets = document.querySelectorAll('link[rel="stylesheet"]').length;
                result.images = document.querySelectorAll('img').length;
                const layoutShifts = performance.getEntriesByType('layout-shift');
                let cls = 0;
                for (const ls of layoutShifts) {
                    if (!ls.hadRecentInput) cls += ls.value;
                }
                result.cls = cls;
                return result;
            }""")
            if metrics:
                self.fcp = metrics.get("fcp", 0)
                self.lcp = metrics.get("lcp", 0)
                self.ttfb = metrics.get("ttfb", 0)
                self.cls = metrics.get("cls", 0)
                self.dom_content_loaded = metrics.get("domContentLoaded", 0)
                self.dom_elements = metrics.get("domElements", 0)
                self.dom_depth = metrics.get("domDepth", 0)
                self.page_metrics = metrics
        except Exception as e:
            console.print(f"[dim]⚠️ Web Vitals measurement limited: {truncate(e)}[/dim]")

    def calculate_performance_score(self) -> int:
        score = 100
        if self.ttfb > 800: score -= 20
        elif self.ttfb > 400: score -= 10
        elif self.ttfb > 200: score -= 5
        if self.fcp > 2500: score -= 25
        elif self.fcp > 1800: score -= 15
        elif self.fcp > 1000: score -= 5
        if self.lcp > 4000: score -= 25
        elif self.lcp > 2500: score -= 15
        elif self.lcp > 1500: score -= 5
        if self.cls > 0.25: score -= 20
        elif self.cls > 0.1: score -= 10
        elif self.cls > 0.05: score -= 5
        if self.total_page_size > 5_000_000: score -= 20
        elif self.total_page_size > 2_000_000: score -= 10
        elif self.total_page_size > 1_000_000: score -= 5
        if self.total_requests > 100: score -= 15
        elif self.total_requests > 50: score -= 8
        elif self.total_requests > 30: score -= 3
        if self.dom_elements > 3000: score -= 10
        elif self.dom_elements > 1500: score -= 5
        return max(score, 0)

    def get_performance_grade(self, score: int) -> str:
        if score >= 90: return "A"
        if score >= 75: return "B"
        if score >= 60: return "C"
        if score >= 40: return "D"
        return "F"

    def get_recommendations(self) -> List[Dict[str, str]]:
        recs = []
        if self.ttfb > 400: recs.append({"priority":"high","title":"Improve server response time","description":f"TTFB is {format_ms(self.ttfb)}. Consider using CDN, caching, or upgrading hosting."})
        if self.lcp > 2500: recs.append({"priority":"high","title":"Optimize Largest Contentful Paint","description":f"LCP is {format_ms(self.lcp)}. Optimize main image, text, or hero element loading."})
        if self.fcp > 1800: recs.append({"priority":"medium","title":"Improve First Contentful Paint","description":f"FCP is {format_ms(self.fcp)}. Reduce render-blocking resources."})
        if self.cls > 0.1: recs.append({"priority":"medium","title":"Fix layout shifts","description":f"CLS is {self.cls:.3f}. Set explicit sizes on images, iframes, and dynamic content."})
        if self.total_page_size > 2_000_000: recs.append({"priority":"high","title":"Reduce page size","description":f"Page size is {format_bytes(self.total_page_size)}. Compress images, minify JS/CSS, use lazy loading."})
        if self.total_requests > 50: recs.append({"priority":"medium","title":"Reduce HTTP requests","description":f"{self.total_requests} requests. Bundle files, use sprites, remove unused code."})
        if self.total_js_size > 500_000: recs.append({"priority":"high","title":"Reduce JavaScript size","description":f"JS is {format_bytes(self.total_js_size)}. Use code splitting, tree shaking, defer non-critical JS."})
        if self.total_image_size > 1_000_000: recs.append({"priority":"medium","title":"Optimize images","description":f"Images are {format_bytes(self.total_image_size)}. Use WebP/AVIF, lazy loading, responsive images."})
        blocking = [r for r in self.resources if r.blocking and r.type in ["script","stylesheet"]]
        if len(blocking) > 5: recs.append({"priority":"medium","title":"Reduce render-blocking resources","description":f"{len(blocking)} render-blocking resources. Defer JS, inline critical CSS."})
        uncached = [r for r in self.resources if not r.cached and r.size > 10000]
        if len(uncached) > 10: recs.append({"priority":"low","title":"Improve caching","description":f"{len(uncached)} resources without caching headers. Add Cache-Control headers."})
        uncompressed = [r for r in self.resources if not r.compressed and r.size > 5000 and r.type in ["script","stylesheet","fetch"]]
        if len(uncompressed) > 5: recs.append({"priority":"medium","title":"Enable compression","description":f"{len(uncompressed)} resources not compressed. Enable gzip/brotli compression."})
        if self.dom_elements > 3000: recs.append({"priority":"low","title":"Simplify DOM","description":f"{self.dom_elements} DOM elements. Reduce DOM size for better performance."})
        return recs

    def record_page_load(self, url: str, load_time: float, status: int = 200):
        is_slow = load_time > self.slow_threshold_ms / 1000
        self.page_timings.append({"url":url,"load_time":round(load_time,2),"slow":is_slow,"status":status,"timestamp":datetime.now().isoformat()})

    def get_summary(self) -> Dict[str, Any]:
        score = self.calculate_performance_score()
        grade = self.get_performance_grade(score)
        recommendations = self.get_recommendations()
        resource_breakdown = {
            "total": {"count":self.total_requests,"size":self.total_page_size,"size_formatted":format_bytes(self.total_page_size)},
            "scripts": {"count":len([r for r in self.resources if r.type=="script"]),"size":self.total_js_size,"size_formatted":format_bytes(self.total_js_size)},
            "stylesheets": {"count":len([r for r in self.resources if r.type=="stylesheet"]),"size":self.total_css_size,"size_formatted":format_bytes(self.total_css_size)},
            "images": {"count":len([r for r in self.resources if r.type=="image"]),"size":self.total_image_size,"size_formatted":format_bytes(self.total_image_size)},
            "fonts": {"count":len([r for r in self.resources if r.type=="font"]),"size":self.total_font_size,"size_formatted":format_bytes(self.total_font_size)},
            "other": {"count":len([r for r in self.resources if r.type not in ["script","stylesheet","image","font"]]),"size":0,"size_formatted":"N/A"},
        }
        sorted_resources = sorted(self.resources, key=lambda r: r.duration, reverse=True)
        slowest = [r.to_dict() for r in sorted_resources[:10] if r.duration > 100]
        sorted_by_size = sorted(self.resources, key=lambda r: r.size, reverse=True)
        largest = [r.to_dict() for r in sorted_by_size[:10] if r.size > 0]
        third_party = defaultdict(lambda: {"count":0,"size":0})
        for r in self.resources:
            if r.third_party:
                third_party[r.domain]["count"] += 1
                third_party[r.domain]["size"] += r.size
        slow_pages = [p for p in self.page_timings if p["slow"]]
        avg_load = sum(p["load_time"] for p in self.page_timings) / max(len(self.page_timings), 1)
        return {
            "score":score,"grade":grade,
            "web_vitals":{"ttfb":round(self.ttfb,2),"ttfb_formatted":format_ms(self.ttfb),
                          "fcp":round(self.fcp,2),"fcp_formatted":format_ms(self.fcp),
                          "lcp":round(self.lcp,2),"lcp_formatted":format_ms(self.lcp),
                          "cls":round(self.cls,4),"dom_content_loaded":round(self.dom_content_loaded,2)},
            "dom_stats":{"elements":self.dom_elements,"depth":self.dom_depth,
                         "scripts":self.page_metrics.get("scripts",0),
                         "stylesheets":self.page_metrics.get("stylesheets",0),
                         "images":self.page_metrics.get("images",0)},
            "resource_breakdown":resource_breakdown,
            "total_requests":self.total_requests,
            "total_page_size":self.total_page_size,
            "total_page_size_formatted":format_bytes(self.total_page_size),
            "slowest_resources":slowest,
            "largest_resources":largest,
            "third_party_domains":{k:{"count":v["count"],"size":format_bytes(v["size"])} for k,v in sorted(third_party.items(), key=lambda x: x[1]["size"], reverse=True)[:10]},
            "recommendations":recommendations,
            "pages_tested":len(self.page_timings),
            "slow_pages":len(slow_pages),
            "average_load_time":round(avg_load,2),
            "slow_pages_list":slow_pages,
            "all_timings":self.page_timings,
            "resources":[r.to_dict() for r in self.resources],
        }

class ScreenshotManager:
    def __init__(self, output_dir: Path, watermark: WatermarkEngine):
        self.output_dir = output_dir
        self.watermark = watermark
        self.screenshots_dir = output_dir / "screenshots"
        self.pages_dir = self.screenshots_dir / "pages"
        self.security_dir = self.screenshots_dir / "security"
        self.errors_dir = self.screenshots_dir / "errors"
        for d in [self.screenshots_dir, self.pages_dir, self.security_dir, self.errors_dir]:
            d.mkdir(parents=True, exist_ok=True)
        self.screenshots: List[Dict] = []

    async def capture_page_screenshot(self, page: Page, url: str, title: str = "", prefix: str = "page") -> Optional[str]:
        try:
            safe_name = re.sub(r'[^a-zA-Z0-9]', '_', url)[:50]
            filename = f"{prefix}_{safe_name}_{datetime.now().strftime('%H%M%S')}.png"
            filepath = self.pages_dir / filename
            await page.screenshot(path=str(filepath), full_page=True)
            self.watermark.apply(str(filepath))
            rel = str(filepath.relative_to(self.output_dir))
            self.screenshots.append({"url":url,"title":title,"screenshot":rel,"type":"page","timestamp":datetime.now().isoformat()})
            return rel
        except Exception as e:
            console.print(f"[dim]⚠️ Screenshot failed: {truncate(e)}[/dim]")
            return None

    async def capture_security_screenshot(self, page: Page, finding_id: str, url: str = "") -> Optional[str]:
        try:
            safe_id = re.sub(r'[^a-zA-Z0-9]', '_', finding_id)[:30]
            filename = f"security_{safe_id}_{datetime.now().strftime('%H%M%S')}.png"
            filepath = self.security_dir / filename
            await page.screenshot(path=str(filepath), full_page=True)
            self.watermark.apply(str(filepath))
            rel = str(filepath.relative_to(self.output_dir))
            self.screenshots.append({"url":url,"title":f"Security: {finding_id}","screenshot":rel,"type":"security","finding_id":finding_id,"timestamp":datetime.now().isoformat()})
            return rel
        except Exception: return None

    def get_all_screenshots(self) -> List[Dict]:
        return self.screenshots

# ═══════════════════════════════════════════
# DEEP DAST MODULES (v5.0.0)
# ═══════════════════════════════════════════

class ContextAnalyzer:
    @staticmethod
    def detect_context(response_body: str, probe_string: str) -> str:
        if probe_string not in response_body:
            return "not_reflected"
        if re.search(rf'<!--[^>]*{re.escape(probe_string)}[^>]*-->', response_body):
            return "html_comment"
        idx = response_body.find(probe_string)
        before = response_body[:idx]
        if re.search(r'<script[^>]*>[^<]*$', before):
            return "script_string"
        if re.search(rf'=\s*["\'][^"\']*{re.escape(probe_string)}[^"\']*["\']', response_body):
            return "html_attribute"
        return "html_body"

class BundleAnalyzer:
    def __init__(self, context: BrowserContext, domain: str):
        self.context = context
        self.domain = domain
        self.found_endpoints: List[str] = []

    async def analyze_scripts(self, script_urls: List[str]):
        for url in script_urls:
            try:
                resp = await self.context.request.get(url, timeout=8000)
                if resp.status == 200:
                    content = await resp.text()
                    endpoints = re.findall(r'["\'](/[a-zA-Z0-9_\-./]+)["\']', content)
                    for ep in endpoints:
                        if ep.startswith("/api") or ep.startswith("/graphql") or re.search(r'/v\d+/', ep):
                            self.found_endpoints.append(urljoin(url, ep))
            except Exception: continue

    async def analyze_source_maps(self, script_urls: List[str]):
        for url in script_urls:
            if not url.endswith(".js"): continue
            map_url = url + ".map"
            try:
                resp = await self.context.request.get(map_url, timeout=8000)
                if resp.status == 200:
                    map_data = await resp.json()
                    if "sources" in map_data:
                        for source in map_data["sources"]:
                            self.found_endpoints.append(source)
            except Exception: pass

# ═══════════════════════════════════════════
# PHASE 1: INTELLIGENCE GATHERING
# ═══════════════════════════════════════════

class SubdomainEnumerator:
    """
    Passive subdomain enumeration via public APIs (crt.sh, HackerTarget).
    Verifies which subdomains are alive via HTTP HEAD, then prompts user
    which target(s) to include in the scan.
    Supports --deep-enum for Level 2 (*.sub.domain.com) discovery.
    """
    SOURCES = {
        "crt.sh": "https://crt.sh/?q=%.{domain}&output=json",
        "HackerTarget": "https://api.hackertarget.com/hostsearch/?q={domain}",
    }

    def __init__(self, domain: str, deep: bool = False):
        # Strip www. to get root domain
        self.root = re.sub(r"^www\.", "", domain)
        self.deep = deep

    async def enumerate(self) -> Dict:
        console.print(f"\n[bold cyan]🌐 Subdomain Enumeration: {self.root}[/bold cyan]")
        raw: Set[str] = set()

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
            # --- crt.sh ---
            try:
                url = self.SOURCES["crt.sh"].format(domain=self.root)
                async with session.get(url, ssl=False) as r:
                    if r.status == 200:
                        data = await r.json(content_type=None)
                        for entry in data:
                            name = entry.get("name_value", "")
                            for n in name.split("\n"):
                                n = n.strip().lstrip("*.")
                                if n.endswith(self.root):
                                    raw.add(n.lower())
                console.print(f"  [green]crt.sh:[/green] {len(raw)} entries")
            except Exception as e:
                console.print(f"  [yellow]crt.sh failed: {e}[/yellow]")

            # --- HackerTarget ---
            ht_count = 0
            try:
                url = self.SOURCES["HackerTarget"].format(domain=self.root)
                async with session.get(url, ssl=False) as r:
                    if r.status == 200:
                        text = await r.text()
                        if "error check your" not in text.lower():
                            for line in text.splitlines():
                                parts = line.split(",")
                                if parts and parts[0].endswith(self.root):
                                    raw.add(parts[0].strip().lower())
                                    ht_count += 1
                console.print(f"  [green]HackerTarget:[/green] {ht_count} entries")
            except Exception as e:
                console.print(f"  [yellow]HackerTarget failed: {e}[/yellow]")

        # Filter: Level 1 only unless --deep-enum
        # Level 1 = exactly one extra label (sub.root.com)
        candidates = set()
        for sub in raw:
            labels = sub.replace(self.root, "").rstrip(".").split(".")
            labels = [l for l in labels if l]
            depth = len(labels)
            if depth == 0:
                continue  # skip root itself
            if depth == 1 or (self.deep and depth == 2):
                candidates.add(sub)

        # Exclude root & www itself
        candidates.discard(self.root)
        candidates.discard(f"www.{self.root}")

        if not candidates:
            console.print("  [yellow]No subdomains found.[/yellow]")
            return {"subdomains": [], "selected": []}

        console.print(f"\n  [bold]🔎 Checking {len(candidates)} unique subdomains (alive check)...[/bold]")

        # Active check via HTTP HEAD (concurrent, max 20 at once)
        alive: List[Dict] = []
        sem = asyncio.Semaphore(20)

        async def check(sub: str):
            async with sem:
                for scheme in ("https", "http"):
                    try:
                        async with aiohttp.ClientSession(
                            timeout=aiohttp.ClientTimeout(total=5),
                            connector=aiohttp.TCPConnector(ssl=False)
                        ) as s:
                            async with s.head(f"{scheme}://{sub}", allow_redirects=True) as resp:
                                alive.append({
                                    "subdomain": sub,
                                    "url": f"{scheme}://{sub}",
                                    "status_code": resp.status,
                                    "active": True,
                                    "ip": resp.headers.get("X-Real-IP", ""),
                                })
                                return
                    except Exception:
                        continue
                # Not reachable
                alive.append({"subdomain": sub, "url": "", "status_code": 0, "active": False, "ip": ""})

        await asyncio.gather(*[check(s) for s in candidates])

        active_list = sorted([x for x in alive if x["active"]], key=lambda x: x["subdomain"])
        dead_list   = [x for x in alive if not x["active"]]

        # Print summary table
        if active_list:
            table = Table(title=f"Active Subdomains ({len(active_list)} alive, {len(dead_list)} unreachable)",
                          show_header=True, header_style="bold cyan")
            table.add_column("#", style="dim", width=4)
            table.add_column("Subdomain", style="bold white")
            table.add_column("Status", justify="center", width=8)
            for i, s in enumerate(active_list, 1):
                color = "green" if s["status_code"] < 400 else "yellow"
                table.add_row(str(i), s["subdomain"], f"[{color}]{s['status_code']}[/{color}]")
            console.print(table)
        else:
            console.print("  [yellow]No alive subdomains found.[/yellow]")
            return {"subdomains": alive, "selected": []}

        # Ask user which to include
        console.print("\n[bold]🎯 Subdomain Scan Targets[/bold]")
        console.print("  Enter the subdomain numbers you want to scan (e.g., 1,3,5), 'all' for all of them, or press Enter to skip.")
        choice = Prompt.ask("  Selection", default="skip")

        selected = []
        if choice.strip().lower() == "all":
            selected = active_list
        elif choice.strip().lower() not in ("skip", ""):
            try:
                indices = [int(x.strip()) - 1 for x in choice.split(",")]
                selected = [active_list[i] for i in indices if 0 <= i < len(active_list)]
            except Exception:
                console.print("  [yellow]Invalid input, continuing without additional subdomains.[/yellow]")

        if selected:
            console.print(f"  [green]✅ {len(selected)} subdomain selected for scanning.[/green]")
        else:
            console.print("  [dim]Subdomain skipped, only scanning main domain.[/dim]")

        return {
            "subdomains": active_list + dead_list,
            "selected": selected,
        }


class TechStackFingerprinter:
    """
    Multi-layer tech stack detection:
      Layer 1 - HTTP Response Headers (Server, X-Powered-By, Set-Cookie, etc.)
      Layer 2 - HTML Meta tags (<meta name="generator">, <script src>, <link href>)
      Layer 3 - URL path patterns (/wp-content/, /_next/, etc.)
      Layer 4 - JS global window variables (window.React, window.__NEXT_DATA__, etc.)
    """
    # Header → (category, display_name)
    HEADER_SIGS: Dict[str, List[Tuple[str, str, str]]] = {
        "Server": [
            ("nginx",        "server",  "Nginx"),
            ("apache",       "server",  "Apache"),
            ("microsoft-iis","server",  "IIS"),
            ("litespeed",    "server",  "LiteSpeed"),
            ("cloudflare",   "cdn",     "Cloudflare"),
            ("openresty",    "server",  "OpenResty (nginx)"),
            ("gunicorn",     "server",  "Gunicorn"),
            ("uvicorn",      "server",  "Uvicorn"),
            ("caddy",        "server",  "Caddy"),
        ],
        "X-Powered-By": [
            ("php",          "backend", "PHP"),
            ("asp.net",      "backend", "ASP.NET"),
            ("express",      "backend", "Express.js"),
            ("next.js",      "backend", "Next.js"),
        ],
        "X-Generator":   [("wordpress","cms","WordPress")],
        "X-Drupal-Cache": [("",        "cms","Drupal")],
    }

    COOKIE_SIGS: List[Tuple[str, str, str]] = [
        ("phpsessid",    "backend", "PHP"),
        ("xsrf-token",   "backend", "Laravel"),
        ("laravel_session","backend","Laravel"),
        ("jsessionid",   "backend", "Java / Servlet"),
        ("aspsessionid", "backend", "ASP Classic"),
        ("asp.net_sessionid","backend","ASP.NET"),
        ("_rails",       "backend", "Ruby on Rails"),
        ("rack.session", "backend", "Ruby Rack"),
        ("django",       "backend", "Django"),
        ("connect.sid",  "backend", "Node.js / Express"),
        ("__cfduid",     "cdn",     "Cloudflare"),
        ("_ga",          "analytics","Google Analytics"),
        ("_gid",         "analytics","Google Analytics"),
    ]

    META_SIGS: List[Tuple[str, str, str]] = [
        ("wordpress",    "cms",      "WordPress"),
        ("drupal",       "cms",      "Drupal"),
        ("joomla",       "cms",      "Joomla"),
        ("wix.com",      "cms",      "Wix"),
        ("squarespace",  "cms",      "Squarespace"),
        ("ghost",        "cms",      "Ghost"),
        ("shopify",      "cms",      "Shopify"),
        ("magento",      "cms",      "Magento"),
        ("opencart",     "cms",      "OpenCart"),
    ]

    SCRIPT_SIGS: List[Tuple[str, str, str]] = [
        ("react",        "frontend", "React"),
        ("vue",          "frontend", "Vue.js"),
        ("angular",      "frontend", "Angular"),
        ("jquery",       "frontend", "jQuery"),
        ("bootstrap",    "frontend", "Bootstrap"),
        ("/_next/",      "frontend", "Next.js"),
        ("/nuxt/",       "frontend", "Nuxt.js"),
        ("/vite/",       "frontend", "Vite"),
        ("svelte",       "frontend", "Svelte"),
        ("ember",        "frontend", "Ember.js"),
        ("backbone",     "frontend", "Backbone.js"),
        ("alpine",       "frontend", "Alpine.js"),
        ("htmx",         "frontend", "HTMX"),
        ("stimulus",     "frontend", "Stimulus"),
        ("livewire",     "frontend", "Livewire"),
        ("inertia",      "frontend", "Inertia.js"),
    ]

    PATH_SIGS: List[Tuple[str, str, str]] = [
        ("/wp-content/", "cms",      "WordPress"),
        ("/wp-includes/","cms",      "WordPress"),
        ("/sites/default/","cms",    "Drupal"),
        ("/media/",       "cms",     "Wagtail / Django CMS"),
        ("/_next/",       "frontend","Next.js"),
        ("/static/chunks/","frontend","Next.js / Vite"),
        ("/__nuxt/",      "frontend","Nuxt.js"),
        ("/rails/",       "backend", "Ruby on Rails"),
    ]

    JS_GLOBALS: List[Tuple[str, str, str]] = [
        ("window.React",       "frontend","React"),
        ("window.__REACT",     "frontend","React"),
        ("window.Vue",         "frontend","Vue.js"),
        ("window.angular",     "frontend","Angular"),
        ("window.jQuery",      "frontend","jQuery"),
        ("window.$",           "frontend","jQuery"),
        ("window.__NEXT_DATA__","frontend","Next.js"),
        ("window.Nuxt",        "frontend","Nuxt.js"),
        ("window.Inertia",     "frontend","Inertia.js"),
        ("window.livewire",    "frontend","Livewire"),
        ("window.Stimulus",    "frontend","Stimulus"),
        ("window.htmx",        "frontend","HTMX"),
        ("window.Alpine",      "frontend","Alpine.js"),
        ("window.Shopify",     "cms",     "Shopify"),
        ("window.wixBiSession","cms",     "Wix"),
    ]

    def __init__(self, page, response):
        self.page = page
        self.response = response  # Playwright Response object from page.goto()

    async def detect(self) -> Dict[str, List[str]]:
        console.print("\n[bold cyan]🔬 Tech Stack Fingerprinting...[/bold cyan]")
        stack: Dict[str, Set[str]] = defaultdict(set)

        # Layer 1 — HTTP Headers
        try:
            headers = dict(self.response.headers) if self.response else {}
            for header_name, sigs in self.HEADER_SIGS.items():
                val = headers.get(header_name.lower(), "").lower()
                if val:
                    for pattern, cat, name in sigs:
                        if not pattern or pattern in val:
                            stack[cat].add(name)
                            break
            # Cookie-based detection
            set_cookie = headers.get("set-cookie", "").lower()
            for cookie_key, cat, name in self.COOKIE_SIGS:
                if cookie_key in set_cookie:
                    stack[cat].add(name)
        except Exception:
            pass

        # Layer 2 — HTML Meta & Script tags (via page content)
        try:
            html_content = await self.page.content()
            html_lower = html_content.lower()

            # Meta generator
            for pattern, cat, name in self.META_SIGS:
                if pattern in html_lower and 'generator' in html_lower:
                    # Only if pattern is near "generator"
                    gen_idx = html_lower.find('generator')
                    nearby = html_lower[max(0,gen_idx-10):gen_idx+200]
                    if pattern in nearby:
                        stack[cat].add(name)

            # Script src patterns
            script_matches = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
            link_matches   = re.findall(r'<link[^>]+href=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
            all_assets = " ".join(script_matches + link_matches).lower()
            for pattern, cat, name in self.SCRIPT_SIGS:
                if pattern.lower() in all_assets:
                    stack[cat].add(name)

            # Layer 3 — URL path patterns
            for pattern, cat, name in self.PATH_SIGS:
                if pattern.lower() in html_lower:
                    stack[cat].add(name)
        except Exception:
            pass

        # Layer 4 — JS global window variables
        try:
            js_checks = {sig[0]: (sig[1], sig[2]) for sig in self.JS_GLOBALS}
            js_script = "({" + ", ".join(
                f'"{k}": typeof {k} !== "undefined"'
                for k in js_checks.keys()
            ) + "})"
            results = await asyncio.wait_for(self.page.evaluate(js_script), timeout=5)
            for key, present in results.items():
                if present:
                    cat, name = js_checks[key]
                    stack[cat].add(name)
        except Exception:
            pass

        # Build final dict with sorted lists
        final = {cat: sorted(list(names)) for cat, names in stack.items() if names}

        # Print summary
        if final:
            for cat, techs in final.items():
                icons = {"backend":"⚙️","frontend":"🎨","cms":"📝","server":"🖥️","cdn":"☁️","analytics":"📊"}
                icon = icons.get(cat, "🔧")
                console.print(f"  {icon} [bold]{cat.upper()}[/bold]: {', '.join(techs)}")
        else:
            console.print("  [dim]No tech stack signatures detected.[/dim]")

        return final


class WAFDetector:
    """
    Two-phase WAF/CDN detection:
      Phase A (Passive): Inspect HTTP response headers & cookies for known WAF signatures.
      Phase B (Active):  If Phase A finds nothing, send a single malformed request
                         to a non-existent path and analyse the response body/status.
    """
    # (header_name, value_substring, waf_name, confidence)
    HEADER_SIGS: List[Tuple[str, str, str, str]] = [
        ("server",                   "cloudflare",       "Cloudflare",        "high"),
        ("server",                   "akamaighost",      "Akamai",            "high"),
        ("server",                   "akamai",           "Akamai",            "high"),
        ("x-sucuri-id",              "",                 "Sucuri",            "high"),
        ("x-sucuri-cache",           "",                 "Sucuri",            "high"),
        ("x-cdn",                    "incapsula",        "Imperva Incapsula", "high"),
        ("x-iinfo",                  "",                 "Imperva Incapsula", "high"),
        ("x-fw-hash",                "",                 "Fortinet FortiWeb", "high"),
        ("x-waf-event-info",         "",                 "Radware",           "high"),
        ("x-protected-by",           "sqreen",           "Sqreen",            "high"),
        ("x-protected-by",           "wallarm",          "Wallarm",           "high"),
        ("x-protected-by",           "modsecurity",      "ModSecurity",       "high"),
        ("x-amzn-requestid",         "",                 "AWS (ALB/API GW)",  "medium"),
        ("x-amzn-trace-id",          "",                 "AWS (ALB/API GW)",  "medium"),
        ("x-cache",                  "cloudfront",       "AWS CloudFront",    "high"),
        ("via",                      "cloudfront",       "AWS CloudFront",    "high"),
        ("x-varnish",                "",                 "Varnish Cache",     "medium"),
        ("x-cache",                  "varnish",          "Varnish Cache",     "medium"),
        ("x-kong-upstream-latency",  "",                 "Kong API Gateway",  "medium"),
        ("x-kong-proxy-latency",     "",                 "Kong API Gateway",  "medium"),
        ("cf-ray",                   "",                 "Cloudflare",        "high"),
        ("cf-cache-status",          "",                 "Cloudflare",        "high"),
        ("x-barracuda-connect",      "",                 "Barracuda WAF",     "high"),
        ("x-oneagent-js-injection",  "",                 "Dynatrace",         "low"),
    ]

    # Strings to look for in blocked-page body (active probe)
    BODY_SIGS: List[Tuple[str, str]] = [
        ("cloudflare",           "Cloudflare"),
        ("cf-ray",               "Cloudflare"),
        ("sucuri website firewall","Sucuri"),
        ("incapsula",            "Imperva Incapsula"),
        ("attention required",   "Cloudflare"),
        ("access denied",        "Generic WAF"),
        ("forbidden",            "Generic WAF"),
        ("request rejected",     "Generic WAF"),
        ("your ip",              "Generic WAF/IPS"),
        ("modsecurity",          "ModSecurity"),
        ("akamai",               "Akamai"),
        ("barracuda",            "Barracuda WAF"),
        ("wallarm",              "Wallarm"),
        ("radware",              "Radware"),
    ]

    def __init__(self, base_url: str, response, context):
        self.base_url = base_url
        self.response = response
        self.context = context  # Playwright BrowserContext for active probe

    async def detect(self) -> Dict:
        console.print("\n[bold cyan]🛡️ WAF / CDN Detection...[/bold cyan]")

        # --- Phase A: Passive header inspection ---
        detected = await self._passive_detect()
        if detected:
            console.print(f"  [red]🚨 WAF/CDN Detected (passive): {detected['name']} "
                          f"[dim]({detected['confidence']} confidence)[/dim][/red]")
            console.print(f"  [dim]Evidence: {detected['details']}[/dim]")
            return detected

        console.print("  [dim]Phase A (headers): no signature found → running active probe...[/dim]")

        # --- Phase B: Active behavioral probe ---
        detected = await self._active_probe()
        if detected:
            console.print(f"  [red]🚨 WAF Detected (active probe): {detected['name']} "
                          f"[dim]({detected['confidence']} confidence)[/dim][/red]")
        else:
            console.print("  [green]✅ No WAF/CDN detected (or well-hidden)[/green]")

        return detected or {"detected": False, "name": None, "confidence": None,
                            "method": None, "details": None}

    async def _passive_detect(self) -> Optional[Dict]:
        try:
            headers = dict(self.response.headers) if self.response else {}
        except Exception:
            return None

        for h_name, h_val_sub, waf_name, confidence in self.HEADER_SIGS:
            raw = headers.get(h_name, "").lower()
            if raw and (not h_val_sub or h_val_sub.lower() in raw):
                return {
                    "detected": True,
                    "name": waf_name,
                    "confidence": confidence,
                    "method": "passive-header",
                    "details": f"{h_name}: {headers.get(h_name, '')}",
                }
        return None

    async def _active_probe(self) -> Optional[Dict]:
        """
        Send one request with an obvious XSS payload to a guaranteed-404 path.
        A WAF will block this; we read the block page for WAF identity.
        """
        probe_path = "/lilo-waf-probe-xss"
        probe_param = "?q=%3Cscript%3Ealert%28%27WAF_PROBE%27%29%3C%2Fscript%3E"
        probe_url = f"{self.base_url.rstrip('/')}{probe_path}{probe_param}"
        try:
            resp = await asyncio.wait_for(
                self.context.request.get(probe_url, headers={"User-Agent": "Mozilla/5.0"}),
                timeout=10
            )
            status = resp.status
            body = (await resp.text()).lower()

            # WAF indicator: blocked status codes
            waf_statuses = {403, 406, 412, 429, 503}

            # Scan body for WAF signatures
            for sig, waf_name in self.BODY_SIGS:
                if sig in body:
                    return {
                        "detected": True,
                        "name": waf_name,
                        "confidence": "medium",
                        "method": "active-probe-body",
                        "details": f"Status {status}, body contains '{sig}'",
                    }

            if status in waf_statuses:
                return {
                    "detected": True,
                    "name": "Unknown WAF",
                    "confidence": "low",
                    "method": "active-probe-status",
                    "details": f"Status {status} on probe request (possible WAF block)",
                }
        except asyncio.TimeoutError:
            return {
                "detected": True,
                "name": "Unknown WAF/IPS",
                "confidence": "low",
                "method": "active-probe-timeout",
                "details": "Probe request timed out (possible rate-limit or IPS block)",
            }
        except Exception:
            pass
        return None


# ═══════════════════════════════════════════
# PHASE 2: VULNERABILITY ANALYSIS
# ═══════════════════════════════════════════

class SmartParameterDiscoverer:
    """
    Hidden parameter discovery via response-length delta fuzzing.
    For each target URL, inject candidate parameters one by one and compare
    the response body length against the baseline. A significant delta (>5%)
    signals the parameter is processed by the server.
    """
    # Common hidden / debug parameters to probe
    PARAM_WORDLIST = [
        # Debug / dev
        "debug", "test", "dev", "verbose", "trace", "log", "output",
        # Auth bypass / privilege
        "admin", "role", "is_admin", "superuser", "elevated", "privilege",
        # ID / object traversal
        "id", "user_id", "uid", "account_id", "order_id", "invoice_id",
        "customer_id", "product_id", "item_id", "record_id", "doc_id",
        # Data control
        "page", "limit", "offset", "per_page", "size", "count", "start",
        "sort", "order", "direction", "filter", "search", "q", "query",
        "format", "type", "mode", "view",
        # Hidden toggles
        "show_all", "include_deleted", "with_deleted", "archived",
        "hidden", "internal", "beta", "preview", "draft",
        # API / integrations
        "api_key", "token", "key", "secret", "callback", "redirect",
        "return_url", "next", "ref", "source", "utm_source",
        # Config
        "lang", "locale", "currency", "timezone", "theme",
        "version", "v", "api_version",
    ]

    # Threshold: response length must change by at least this many bytes
    MIN_DELTA_BYTES = 50
    # And by at least this percentage of baseline
    MIN_DELTA_PCT   = 0.03  # 3%

    def __init__(self, context, base_url: str, max_urls: int = 10):
        self.context  = context
        self.base_url = base_url
        self.max_urls = max_urls

    async def _get_body_len(self, url: str, extra_params: Dict = None) -> int:
        """Return response body byte length for the given URL + params."""
        try:
            target = url
            if extra_params:
                sep = "&" if "?" in url else "?"
                qs  = "&".join(f"{k}={v}" for k, v in extra_params.items())
                target = f"{url}{sep}{qs}"
            resp = await asyncio.wait_for(
                self.context.request.get(target, timeout=8000),
                timeout=9
            )
            body = await resp.body()
            return len(body)
        except Exception:
            return -1

    async def discover(self, urls: List[str]) -> List[Dict]:
        """
        Run parameter fuzzing on up to self.max_urls discovered pages.
        Returns list of findings: {url, parameter, baseline_len, found_len, delta_pct}
        """
        targets = [u for u in urls if u.startswith("http")][:self.max_urls]
        if not targets:
            return []

        findings: List[Dict] = []
        console.print(f"\n[bold cyan]🔎 Smart Parameter Discovery ({len(targets)} URLs × {len(self.PARAM_WORDLIST)} params)[/bold cyan]")

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                      BarColumn(), TextColumn("{task.completed}/{task.total}"),
                      TimeElapsedColumn(), console=console) as progress:
            task = progress.add_task("[cyan]Fuzzing params...", total=len(targets))

            for url in targets:
                baseline = await self._get_body_len(url)
                if baseline < 0:
                    progress.advance(task)
                    continue

                # Fire all param probes concurrently (batch of 10 at a time)
                sem = asyncio.Semaphore(10)
                url_findings: List[Dict] = []

                async def probe(param: str):
                    async with sem:
                        test_val = f"LILOPROBE{int(time.time() * 1000) % 99999}"
                        length = await self._get_body_len(url, {param: test_val})
                        if length < 0:
                            return
                        delta = abs(length - baseline)
                        if baseline > 0:
                            pct = delta / baseline
                        else:
                            pct = 0
                        if delta >= self.MIN_DELTA_BYTES and pct >= self.MIN_DELTA_PCT:
                            url_findings.append({
                                "url":          url,
                                "parameter":    param,
                                "baseline_len": baseline,
                                "found_len":    length,
                                "delta_bytes":  delta,
                                "delta_pct":    round(pct * 100, 1),
                                "test_value":   test_val,
                            })

                await asyncio.gather(*[probe(p) for p in self.PARAM_WORDLIST])

                if url_findings:
                    findings.extend(url_findings)
                    for f in url_findings:
                        console.print(
                            f"  [green]✅ Hidden param:[/green] [bold]{f['parameter']}[/bold] "
                            f"on {truncate(f['url'], 60)} "
                            f"[dim](Δ {f['delta_bytes']}B / {f['delta_pct']}%)[/dim]"
                        )
                progress.advance(task)

        if not findings:
            console.print("  [dim]No hidden parameters found.[/dim]")
        else:
            console.print(f"  [bold green]Total: {len(findings)} hidden parameter(s) discovered.[/bold green]")

        return findings


class ContextAwarePayloadSelector:
    """
    Inject LILO_MARKER into each form field / URL param, then parse the resulting
    HTML to determine the *context* where the marker landed. Based on the context,
    select the most effective XSS payload.

    Contexts and payloads:
      - html_text         → <script>window.__LILO_XSS__=1</script>
      - html_attribute    → " onmouseover=window.__LILO_XSS__=1 x="
      - href_attribute    → javascript:window.__LILO_XSS__=1
      - script_string     → ";window.__LILO_XSS__=1;//
      - script_var        → \x00;window.__LILO_XSS__=1;//
      - js_template_lit   → `${window.__LILO_XSS__=1}`
      - css_context       → </style><script>window.__LILO_XSS__=1</script>
      - unknown           → <img src=x onerror=window.__LILO_XSS__=1>
    """
    MARKER = "LILOCTXMARK9"

    PAYLOADS = {
        "html_text":      "<script>window.__LILO_XSS__=1</script>",
        "html_attribute": "\" onmouseover=\"window.__LILO_XSS__=1\" x=\"",
        "href_attribute": "javascript:window.__LILO_XSS__=1",
        "script_string":  '";window.__LILO_XSS__=1;//',
        "script_var":     "\\x00;window.__LILO_XSS__=1;//",
        "js_template_lit":"${window.__LILO_XSS__=1}",
        "css_context":    "</style><script>window.__LILO_XSS__=1</script>",
        "unknown":        "<img src=x onerror=window.__LILO_XSS__=1>",
    }

    def __init__(self, page, context, base_url: str, error_tracker):
        self.page         = page
        self.context      = context
        self.base_url     = base_url
        self.error_tracker = error_tracker

    def _detect_context(self, html: str) -> str:
        """Parse HTML source to find where MARKER appears and classify context."""
        marker = self.MARKER
        idx = html.find(marker)
        if idx < 0:
            return "unknown"

        # Grab surrounding context (up to 300 chars before marker)
        before = html[max(0, idx - 300):idx]
        after  = html[idx:min(len(html), idx + 300)]

        # Inside <script> block
        if re.search(r'<script[^>]*>', before, re.IGNORECASE):
            # Check if we're inside a string literal
            if re.search(r'["\']' + r'[^"\']*$', before):
                return "script_string"
            if re.search(r'`[^`]*$', before):
                return "js_template_lit"
            return "script_var"

        # Inside <style> block
        if re.search(r'<style[^>]*>', before, re.IGNORECASE):
            return "css_context"

        # Inside an attribute
        # Find the last unclosed tag before marker
        last_tag = re.findall(r'<[a-zA-Z][^>]*$', before)
        if last_tag:
            tag_text = last_tag[-1]
            # href / src / action attribute
            if re.search(r'href\s*=\s*["\']?[^"\']*$', tag_text, re.IGNORECASE) or \
               re.search(r'action\s*=\s*["\']?[^"\']*$', tag_text, re.IGNORECASE):
                return "href_attribute"
            return "html_attribute"

        return "html_text"

    async def _inject_and_detect(self, url: str) -> Optional[Dict]:
        """
        For a given URL with query params, replace each value with MARKER,
        load the page, and detect context.
        Returns the best finding dict or None.
        """
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if not params:
            return None

        findings = []
        for param_name in params:
            try:
                test_url = url.replace(
                    f"{param_name}={params[param_name][0]}",
                    f"{param_name}={self.MARKER}"
                )
                resp = await asyncio.wait_for(
                    self.context.request.get(test_url, timeout=8000),
                    timeout=9
                )
                html = await resp.text()
                context = self._detect_context(html)
                payload  = self.PAYLOADS.get(context, self.PAYLOADS["unknown"])
                findings.append({
                    "url":         url,
                    "parameter":   param_name,
                    "context":     context,
                    "payload":     payload,
                    "description": f"Marker landed in [{context}] context. Suggested payload selected.",
                })
            except Exception:
                continue

        return findings if findings else None

    async def analyze(self, urls: List[str], param_findings: List[Dict]) -> List[Dict]:
        """
        Analyze:
        1. URLs that already have query parameters (from crawler)
        2. URLs where hidden params were found (from SmartParameterDiscoverer)
        Returns list of context-annotated XSS findings.
        """
        # Build set of URLs to test
        targets: Set[str] = set()
        for url in urls:
            if "?" in url:
                targets.add(url)
        # Also construct URLs from param findings
        for pf in param_findings:
            sep = "&" if "?" in pf["url"] else "?"
            targets.add(f"{pf['url']}{sep}{pf['parameter']}=VALUE")

        targets = list(targets)[:15]  # cap at 15 URLs
        if not targets:
            return []

        console.print(f"\n[bold cyan]🎯 Context-Aware Payload Selection ({len(targets)} URLs)[/bold cyan]")
        all_findings: List[Dict] = []

        for url in targets:
            result = await self._inject_and_detect(url)
            if result:
                all_findings.extend(result)
                for r in result:
                    ctx_color = {
                        "script_string": "red", "href_attribute": "red",
                        "html_attribute": "yellow", "html_text": "yellow",
                    }.get(r["context"], "cyan")
                    console.print(
                        f"  [{ctx_color}]🎯 [{r['context']}][/{ctx_color}] "
                        f"param=[bold]{r['parameter']}[/bold] on {truncate(r['url'], 50)}"
                    )
                    console.print(f"  [dim]  → Payload: {r['payload'][:80]}[/dim]")

        if not all_findings:
            console.print("  [dim]No injectable parameters with detectable context found.[/dim]")
        else:
            console.print(f"  [bold green]Total: {len(all_findings)} context-mapped injection point(s).[/bold green]")

        return all_findings


class LocalStorageJWTAnalyzer:
    """
    Extracts localStorage and sessionStorage data via Playwright page.evaluate().
    Scans for:
    1. JWT tokens (ey... strings) → decode header+payload, check alg:none
    2. Sensitive plaintext data (PINs, email, passwords, tokens)
    3. Insecure storage of PII / credentials
    """
    # Regex patterns for sensitive data keys
    SENSITIVE_KEY_PATTERNS = [
        (re.compile(r'pass(word)?', re.I),   "Password"),
        (re.compile(r'pin\b', re.I),          "PIN"),
        (re.compile(r'secret', re.I),         "Secret"),
        (re.compile(r'token', re.I),           "Token"),
        (re.compile(r'api[_-]?key', re.I),    "API Key"),
        (re.compile(r'credit|card', re.I),    "Credit Card"),
        (re.compile(r'ssn|social.security', re.I), "SSN"),
        (re.compile(r'private.?key', re.I),   "Private Key"),
    ]

    # Regex to detect JWT format
    JWT_RE = re.compile(r'^ey[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*$')

    def __init__(self, page):
        self.page = page

    def _decode_jwt(self, token: str) -> Optional[Dict]:
        """Decode a JWT token without verification. Returns {header, payload} dicts."""
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None
            def _b64decode(s: str) -> str:
                # Add padding
                s += "=" * (4 - len(s) % 4)
                return base64.urlsafe_b64decode(s).decode("utf-8", errors="replace")
            header  = json.loads(_b64decode(parts[0]))
            payload = json.loads(_b64decode(parts[1]))
            return {"header": header, "payload": payload, "signature": parts[2]}
        except Exception:
            return None

    def _check_jwt_issues(self, decoded: Dict) -> List[str]:
        """Return list of security issues found in a decoded JWT."""
        issues = []
        header  = decoded.get("header", {})
        payload = decoded.get("payload", {})

        # Algorithm checks
        alg = header.get("alg", "")
        if str(alg).lower() in ("none", "", "null"):
            issues.append("🚨 CRITICAL: Algorithm is 'none' — signature not verified!")
        if str(alg).upper() in ("HS256", "HS384", "HS512"):
            issues.append("⚠️ Symmetric HMAC — secret key brute-forceable if weak")

        # Expiry check
        exp = payload.get("exp")
        if not exp:
            issues.append("⚠️ No expiry (exp) claim — token never expires!")
        elif exp < time.time():
            issues.append("⚠️ Token is EXPIRED but still stored")

        # Sensitive data in payload
        sensitive_keys = ["password", "pin", "secret", "credit_card", "ssn", "private_key"]
        for k in sensitive_keys:
            if k in str(payload).lower():
                issues.append(f"🚨 Sensitive field '{k}' found plaintext in JWT payload!")

        return issues

    def _check_storage_value(self, key: str, value: str) -> Optional[Dict]:
        """Check a storage key/value pair for sensitive data."""
        # Check if it's a JWT
        if self.JWT_RE.match(str(value)):
            decoded = self._decode_jwt(str(value))
            if decoded:
                issues = self._check_jwt_issues(decoded)
                return {
                    "type":    "JWT",
                    "key":     key,
                    "issues":  issues,
                    "alg":     decoded["header"].get("alg", "?"),
                    "subject": decoded["payload"].get("sub", decoded["payload"].get("user", "?")),
                    "exp":     decoded["payload"].get("exp"),
                    "preview": str(decoded["payload"])[:200],
                }

        # Check if key name suggests sensitive data
        for pattern, label in self.SENSITIVE_KEY_PATTERNS:
            if pattern.search(str(key)):
                return {
                    "type":    "Sensitive Storage",
                    "key":     key,
                    "label":   label,
                    "issues":  [f"⚠️ {label} stored in browser storage (key: '{key}')"],
                    "preview": str(value)[:100],
                }
        return None

    async def analyze(self, urls: List[str]) -> List[Dict]:
        """
        Navigate to up to 5 URLs and extract localStorage + sessionStorage.
        Returns list of findings.
        """
        targets = list({u for u in urls if u.startswith("http")})[:5]
        findings: List[Dict] = []

        console.print(f"\n[bold cyan]🔐 Local Storage & JWT Analysis ({len(targets)} pages)[/bold cyan]")

        for url in targets:
            try:
                # Use current page (already logged in)
                await asyncio.wait_for(
                    self.page.goto(url, wait_until="domcontentloaded", timeout=15000),
                    timeout=16
                )
                await self.page.wait_for_timeout(500)

                storage_data = await asyncio.wait_for(
                    self.page.evaluate("""() => {
                        const dump = (store) => {
                            const result = {};
                            for (let i = 0; i < store.length; i++) {
                                const k = store.key(i);
                                result[k] = store.getItem(k);
                            }
                            return result;
                        };
                        return {
                            localStorage:   dump(localStorage),
                            sessionStorage: dump(sessionStorage),
                        };
                    }"""),
                    timeout=5
                )

                for store_name, store_data in storage_data.items():
                    for key, value in store_data.items():
                        finding = self._check_storage_value(key, str(value))
                        if finding:
                            finding["storage"] = store_name
                            finding["page_url"] = url
                            findings.append(finding)

                            if finding["type"] == "JWT":
                                sev_color = "red" if any("CRITICAL" in i for i in finding["issues"]) else "yellow"
                                console.print(
                                    f"  [{sev_color}]🔑 JWT in {store_name}[/{sev_color}]: "
                                    f"key=[bold]{finding['key']}[/bold] | "
                                    f"alg={finding['alg']} | sub={finding['subject']}"
                                )
                                for issue in finding["issues"]:
                                    console.print(f"    {issue}")
                            else:
                                console.print(
                                    f"  [yellow]⚠️ {finding['label']} in {store_name}[/yellow]: "
                                    f"key=[bold]{finding['key']}[/bold]"
                                )
            except Exception as e:
                console.print(f"  [dim]Skipped {truncate(url, 50)}: {truncate(e, 60)}[/dim]")
                continue

        if not findings:
            console.print("  [green]✅ No sensitive data or insecure JWTs found in browser storage.[/green]")
        else:
            console.print(f"  [bold {'red' if any(f['type']=='JWT' for f in findings) else 'yellow'}]"
                          f"Total: {len(findings)} storage issue(s) found.[/]")

        return findings


class OOBClient:

    def __init__(self, server_url: Optional[str] = None):
        self.server_url = server_url  # None = use library defaults (oast.pro etc)
        self.client = None
        self.subdomain = None
        self._active = False
        self._local_server = None
        self._local_runner = None
        self._local_interactions = []
        self._local_port = 8080

    async def _start_local_server(self):
        try:
            from aiohttp import web
            async def handle_req(request):
                self._local_interactions.append({
                    "protocol": "http",
                    "unique-id": request.match_info.get("id", "unknown"),
                    "full-id": request.url.path,
                    "raw-request": f"{request.method} {request.url.path}",
                    "remote-address": request.remote,
                    "timestamp": datetime.now().isoformat()
                })
                return web.Response(text="OK")

            app = web.Application()
            app.router.add_route('*', '/{id:.*}', handle_req)
            self._local_runner = web.AppRunner(app)
            await self._local_runner.setup()
            
            # Find open port
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('127.0.0.1', 0))
            self._local_port = sock.getsockname()[1]
            sock.close()
            
            site = web.TCPSite(self._local_runner, '127.0.0.1', self._local_port)
            await site.start()
            self.subdomain = f"127.0.0.1:{self._local_port}"
            self._active = True
            console.print(f"[green]✅ OOB (Local Fallback) aktif: http://{self.subdomain}[/green]")
            return True
        except Exception as e:
            console.print(f"[red]❌ Local OOB fallback failed: {e}[/red]")
            return False

    async def start(self):
        if not HAS_INTERACTSH:
            console.print("[yellow]⚠️ Interactsh library not installed, attempting local fallback...[/yellow]")
            return await self._start_local_server()
        try:
            from interactsh import Options
            opts = Options(server_url=self.server_url) if self.server_url else Options()
            self.client = InteractshClient(options=opts)
            await self.client.initialize()
            self.subdomain = self.client.domain  # property: returns current interactsh domain
            self._active = True
            console.print(f"[green]✅ OOB/Interactsh active: {self.subdomain}[/green]")
            return True
        except Exception as e:
            console.print(f"[yellow]⚠️ OOB start failed: {e}, attempting local fallback...[/yellow]")
            return await self._start_local_server()

    async def get_payload_url(self, path: str = "") -> str:
        if self.client:
            try:
                return await self.client.url()
            except Exception: pass
        if self._local_runner:
            # Generate a unique ID for local tracking
            uid = os.urandom(4).hex()
            return f"http://{self.subdomain}/{path}_{uid}"
        return f"http://{self.subdomain}/{path}" if self.subdomain else ""

    async def poll(self) -> List[Dict]:
        if self.client:
            try:
                interactions = await self.client.poll_once()
                return [i.model_dump() if hasattr(i, 'model_dump') else dict(vars(i)) for i in (interactions or [])]
            except Exception: return []
        if self._local_runner:
            new_interactions = list(self._local_interactions)
            self._local_interactions.clear()
            return new_interactions
        return []

    async def close(self):
        if self.client:
            try:
                await self.client.close()
            except Exception: pass
        if self._local_runner:
            try:
                await self._local_runner.cleanup()
            except Exception: pass

class SmartFuzzer:
    def __init__(self, page: Page, context: BrowserContext, base_url: str):
        self.page = page
        self.context = context
        self.base_url = base_url

    async def test_xss_smart(self, param_name: str) -> List['SecurityFinding']:
        findings = []
        current_url = self.page.url
        parsed = urlparse(current_url)
        if param_name not in parse_qs(parsed.query):
            return findings
        probe = f"LILOCTX{int(time.time())}"
        orig_val = parse_qs(parsed.query)[param_name][0]
        test_url = current_url.replace(f"{param_name}={orig_val}", f"{param_name}={urllib.parse.quote(probe)}")
        try:
            resp = await self.context.request.get(test_url, timeout=10000)
            body = await resp.text()
            ctx = ContextAnalyzer.detect_context(body, probe)
            if ctx == "not_reflected":
                return findings
            payload_map = {
                "html_attribute": ['" onmouseover=alert(1)//', "'><img src=x onerror=alert(1)>"],
                "script_string": ['\"; alert(1);//', "'; alert(1);//"],
                "html_body": ["<svg onload=alert(1)>", "<img src=x onerror=alert(1)>"],
                "html_comment": ["--><script>alert(1)</script><!--"],
            }
            payloads = payload_map.get(ctx, ["<script>alert(1)</script>"])
            for p in payloads:
                test_url_payload = current_url.replace(f"{param_name}={orig_val}", f"{param_name}={urllib.parse.quote(p)}")
                resp2 = await self.context.request.get(test_url_payload, timeout=10000)
                body2 = await resp2.text()
                if p in body2:
                    findings.append(SecurityFinding("XSS","high",f"Context-aware XSS in {param_name} ({ctx})","Payload reflected",location=test_url_payload,evidence=p))
                    break
        except Exception: pass
        return findings

class SecurityFinding:
    CVSS_MAP = {
        "SQL Injection": {"score": 9.8, "severity": "critical"},
        "Blind SQL Injection": {"score": 9.8, "severity": "critical"},
        "Command Injection": {"score": 9.8, "severity": "critical"},
        "Blind OOB Injection": {"score": 9.8, "severity": "critical"},
        "Blind OOB": {"score": 9.8, "severity": "critical"},
        "IDOR": {"score": 8.5, "severity": "high"},
        "XSS": {"score": 6.1, "severity": "medium"},
        "CSRF": {"score": 6.5, "severity": "medium"},
        "Sensitive File Exposure": {"score": 7.5, "severity": "high"},
        "Directory Listing": {"score": 5.3, "severity": "medium"},
        "Information Disclosure": {"score": 5.3, "severity": "medium"},
        "CORS": {"score": 5.4, "severity": "medium"},
        "Clickjacking": {"score": 4.3, "severity": "low"},
        "Form Security": {"score": 4.3, "severity": "low"},
        "Cookie Security": {"score": 4.3, "severity": "low"},
        "SSL/TLS": {"score": 3.1, "severity": "low"},
        "Security Headers": {"score": 0.0, "severity": "info"}
    }

    def __init__(self, category, severity, title, description, location="", evidence="", recommendation="", screenshot="", poc=""):
        self.category = category
        self.title = title
        self.description = description
        self.location = location
        self.evidence = evidence
        self.recommendation = recommendation
        self.screenshot = screenshot
        self.poc = poc
        self.timestamp = datetime.now().isoformat()
        self.id = hashlib.md5(f"{category}{title}{location}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        # Auto-calculate CVSS and severity if category matches
        mapping = self.CVSS_MAP.get(self.category)
        if mapping:
            self.cvss_score = mapping["score"]
            self.severity = mapping["severity"]  # Override with standardized severity
        else:
            self.cvss_score = 0.0
            self.severity = severity

    def to_dict(self):
        return {
            "id": self.id, "category": self.category, "severity": self.severity,
            "cvss_score": self.cvss_score, "poc": self.poc,
            "title": self.title, "description": self.description,
            "location": self.location, "evidence": str(self.evidence)[:500] if self.evidence else "",
            "recommendation": self.recommendation, "screenshot": self.screenshot,
            "timestamp": self.timestamp,
        }

class IDOREngine:
    def __init__(self, context_a: BrowserContext, context_b: BrowserContext, base_url: str):
        self.context_a = context_a
        self.context_b = context_b
        self.base_url = base_url
        self.findings: List[SecurityFinding] = []

    async def run(self, pages_b: List[str]) -> List[SecurityFinding]:
        console.print("[bold magenta]🔀 Running IDOR tests...[/bold magenta]")
        
        # Extract JWT from User A's storage via Regex
        page_a_temp = await self.context_a.new_page()
        await page_a_temp.goto(self.base_url, wait_until="domcontentloaded", timeout=15000)
        jwt_token = await page_a_temp.evaluate(r"""() => {
            const jwtRegex = /^ey[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*$/;
            for (let i = 0; i < localStorage.length; i++) {
                const val = localStorage.getItem(localStorage.key(i));
                if (val && jwtRegex.test(val)) return val;
            }
            for (let i = 0; i < sessionStorage.length; i++) {
                const val = sessionStorage.getItem(sessionStorage.key(i));
                if (val && jwtRegex.test(val)) return val;
            }
            return null;
        }""")
        await page_a_temp.close()

        if jwt_token:
            console.print(f"[cyan]🔑 IDOR Engine: JWT Token detected and will be injected![/cyan]")

        for url in pages_b:
            try:
                page_a = await self.context_a.new_page()
                
                # Intercept request and inject JWT Header if available
                async def intercept_and_inject(route, request):
                    headers = request.headers
                    if jwt_token:
                        headers["Authorization"] = f"Bearer {jwt_token}"
                        headers["X-Access-Token"] = jwt_token
                    await route.continue_(headers=headers)

                await page_a.route("**/*", intercept_and_inject)

                resp = await page_a.goto(url, wait_until="domcontentloaded", timeout=15000)
                status = resp.status if resp else 0
                if status == 200:
                    body = await page_a.content()
                    if any(kw in body.lower() for kw in ["profile", "dashboard", "admin"]):
                        poc = f"curl -X GET \"{url}\" -H \"Cookie: <USER_A_SESSION>\""
                        if jwt_token: poc += f" -H \"Authorization: Bearer {jwt_token[:10]}...\""
                        self.findings.append(SecurityFinding("IDOR","high",f"Potential IDOR: {url}","User A accessed User B resource",location=url,evidence=f"HTTP {status}", poc=poc))
                await page_a.close()
            except Exception: continue
        return self.findings

# ═══════════════════════════════════════════
# ENHANCED SECURITY SCANNER (gabungan v4.5.0 + v5.0.0)
# ═══════════════════════════════════════════

class SecurityScanner:
    def __init__(self, page, context, base_url, error_tracker, screenshot_manager, oob_client=None, aiohttp_session=None, xss_wordlist=None, sqli_wordlist=None, rate_limit=0, proxy=None):
        self.aiohttp_session = aiohttp_session
        self.xss_wordlist = xss_wordlist
        self.sqli_wordlist = sqli_wordlist
        self.rate_limit = rate_limit
        self.proxy = proxy
        self.semaphore = asyncio.Semaphore(rate_limit) if rate_limit > 0 else None
        self.page = page
        self.context = context
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.error_tracker = error_tracker
        self.screenshot_manager = screenshot_manager
        self.oob = oob_client
        self.findings: List[SecurityFinding] = []
        self.smart_fuzzer = SmartFuzzer(page, context, base_url)

    def add_finding(self, *args, **kwargs):
        f = SecurityFinding(*args, **kwargs)
        self.findings.append(f)
        return f

    async def _capture_if_important(self, finding):
        if finding.severity in ["critical", "high"]:
            try:
                screenshot = await self.screenshot_manager.capture_security_screenshot(
                    self.page, f"{finding.category}_{finding.id}", finding.location)
                if screenshot: finding.screenshot = screenshot
            except Exception: pass

    async def run_all_tests(self):
        console.print("\n[bold red]🛡️ DEEP SECURITY AUDIT[/bold red]")
        tests = [
            ("Security Headers", self.test_security_headers),
            ("XSS (Smart)", self.test_xss_smart),
            ("XSS Execution", self.test_xss_execution),
            ("SQL Injection Points", self.test_sqli_points),
            ("CSRF Protection", self.test_csrf),
            ("Sensitive Files", self.test_sensitive_files),
            ("Cookie Security", self.test_cookie_security),
            ("Information Disclosure", self.test_info_disclosure),
            ("CORS Configuration", self.test_cors),
            ("Clickjacking", self.test_clickjacking),
            ("Form Security", self.test_form_security),
            ("SSL/TLS Check", self.test_ssl),
            ("Directory Listing", self.test_directory_listing),
        ]
        if self.oob and self.oob.subdomain:
            tests.append(("Blind OOB Injection", self.test_blind_oob))
        
        # Mass Assignment Tester (Module 3)
        if getattr(self, "enable_mass_assign", False):
            tests.append(("Mass Assignment / Business Logic", self.test_mass_assignment))

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), console=console) as progress:
            task = progress.add_task("[red]Running security tests...", total=len(tests))
            for name, func in tests:
                progress.update(task, description=f"[red]{name}[/red]")
                try: await func()
                except Exception as e: self.add_finding("Scanner Error", "info", f"{name} failed", str(e))
                progress.advance(task)
        return self.findings

    async def test_security_headers(self):
        try:
            response = await self.context.request.get(self.base_url, timeout=15000)
            headers = {k.lower(): v for k, v in response.headers.items()}
            for header_name, config in SECURITY_HEADERS.items():
                header_lower = header_name.lower()
                if header_lower not in headers:
                    finding = self.add_finding("Security Headers", config["severity"], f"Missing: {header_name}", config["description"], location=self.base_url, recommendation=f"Add: {header_name}: {config['recommendation']}")
                    await self._capture_if_important(finding)
                elif header_name == "Access-Control-Allow-Origin":
                    if headers[header_lower] == "*":
                        finding = self.add_finding("CORS", "high", "Wildcard CORS Policy", "Access-Control-Allow-Origin is set to '*'", location=self.base_url, evidence=f"Header: {headers[header_lower]}", recommendation="Restrict to specific origins")
                        await self._capture_if_important(finding)
        except Exception as e:
            self.add_finding("Security Headers", "info", "Could not check headers", str(e))

    async def test_xss_smart(self):
        current_url = self.page.url
        parsed = urlparse(current_url)
        if parsed.query:
            
            # DOM Taint Analysis Hook
            await self.page.add_init_script("""
                window.__LILO_TAINT_LOG__ = [];
                const originalEval = window.eval;
                window.eval = function(args) {
                    if(typeof args === 'string' && args.includes('LILO_TAINT')) window.__LILO_TAINT_LOG__.push({sink: 'eval', payload: args});
                    return originalEval(args);
                };
                const originalSetTimeout = window.setTimeout;
                window.setTimeout = function(fn, time) {
                    if(typeof fn === 'string' && fn.includes('LILO_TAINT')) window.__LILO_TAINT_LOG__.push({sink: 'setTimeout', payload: fn});
                    return originalSetTimeout(fn, time);
                };
            """)
            
            for param in parse_qs(parsed.query):
                # Run standard smart fuzzer
                findings = await self.smart_fuzzer.test_xss_smart(param)
                for f in findings:
                    self.findings.append(f)
                    await self._capture_if_important(f)
                
                # Check for DOM Taint Analysis results
                try:
                    taint_logs = await self.page.evaluate("() => window.__LILO_TAINT_LOG__")
                    for log in taint_logs:
                        finding = self.add_finding("DOM-Based XSS", "critical", f"Taint flowed into sink: {log['sink']}", f"Input reached execution sink.", location=current_url, evidence=f"Payload: {log['payload'][:50]}", recommendation="Sanitize user input before passing to DOM sinks.")
                        await self._capture_if_important(finding)
                except Exception: pass

    async def _fetch_with_rate_limit(self, url):
        if self.semaphore:
            async with self.semaphore:
                async with self.aiohttp_session.get(url, proxy=self.proxy) as resp:
                    return await resp.text()
        else:
            async with self.aiohttp_session.get(url, proxy=self.proxy) as resp:
                return await resp.text()

    async def test_xss_execution(self):
        current_url = self.page.url
        parsed = urlparse(current_url)
        if not parsed.query: return
        
        params = parse_qs(parsed.query)
        
        # Generator agar file dibaca baris per baris tanpa menyedot RAM
        async def get_payload_stream():
            if self.xss_wordlist:
                async for p in load_payloads(self.xss_wordlist):
                    yield p
            else:
                for p in XSS_PAYLOADS:
                    yield p
                    
        for param_name in list(params.keys()):
            orig_val = params[param_name][0]
            
            async for payload in get_payload_stream():
                try:
                    test_url = current_url.replace(f"{param_name}={orig_val}", f"{param_name}={urllib.parse.quote(payload)}")
                    body = await self._fetch_with_rate_limit(test_url)
                    if payload in body:
                        temp_page = await self.context.new_page()
                        try:
                            await asyncio.wait_for(temp_page.goto(test_url, wait_until="domcontentloaded", timeout=5000), timeout=6)
                            is_executed = await temp_page.evaluate("() => window.__LILO_XSS__ === true")
                            if is_executed:
                                poc = f"curl -X GET \"{test_url}\""
                                finding = self.add_finding("XSS", "high", f"Reflected XSS Executed in: {param_name}", "Payload executed in browser.", location=test_url, evidence=f"Payload: {payload}", recommendation="Sanitize output.", poc=poc)
                                await self._capture_if_important(finding)
                                break  # <--- INI PENTING! Agar tidak spam finding di parameter yang sama
                        finally:
                            try: await temp_page.close()
                            except Exception: pass
                except Exception: continue

    async def test_sqli_points(self):
        current_url = self.page.url
        parsed = urlparse(current_url)
        if not parsed.query: return
        params = parse_qs(parsed.query)
        
        baseline_time = 0.5
        try:
            b_start = time.time()
            await self._fetch_with_rate_limit(current_url)
            baseline_time = max(0.5, time.time() - b_start)
        except Exception: pass
        
        # Generator stream untuk SQLi payloads
        async def get_payload_stream():
            if self.sqli_wordlist:
                async for p in load_payloads(self.sqli_wordlist):
                    yield p
            else:
                for p in SQLI_TEST_STRINGS:
                    yield p

        for param_name, values in params.items():
            async for test_str in get_payload_stream():
                try:
                    test_url = current_url.replace(f"{param_name}={values[0]}", f"{param_name}={urllib.parse.quote(test_str)}")
                    start = time.time()
                    body = await self._fetch_with_rate_limit(test_url)
                    response_time = time.time() - start
                    
                    if any(x in test_str.upper() for x in ["SLEEP","DELAY","PG_SLEEP"]):
                        if response_time > (baseline_time + 4.5):
                            poc = f"curl -X GET \"{test_url}\" -v"
                            finding = self.add_finding("Blind SQL Injection", "critical", f"Time-Based SQLi in parameter: {param_name}", f"Delay: {response_time:.2f}s (Baseline: {baseline_time:.2f}s).", location=test_url, evidence=f"Payload: {test_str}", recommendation="Use parameterized queries.", poc=poc)
                            await self._capture_if_important(finding)
                            break
                            
                    sql_errors = ["SQL syntax","mysql_fetch","ORA-","PostgreSQL","SQLite","Microsoft SQL","ODBC Driver","SQLSTATE","Database error","Unclosed quotation"]
                    for err_pat in sql_errors:
                        if err_pat.lower() in body.lower():
                            poc = f"curl -X GET \"{test_url}\" -v"
                            finding = self.add_finding("SQL Injection", "critical", f"Error-Based SQLi in parameter: {param_name}", f"Error: {err_pat}", location=test_url, evidence=err_pat, recommendation="Disable detailed errors, use prepared statements.", poc=poc)
                            await self._capture_if_important(finding)
                            break
                except Exception: continue

    async def test_csrf(self):
        forms = await self.page.query_selector_all("form")
        for form in forms:
            try:
                method = (await form.get_attribute("method") or "GET").upper()
                if method in ["POST","PUT","PATCH","DELETE"]:
                    csrf_inputs = await form.query_selector_all('input[name*="csrf" i], input[name*="token" i], input[name="_token"], input[name="authenticity_token"]')
                    csrf_meta = await self.page.query_selector('meta[name="csrf-token"], meta[name="csrf-param"]')
                    if not csrf_inputs and not csrf_meta:
                        action = await form.get_attribute("action") or self.page.url
                        finding = self.add_finding("CSRF", "high", "Missing CSRF Protection", "State-changing form without CSRF token.", location=action[:100], recommendation="Add anti-CSRF tokens or SameSite=Strict.")
                        await self._capture_if_important(finding)
            except Exception: continue

    async def test_sensitive_files(self):
        base = self.base_url.rstrip("/")
        baseline_url = f"{base}/file-ngasal-yang-pasti-gaada-{int(time.time())}.txt"
        baseline_body = ""
        try:
            base_resp = await self.context.request.get(baseline_url, timeout=5000)
            baseline_body = await base_resp.text()
        except Exception: pass
        for file_path in track(SENSITIVE_FILES, description="[yellow]Scanning endpoints & files[/yellow]", console=console):
            try:
                test_url = f"{base}/{file_path}"
                resp = await self.context.request.get(test_url, timeout=5000)
                if resp.status in [200, 403]:
                    content_type = resp.headers.get("content-type","").lower()
                    body = await resp.text() if resp.status == 200 else ""
                    
                    is_api_or_dir = "/" in file_path or "api" in file_path or "graphql" in file_path
                    is_html_expected = file_path.endswith((".html",".txt",".json",".xml"))
                    
                    if "text/html" in content_type and not is_html_expected and not is_api_or_dir:
                        continue
                        
                    if len(body) > 0 and len(baseline_body) > 0:
                        similarity = difflib.SequenceMatcher(None, body, baseline_body).ratio()
                        if similarity > 0.8: continue
                        
                    if any(kw in body.lower() for kw in ["not found","404","page not found","oops"]):
                        continue
                        
                    severity = "high"
                    title = "Sensitive File Exposure"
                    if is_api_or_dir:
                        title = "Directory/Endpoint Discovered"
                        severity = "medium" if resp.status == 403 else "high"
                    elif file_path in ["robots.txt","sitemap.xml","readme.html"]: 
                        severity = "low"
                    elif file_path.startswith(".") or "config" in file_path or "backup" in file_path: 
                        severity = "critical"
                        
                    finding = self.add_finding(title, severity, f"Exposed: {file_path}", f"HTTP {resp.status} accessible and passed soft-404 filter.", location=test_url, evidence=f"Content-Type: {content_type}", recommendation="Restrict access via server config.")
                    await self._capture_if_important(finding)
            except Exception: continue

    async def test_cookie_security(self):
        cookies = await self.context.cookies()
        is_https = self.page.url.startswith("https://")
        for c in cookies:
            if is_https and not c.get("secure",False):
                self.add_finding("Cookie Security","medium",f"Cookie missing Secure: {c['name']}","Transmitted over unencrypted connection",location=self.page.url,recommendation="Set Secure flag")
            if not c.get("httpOnly",False):
                self.add_finding("Cookie Security","medium",f"Cookie missing HttpOnly: {c['name']}","Accessible via JavaScript",location=self.page.url,recommendation="Set HttpOnly flag")

    async def test_info_disclosure(self):
        try:
            page_content = await self.page.content()
            for pattern, description in INFO_DISCLOSURE_PATTERNS:
                matches = re.findall(pattern, page_content, re.IGNORECASE)
                if matches:
                    finding = self.add_finding("Information Disclosure","critical",f"Potential: {description}",f"Found {len(matches)} match(es)",location=self.page.url,evidence=f"Pattern: {pattern[:80]}",recommendation="Remove secrets from source code")
                    await self._capture_if_important(finding)
        except Exception: pass

    async def test_cors(self):
        try:
            for origin in ["https://evil.com","null"]:
                resp = await self.context.request.get(self.base_url, headers={"Origin":origin}, timeout=10000)
                acao = resp.headers.get("access-control-allow-origin","")
                acac = resp.headers.get("access-control-allow-credentials","")
                if acao == origin and acac.lower() == "true":
                    finding = self.add_finding("CORS","critical","CORS misconfiguration",f"Origin {origin} reflected with credentials",location=self.base_url,evidence=f"ACAO: {acao}, ACAC: {acac}",recommendation="Do not reflect Origin with credentials")
                    await self._capture_if_important(finding)
                    break
        except Exception: pass

    async def test_clickjacking(self):
        try:
            resp = await self.context.request.get(self.base_url, timeout=10000)
            xfo = resp.headers.get("x-frame-options","")
            csp = resp.headers.get("content-security-policy","")
            if not xfo and "frame-ancestors" not in csp.lower():
                self.add_finding("Clickjacking","medium","Missing Clickjacking Protection","No X-Frame-Options or CSP frame-ancestors",location=self.base_url,recommendation="Add X-Frame-Options: DENY")
        except Exception: pass

    async def test_form_security(self):
        forms = await self.page.query_selector_all("form")
        for form in forms:
            try:
                action = await form.get_attribute("action") or self.page.url
                if not action.startswith("https://"):
                    finding = self.add_finding("Form Security","high","Form submits over HTTP",f"Action: {action[:100]}",location=self.page.url,recommendation="Use HTTPS")
                    await self._capture_if_important(finding)
            except Exception: continue

    async def test_ssl(self):
        if not self.base_url.startswith("https://"):
            finding = self.add_finding("SSL/TLS","high","No HTTPS","Website does not use HTTPS",location=self.base_url,recommendation="Enable HTTPS")
            await self._capture_if_important(finding)
            return
        try:
            mixed = await self.page.evaluate("""() => { const insecure = []; document.querySelectorAll('img[src^="http:"], script[src^="http:"], link[href^="http:"]').forEach(el => { insecure.push(el.tagName + ': ' + (el.src || el.href)); }); return insecure; }""")
            if mixed:
                finding = self.add_finding("SSL/TLS","medium","Mixed Content",f"Found {len(mixed)} insecure resources",location=self.page.url,evidence=f"First: {mixed[0][:100]}" if mixed else "",recommendation="Use HTTPS for all resources")
        except Exception: pass

    async def test_directory_listing(self):
        for path in ["/images/","/uploads/","/assets/","/admin/","/backup/","/logs/"]:
            try:
                resp = await self.context.request.get(f"{self.base_url.rstrip('/')}{path}", timeout=8000)
                if resp.status == 200:
                    body = await resp.text()
                    if any(ind.lower() in body.lower() for ind in ["Index of /","Directory Listing For","Parent Directory"]):
                        self.add_finding("Directory Listing","medium",f"Directory listing: {path}","Contents publicly visible",location=f"{self.base_url.rstrip('/')}{path}",recommendation="Disable directory listing")
            except Exception: continue

    async def test_blind_oob(self):
        if not self.oob or not self.oob.subdomain: return
        payload_url = await self.oob.get_payload_url("blind")
        current_url = self.page.url
        parsed = urlparse(current_url)
        if parsed.query:
            params = parse_qs(parsed.query)
            for param, values in params.items():
                try:
                    test_url = current_url.replace(f"{param}={values[0]}", f"{param}={urllib.parse.quote(payload_url)}")
                    await self.context.request.get(test_url, timeout=10000)
                except Exception: pass
        await self.page.wait_for_timeout(3000)
        interactions = await self.oob.poll()
        if interactions:
            poc = f"curl -X GET \"{test_url}\" -v" if 'test_url' in locals() else f"Inject '{payload_url}' into vulnerable parameter."
            self.add_finding("Blind OOB","critical","OOB interaction detected",f"Payload: {payload_url}",evidence=str(interactions)[:200], poc=poc)

    async def test_mass_assignment(self):
        console.print("[yellow]Running Mass Assignment / Business Logic Tests...[/yellow]")
        mutations = [{"is_admin": True}, {"role": "admin"}, {"role_id": 1}, {"balance": 999999}, {"plan": "premium"}]
        
        async def intercept_and_mutate(route, request):
            if request.method in ["POST", "PUT", "PATCH"]:
                post_data = request.post_data
                if post_data and request.headers.get("content-type", "").startswith("application/json"):
                    try:
                        data = json.loads(post_data)
                        if isinstance(data, dict):
                            for mutation in mutations:
                                mutated_data = {**data, **mutation}
                                try:
                                    resp = await self.context.request.fetch(
                                        request, 
                                        data=json.dumps(mutated_data),
                                        headers={**request.headers, "content-type": "application/json"}
                                    )
                                    if resp.status in [200, 201]:
                                        finding = self.add_finding("Mass Assignment", "high", f"Potential Privilege Escalation via {list(mutation.keys())[0]}", "Server accepted mutated JSON payload with elevated privileges.", location=request.url, evidence=f"Injected: {json.dumps(mutation)}", recommendation="Implement strict allowed-lists for JSON deserialization.")
                                        await self._capture_if_important(finding)
                                except Exception: pass
                    except Exception: pass
            await route.continue_()
            
        await self.page.route("**/*", intercept_and_mutate)
        
        # Trigger basic actions to fire the intercepted requests
        try:
            forms = await self.page.query_selector_all("form")
            for form in forms[:3]:
                submit_btn = await form.query_selector("button[type='submit'], input[type='submit']")
                if submit_btn: await submit_btn.click(timeout=3000)
        except Exception: pass
        
        # Cleanup route
        await self.page.unroute("**/*", intercept_and_mutate)


    def get_summary(self) -> dict:
        by_sev = defaultdict(list)
        for f in self.findings: by_sev[f.severity].append(f)
        return {
            "total": len(self.findings),
            "critical": len(by_sev.get("critical",[])),
            "high": len(by_sev.get("high",[])),
            "medium": len(by_sev.get("medium",[])),
            "low": len(by_sev.get("low",[])),
            "findings": [f.to_dict() for f in self.findings],
        }

# ═══════════════════════════════════════════
# MICRO-INTERACTION TESTER
# ═══════════════════════════════════════════

class MicroInteractionTester:
    def __init__(self, page: Page, error_tracker: ErrorTracker):
        self.page = page
        self.error_tracker = error_tracker

    async def test_all_interactions(self, page_url: str) -> List[Dict]:
        results = []
        for interaction_id, interaction in MICRO_INTERACTIONS.items():
            result = await self._test_single(interaction_id, interaction, page_url)
            results.append(result)
        return results

    async def _test_single(self, interaction_id: str, interaction: Dict, page_url: str) -> Dict:
        result = {"id": interaction_id, "name": interaction["name"], "page_url": page_url, "status": "not_found", "details": ""}
        element = None
        used_selector = ""
        for selector in interaction["selectors"]:
            try:
                elements = await self.page.query_selector_all(selector)
                for el in elements:
                    if await el.is_visible():
                        element = el
                        used_selector = selector
                        break
                if element: break
            except Exception: continue
        if not element:
            result["details"] = "Not found"
            return result
        result["selector_used"] = used_selector
        result["status"] = "found"
        action = interaction.get("test_action", "")
        try:
            if action == "type_test_query":
                await element.fill("test_query")
                await self.page.wait_for_timeout(500)
                await element.fill("")
                result["status"] = "tested"
                result["details"] = "Search works"
            elif action == "change_select_option":
                tag = await element.evaluate("el => el.tagName.toLowerCase()")
                if tag == "select":
                    opts = await element.query_selector_all("option")
                    if len(opts) > 1:
                        await element.select_option(index=1)
                        result["status"] = "tested"
                        result["details"] = "Filter changed"
            elif action == "click_page_2":
                links = await element.query_selector_all('a, button')
                for link in links:
                    text = (await link.text_content() or "").strip()
                    if text in ["2", "Next", "»"]:
                        await link.click()
                        result["status"] = "tested"
                        result["details"] = "Pagination works"
                        break
            elif action == "click_first_sortable":
                await element.click()
                result["status"] = "tested"
                result["details"] = "Sort clicked"
            elif action == "click_second_tab":
                tabs = await self.page.query_selector_all('.nav-tabs a, [role="tab"]')
                if len(tabs) > 1:
                    await tabs[1].click()
                    result["status"] = "tested"
                    result["details"] = f"Tab 2/{len(tabs)}"
            elif action == "click_and_close_modal":
                await element.click()
                await self.page.wait_for_timeout(1000)
                modal = await self.page.query_selector('.modal.show, [aria-modal="true"]')
                if modal:
                    await self.page.keyboard.press("Escape")
                    result["status"] = "tested"
                    result["details"] = "Modal tested"
            elif action == "toggle_dropdown":
                await element.click()
                result["status"] = "tested"
                result["details"] = "Dropdown toggled"
            elif action == "toggle_accordion":
                await element.click()
                result["status"] = "tested"
                result["details"] = "Accordion toggled"
            elif action == "test_empty_submission":
                result["status"] = "tested"
                result["details"] = "Form found"
            elif action == "type_date_and_check":
                await element.fill("2026-06-15")
                result["status"] = "tested"
                result["details"] = "Date entered"
            elif action == "toggle_checkbox":
                was = await element.is_checked()
                await element.click()
                now = await element.is_checked()
                result["status"] = "tested"
                result["details"] = f"Toggle: {was}→{now}"
                if was != now: await element.click()
            elif action == "change_option":
                tag = await element.evaluate("el => el.tagName.toLowerCase()")
                if tag == "select":
                    opts = await element.query_selector_all("option")
                    if len(opts) > 1:
                        await element.select_option(index=1)
                        result["status"] = "tested"
            elif action == "type_in_editor":
                await element.fill("Lilo test")
                result["status"] = "tested"
                result["details"] = "Editor works"
            elif action == "check_upload_exists":
                result["status"] = "tested"
                result["details"] = "Upload exists"
            elif action == "check_table_interactive":
                rows = await element.query_selector_all("tbody tr")
                headers = await element.query_selector_all("thead th")
                result["status"] = "tested"
                result["details"] = f"{len(rows)}r × {len(headers)}c"
            else:
                result["status"] = "tested"
                result["details"] = "OK"
        except Exception as e:
            result["status"] = "error"
            result["details"] = str(e)[:150]
            self.error_tracker.add_error(f"{interaction['name']} Error", str(e), page_url=page_url, component=interaction["name"], selector=used_selector)
        return result

# ═══════════════════════════════════════════
# LOGIN HANDLER
# ═══════════════════════════════════════════

class LoginHandler:
    def __init__(self, page: Page, context: BrowserContext, base_url: str,
                 custom_login_url: Optional[str] = None,
                 credential_manager: Optional[CredentialManager] = None,
                 skip_login: bool = False,
                 screenshot_manager: Optional[ScreenshotManager] = None):
        self.page = page
        self.context = context
        self.base_url = base_url
        self.custom_login_url = custom_login_url
        self.credential_manager = credential_manager or CredentialManager()
        self.skip_login = skip_login
        self.screenshot_manager = screenshot_manager
        self.domain = urlparse(base_url).netloc
        self.is_logged_in = False
        self.login_url_used = ""
        self.auth_type = "unknown"

    async def _is_dashboard(self) -> bool:
        try:
            indicators = await self.page.evaluate("""() => {
                const body = document.body?.textContent?.toLowerCase() || '';
                const dashWords = ['dashboard', 'admin', 'panel', 'menu', 'sidebar', 'navigation', 'logout'];
                const score = dashWords.filter(w => body.includes(w)).length;
                const hasNav = !!document.querySelector('nav, aside, .sidebar, .menu, .navbar, .navigation');
                const hasTable = !!document.querySelector('table');
                const hasCards = document.querySelectorAll('.card, .widget, .stat-box, .dashboard-card').length;
                return { score, hasNav, hasTable, cardCount: hasCards };
            }""")
            if indicators.get("hasNav") and (indicators.get("hasTable") or indicators.get("cardCount", 0) > 0 or indicators.get("score", 0) >= 2):
                return True
            return False
        except Exception: return False

    async def _analyze_login_form(self) -> Dict[str, Any]:
        return await self.page.evaluate("""() => {
            const passwordField = document.querySelector('input[type="password"]');
            if (!passwordField) return { type: 'no_password_field' };
            const form = passwordField.closest('form');
            const allInputs = form ? Array.from(form.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="button"])')) : [passwordField];
            const usernameFields = [];
            for (const input of allInputs) {
                if (input.type === 'password') continue;
                const name = (input.name || '').toLowerCase();
                const type = input.type || 'text';
                const id = (input.id || '').toLowerCase();
                if (name.includes('user') || name.includes('email') || name.includes('login') || type === 'email' || id.includes('user') || id.includes('email')) {
                    usernameFields.push({ name: input.name, type: input.type, id: input.id, placeholder: input.placeholder });
                }
            }
            const submitBtn = form ? form.querySelector('button[type="submit"], input[type="submit"], button') : null;
            return {
                type: usernameFields.length > 0 ? 'username_password' : 'password_only',
                usernameFields: usernameFields,
                hasSubmitButton: !!submitBtn,
                submitButtonText: submitBtn ? (submitBtn.textContent?.trim() || submitBtn.value || '') : '',
                totalInputs: allInputs.length,
                passwordFieldName: passwordField.name || passwordField.id || '',
            };
        }""")

    async def find_login_page(self) -> Optional[str]:
        if self.custom_login_url:
            login_url = normalize_url(self.custom_login_url)
            console.print(f"[cyan]🔗 Custom login URL: {login_url}[/cyan]")
            try:
                await self.page.goto(login_url, wait_until="domcontentloaded", timeout=15000)
                await self.page.wait_for_timeout(2000)
                has_password = await self.page.evaluate("() => !!document.querySelector('input[type=\"password\"]')")
                if has_password:
                    console.print("[green]✅ Login form found![/green]")
                    return login_url
                if await self._is_dashboard():
                    console.print("[green]✅ Already on dashboard![/green]")
                    self.auth_type = "direct_access"
                    self.is_logged_in = True
                    return None
                return login_url
            except Exception as e:
                console.print(f"[red]❌ Failed: {truncate(e)}[/red]")
        has_password = await self.page.evaluate("() => !!document.querySelector('input[type=\"password\"]')")
        if has_password:
            console.print("[green]✅ Login form on current page![/green]")
            return self.page.url
        if await self._is_dashboard():
            console.print("[green]✅ Already on dashboard![/green]")
            self.auth_type = "direct_access"
            self.is_logged_in = True
            return None
        login_links = await self.page.evaluate("""() => {
            const links = Array.from(document.querySelectorAll('a[href]'));
            const keywords = ['login', 'signin', 'masuk', 'admin'];
            const found = [];
            for (const link of links) {
                const text = (link.textContent || '').toLowerCase();
                const href = (link.href || '').toLowerCase();
                for (const kw of keywords) {
                    if (text.includes(kw) || href.includes(kw)) {
                        found.push({ text: link.textContent?.trim()?.substring(0, 50) || '', href: link.href });
                        break;
                    }
                }
            }
            return found.slice(0, 5);
        }""")
        if login_links:
            for link in login_links:
                try:
                    await self.page.goto(link["href"], wait_until="domcontentloaded", timeout=15000)
                    await self.page.wait_for_timeout(2000)
                    if await self.page.evaluate("() => !!document.querySelector('input[type=\"password\"]')"):
                        console.print("[green]✅ Navigated to login page![/green]")
                        return self.page.url
                    if await self._is_dashboard():
                        console.print("[green]✅ Navigated to dashboard![/green]")
                        self.auth_type = "direct_access"
                        self.is_logged_in = True
                        return None
                except Exception: continue
        base = self.base_url.rstrip("/")
        for path in COMMON_LOGIN_PATHS[:8]:
            try:
                await self.page.goto(f"{base}{path}", wait_until="domcontentloaded", timeout=10000)
                await self.page.wait_for_timeout(1000)
                if await self.page.evaluate("() => !!document.querySelector('input[type=\"password\"]')"):
                    console.print(f"[green]✅ Found: {base}{path}[/green]")
                    return self.page.url
                if await self._is_dashboard():
                    console.print(f"[green]✅ Dashboard: {base}{path}[/green]")
                    self.auth_type = "direct_access"
                    self.is_logged_in = True
                    return None
            except Exception: continue
        console.print("[red]❌ Login page not found![/red]")
        console.print("[yellow]💡 Use --login-url to specify login URL[/yellow]")
        return None

    async def attempt_login(self) -> bool:
        if self.skip_login:
            console.print("[yellow]⏭️  Skipping login[/yellow]")
            if await self._is_dashboard():
                self.is_logged_in = True
                self.auth_type = "direct_access"
                console.print("[green]✅ Dashboard detected (skip mode)![/green]")
                return True
            return False
        console.print("\n[bold magenta]🔐 LOGIN PROCESS[/bold magenta]")
        login_url = await self.find_login_page()
        if self.is_logged_in and self.auth_type == "direct_access":
            console.print("\n[bold green]🎉 ALREADY AUTHENTICATED![/bold green]")
            if self.screenshot_manager:
                await self.screenshot_manager.capture_page_screenshot(self.page, self.page.url, "Dashboard Direct Access", "dashboard_direct")
            return True
        if not login_url:
            if await self._is_dashboard():
                self.is_logged_in = True
                self.auth_type = "direct_access"
                console.print("[green]✅ Dashboard detected![/green]")
                return True
            return False
        self.login_url_used = login_url
        console.print(f"\n[bold]📍 Login URL:[/bold] {login_url}")
        if self.page.url != login_url:
            try:
                await self.page.goto(login_url, wait_until="networkidle", timeout=20000)
                await self.page.wait_for_timeout(2000)
            except Exception: pass
        console.print("[cyan]🔍 Analyzing login form...[/cyan]")
        form_info = await self._analyze_login_form()
        if form_info.get("type") == "no_password_field":
            console.print("[yellow]⚠️ No password field found[/yellow]")
            if await self._is_dashboard():
                self.is_logged_in = True
                self.auth_type = "direct_access"
                console.print("[green]✅ Dashboard detected - no login needed![/green]")
                return True
            return False
        self.auth_type = form_info["type"]
        if form_info["type"] == "password_only":
            console.print("[bold yellow]🔑 PASSWORD-ONLY FORM DETECTED[/bold yellow]")
        else:
            console.print("[bold cyan]📧 USERNAME + PASSWORD FORM[/bold cyan]")
        saved_cred = self.credential_manager.select_credential_interactive(login_url)
        if saved_cred:
            console.print(f"\n[cyan]📝 Using saved credential: {saved_cred['label']}[/cyan]")
            username = saved_cred.get("username", "")
            password = saved_cred["password"]
            is_saved = True
        else:
            console.print("\n[bold cyan]📝 ENTER CREDENTIALS[/bold cyan]")
            if not Confirm.ask("Proceed with login?", default=True): return False
            if form_info["type"] == "password_only":
                username = ""
                skip_user = Confirm.ask("  Skip username/email? (Enter=yes)", default=True)
                if not skip_user:
                    username = Prompt.ask("  📧 Username / Email (optional, press Enter to skip)")
                    if not username: username = ""
                password = Prompt.ask("  🔑 Password", password=True)
            else:
                username = Prompt.ask("  📧 Username / Email")
                password = Prompt.ask("  🔑 Password", password=True)
            is_saved = False
        password_field = await self.page.query_selector('input[type="password"]')
        if not password_field:
            console.print("[red]❌ Cannot find password field![/red]")
            return False
        try:
            await password_field.click()
            await password_field.fill("")
            await password_field.type(password, delay=50)
            console.print("[green]✅ Password filled[/green]")
        except Exception as e:
            console.print(f"[red]❌ Failed to fill password: {truncate(e)}[/red]")
            return False
        if username:
            username_field = None
            for uf_info in form_info.get("usernameFields", []):
                if uf_info.get("name"): username_field = await self.page.query_selector(f'input[name="{uf_info["name"]}"]')
                elif uf_info.get("id"): username_field = await self.page.query_selector(f'#{uf_info["id"]}')
                if username_field: break
            if not username_field:
                for sel in ['input[type="email"]', 'input[name="email"]', 'input[name="username"]', 'input[type="text"]:first-of-type']:
                    try:
                        username_field = await self.page.query_selector(sel)
                        if username_field and await username_field.get_attribute("type") != "password":
                            break
                        username_field = None
                    except Exception: continue
            if username_field:
                try:
                    await username_field.click()
                    await username_field.fill("")
                    await username_field.type(username, delay=50)
                    console.print("[green]✅ Username filled[/green]")
                except Exception: console.print("[yellow]⚠️ Could not fill username[/yellow]")
            else: console.print("[yellow]⚠️ No username field found[/yellow]")
        elif form_info["type"] == "password_only":
            console.print("[dim]  (Password-only form)[/dim]")
        console.print("[cyan]🔘 Submitting login form...[/cyan]")
        submit_btn = None
        for sel in ['button[type="submit"]', 'input[type="submit"]', 'form button', 'button']:
            try:
                submit_btn = await self.page.query_selector(sel)
                if submit_btn and await submit_btn.is_visible():
                    break
                submit_btn = None
            except Exception: continue
        if submit_btn:
            try:
                if await submit_btn.is_enabled(): await submit_btn.click()
                else: await password_field.press("Enter")
            except Exception: await password_field.press("Enter")
        else:
            await password_field.press("Enter")
        console.print("[cyan]⏳ Waiting for login to complete...[/cyan]")
        await self.page.wait_for_timeout(3000)
        try: await self.page.wait_for_load_state("networkidle", timeout=20000)
        except Exception: console.print("[yellow]⚠️ Timeout waiting for network idle[/yellow]")
        await self.page.wait_for_timeout(2000)
        current_url = self.page.url
        still_has_password = await self.page.evaluate("() => !!document.querySelector('input[type=\"password\"]')")
        error_selectors = ['.alert-danger','.alert-error','.error-message','.text-danger','.text-error','[role="alert"]','.invalid-feedback','.error','.message-error','.notification-error','.toast-error']
        has_errors = False
        for sel in error_selectors:
            try:
                elements = await self.page.query_selector_all(sel)
                for el in elements:
                    if await el.is_visible():
                        text = (await el.text_content() or "").strip()
                        if text and len(text) > 2:
                            console.print(f"[red]❌ Error message: {text[:200]}[/red]")
                            has_errors = True
            except Exception: continue
        is_dashboard = await self._is_dashboard()
        url_changed = current_url != login_url
        if still_has_password and has_errors:
            console.print("[red]❌ LOGIN FAILED - Error message detected[/red]")
            return False
        if still_has_password and not is_dashboard and not url_changed:
            console.print("[red]❌ LOGIN FAILED - Still on login page[/red]")
            return False
        self.is_logged_in = True
        console.print("\n[bold green]🎉 LOGIN SUCCESS![/bold green]")
        if self.screenshot_manager:
            await self.screenshot_manager.capture_page_screenshot(self.page, current_url, "After Login", "after_login")
        if not is_saved:
            if Confirm.ask("\n💾 Save this credential for future use?", default=True):
                label = Prompt.ask("  Label", default=username if username else "password-only")
                self.credential_manager.save_credential(login_url, username, password, label)
                console.print("[green]✅ Credential saved![/green]")
        try:
            session_dir = Path("lilo_reports/sessions")
            session_dir.mkdir(parents=True, exist_ok=True)
            await self.context.storage_state(path=str(session_dir / "auth_session.json"))
            console.print("[dim]Browser session state saved[/dim]")
        except Exception: pass
        return True

# ═══════════════════════════════════════════
# DEEP CRAWLER
# ═══════════════════════════════════════════

class DeepCrawler:
    def __init__(self, page, context, domain, config, error_tracker, perf_tracker, screenshot_manager):
        self.page = page
        self.context = context
        self.domain = domain
        self.config = config
        self.error_tracker = error_tracker
        self.perf_tracker = perf_tracker
        self.screenshot_manager = screenshot_manager
        self.max_pages = config.get("max_pages", 50)
        self.visited_urls: Set[str] = set()
        self.discovered_pages: List[Dict] = []
        self.components_found: Dict[str, int] = defaultdict(int)
        self.api_endpoints: List[Dict] = []
        self.micro_test_results: List[Dict] = []
        self.bundle_analyzer = BundleAnalyzer(context, domain)
        self._setup_monitoring()

    def _setup_monitoring(self):
        seen_endpoints: Set[str] = set()

        # API path patterns to capture from network traffic
        API_PATTERNS = [
            '/api/', '/graphql', '/ajax/', '/rest/', '/rpc/',
            '/v1/', '/v2/', '/v3/', '/v4/', '/v5/',
            '/ws/', '/webhook', '/callback',
        ]
        # Also catch REST-style /resource/id patterns (path with 2+ segments)
        REST_PATTERN = re.compile(r'/(?:data|service|user|account|product|order|item|admin)[s]?/\d+')

        async def on_request(request: Request):
            url_lower = request.url.lower()
            is_api = (
                any(p in url_lower for p in API_PATTERNS)
                or REST_PATTERN.search(request.url)
                or request.resource_type in ("xhr", "fetch")
            )
            if is_api:
                key = f"{request.method}:{request.url}"
                if key not in seen_endpoints:
                    seen_endpoints.add(key)
                    self.api_endpoints.append({
                        "method": request.method,
                        "url": request.url,
                        "type": request.resource_type,
                        "page": self.page.url,
                    })
            self.perf_tracker.record_resource_start(request)

        async def on_response(response: Response):
            if response.request:
                self.perf_tracker.record_resource(response.request, response)

        async def on_request_failed(request: Request):
            self.error_tracker.add_error(
                "Network Failed", f"{request.method} {request.url}",
                page_url=self.page.url,
                extra={"failure": str(request.failure) if request.failure else "Unknown"}
            )

        async def on_console(msg):
            if msg.type in ["error", "warning"]:
                location = getattr(msg, "location", {})
                self.error_tracker.add_error(
                    f"Console {msg.type}", msg.text[:300],
                    page_url=self.page.url,
                    extra={"url": location.get("url",""), "line": location.get("lineNumber",""),
                           "column": location.get("columnNumber","")}
                )

        self.page.on("request", on_request)
        self.page.on("response", on_response)
        self.page.on("requestfailed", on_request_failed)
        self.page.on("console", on_console)

    async def explore(self):
        start_url = clean_url(self.page.url)
        self.visited_urls.add(start_url)
        title = await self.page.title()
        console.print(f"[green]📍 Starting: {title}[/green]")
        await self.perf_tracker.measure_web_vitals(self.page)
        self._print_perf_summary()
        await self.screenshot_manager.capture_page_screenshot(self.page, start_url, title, "00_dashboard")
        tester = MicroInteractionTester(self.page, self.error_tracker)
        self.micro_test_results = await tester.test_all_interactions(start_url)
        self._print_micro_summary(self.micro_test_results)
        await self._discover_navigation()
        await self._expand_menus()
        await self._discover_navigation()
        await self._explore_interactive_elements()
        await self._analyze_js_bundles()
        await self._explore_pages()
        await self._scan_components()
        return {
            "pages_explored": len(self.visited_urls),
            "pages": self.discovered_pages,
            "components": dict(self.components_found),
            "api_endpoints": self.api_endpoints + self.bundle_analyzer.found_endpoints,
            "micro_tests": self.micro_test_results,
            "screenshots": self.screenshot_manager.get_all_screenshots(),
        }

    def _print_perf_summary(self):
        summary = self.perf_tracker.get_summary()
        color = "green" if summary['score'] >= 75 else ("yellow" if summary['score'] >= 50 else "red")
        console.print(f"\n[bold]⚡ Performance Score:[/bold] [{color}]{summary['score']}/100 ({summary['grade']})[/{color}]")
        console.print(f"  TTFB: {summary['web_vitals']['ttfb_formatted']} | FCP: {summary['web_vitals']['fcp_formatted']} | LCP: {summary['web_vitals']['lcp_formatted']} | CLS: {summary['web_vitals']['cls']}")

    def _print_micro_summary(self, results: List[Dict]):
        tested = [r for r in results if r["status"] == "tested"]
        errors = [r for r in results if r["status"] == "error"]
        console.print(f"\n[bold]📊 Micro-Tests:[/bold] ✅ {len(tested)} tested, ❌ {len(errors)} errors")

    async def _discover_navigation(self):
        all_links = []
        for selector in NAV_SELECTORS[:10]:
            try:
                links = await self.page.evaluate(f"""() => {{
                    return Array.from(document.querySelectorAll('{selector}'))
                        .filter(el => el.href && !el.href.startsWith('javascript:') && !el.href.startsWith('#'))
                        .map(el => ({{href: el.href, text: (el.textContent || '').trim().substring(0, 100)}}));
                }}""")
                all_links.extend(links)
            except Exception: pass
        seen = set()
        new_pages = 0
        for link in all_links:
            try:
                url = clean_url(link["href"])
                if not url or url in seen: continue
                if not same_domain(self.domain, url): continue
                if any(kw in url.lower() for kw in ['logout', 'signout']): continue
                if any(url.lower().endswith(ext) for ext in ['.css','.js','.png','.jpg','.svg','.ico','.pdf']): continue
                seen.add(url)
                if url not in self.visited_urls:
                    self.discovered_pages.append({"url": url, "title": link.get("text", ""), "source": self.page.url})
                    new_pages += 1
            except Exception: continue
        console.print(f"[green]✅ Found {new_pages} new pages[/green]")

    async def _expand_menus(self):
        expanded = 0
        for selector in EXPANDABLE_SELECTORS:
            try:
                elements = await self.page.query_selector_all(selector)
                for el in elements:
                    if await el.is_visible():
                        await el.click()
                        await self.page.wait_for_timeout(300)
                        expanded += 1
            except Exception: continue
        if expanded > 0:
            console.print(f"[green]✅ {expanded} menus expanded[/green]")
            await self.page.wait_for_timeout(1000)

    async def _explore_interactive_elements(self):
        """Click non-submit buttons to discover SPA routes. Hard-capped at 10 elements
        with a per-click timeout so it never hangs."""
        try:
            interactive = await asyncio.wait_for(
                self.page.evaluate("""() => {
                    const els = document.querySelectorAll(
                        'button:not([type="submit"]):not([data-bs-toggle]):not([data-toggle]), [data-action]'
                    );
                    return Array.from(els).slice(0, 10).map(el => ({
                        tag: el.tagName.toLowerCase(),
                        text: el.textContent?.trim().substring(0, 30) || '',
                        visible: el.offsetParent !== null
                    }));
                }"""),
                timeout=5
            )
        except asyncio.TimeoutError:
            return
        base_url = self.page.url
        for el in interactive[:10]:
            if not el.get('visible') or not el.get('text'): continue
            try:
                safe_text = el['text'].replace("'", "").replace('"', '')
                if not safe_text: continue
                await asyncio.wait_for(
                    self.page.click(f"{el['tag']}:has-text('{safe_text}')", timeout=2000),
                    timeout=3
                )
                await self.page.wait_for_timeout(300)
                new_url = clean_url(self.page.url)
                if new_url not in self.visited_urls and same_domain(self.domain, new_url):
                    self.discovered_pages.append({"url": new_url, "title": el['text'], "source": "interactive"})
                    self.visited_urls.add(new_url)
                # Navigate back if page changed
                if self.page.url != base_url:
                    try:
                        await asyncio.wait_for(self.page.go_back(wait_until="domcontentloaded", timeout=5000), timeout=6)
                    except Exception:
                        try:
                            await asyncio.wait_for(self.page.goto(base_url, wait_until="domcontentloaded", timeout=8000), timeout=9)
                        except Exception: pass
            except Exception: pass

    async def _analyze_js_bundles(self):
        """Analyze up to 5 JS bundles from same domain for hidden API endpoints."""
        try:
            script_urls = await asyncio.wait_for(
                self.page.evaluate("""() => {
                    return Array.from(document.querySelectorAll('script[src]'))
                        .map(s => s.src)
                        .filter(src => src.includes(window.location.hostname))
                        .slice(0, 5);
                }"""),
                timeout=5
            )
        except asyncio.TimeoutError:
            return
        await self.bundle_analyzer.analyze_scripts(script_urls)
        await self.bundle_analyzer.analyze_source_maps(script_urls)

    async def _explore_pages(self):
        pages_to_visit = [p for p in self.discovered_pages if p["url"] not in self.visited_urls][:self.max_pages]
        if not pages_to_visit:
            console.print("[yellow]⚠️ No new pages[/yellow]")
            return
        console.print(f"\n[bold cyan]🔍 Exploring {len(pages_to_visit)} pages...[/bold cyan]")
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(), TextColumn("[progress.percentage]{task.percentage:>3.0f}%"), TimeElapsedColumn(), console=console) as progress:
            task = progress.add_task("[cyan]Exploring...", total=len(pages_to_visit))
            for i, page_info in enumerate(pages_to_visit):
                url = page_info["url"]
                progress.update(task, description=f"[cyan]{i+1}/{len(pages_to_visit)}: {truncate(url, 50)}[/cyan]")
                try:
                    start = time.time()
                    resp = await self.page.goto(url, wait_until="domcontentloaded", timeout=15000)
                    load_time = time.time() - start
                    self.perf_tracker.record_page_load(url, load_time, resp.status if resp else 0)
                    await self.page.wait_for_timeout(1000)
                    self.visited_urls.add(url)
                    page_info["title"] = await self.page.title()
                    if i < 10:
                        tester = MicroInteractionTester(self.page, self.error_tracker)
                        self.micro_test_results.extend(await tester.test_all_interactions(url))
                    if i < 20:
                        await self.screenshot_manager.capture_page_screenshot(self.page, url, page_info["title"], f"page_{i+1:02d}")
                        
                    # Proactive garbage collection for memory leak prevention
                    try: await self.page.evaluate("window.gc && window.gc()")
                    except Exception: pass

                except Exception as e:
                    console.print(f"[yellow]⚠️ Failed: {truncate(url, 60)} - {truncate(e)}[/yellow]")
                    page_info["error"] = str(e)
                progress.advance(task)

    async def _scan_components(self):
        for comp_name, selectors in COMPONENT_SELECTORS.items():
            for selector in selectors:
                try:
                    count = await self.page.evaluate(f"document.querySelectorAll('{selector}').length")
                    if count > 0: self.components_found[comp_name] += count
                except Exception: pass
        if self.components_found:
            console.print("[green]✅ Components:[/green]")
            for name, count in sorted(self.components_found.items()):
                console.print(f"  • {name}: {count}")

# ═══════════════════════════════════════════
# MAIN LILO TESTER v5.0.0
# ═══════════════════════════════════════════

def get_banner() -> str:
    # Each letter in TESTER uses a different fill character:
    # T=▓  E=▒  S=░  T=#  E=@  R=$
    return (
        f"\n"
        f"  [dim]lilo[/dim]  [dim]v{APP_VERSION}[/dim]\n"
        f"\n"
        f"  [bold cyan]▓▓▓▓▓▓▓▓  ▒▒▒▒▒▒▒    ░░░░░░  ########  @@@@@@@   $$$$$$ [/bold cyan]\n"
        f"  [bold cyan]   ▓▓     ▒▒        ░░          ##     @@        $$  $$ [/bold cyan]\n"
        f"  [bold cyan]   ▓▓     ▒▒▒▒▒▒    ░░░░░     ##     @@@@@@    $$$$$$ [/bold cyan]\n"
        f"  [bold cyan]   ▓▓     ▒▒             ░░     ##     @@        $$  $$ [/bold cyan]\n"
        f"  [bold cyan]   ▓▓     ▒▒▒▒▒▒▒   ░░░░░░     ##     @@@@@@@   $$   $$[/bold cyan]\n"
        f"\n"
        f"[dim]  ──────────────────────────────────────────────────────[/dim]\n"
        f"[bold cyan]  ⚡ Engines  [/bold cyan][dim]Crawler · Fuzzer · OOB · IDOR · DOM Taint[/dim]\n"
        f"[bold cyan]  📊 Reports  [/bold cyan][dim]HTML · Markdown · PDF[/dim]\n"
        f"[bold cyan]  🛡️  Modules  [/bold cyan][dim]SQLi · XSS · SSRF · JWT · Cookie · Headers[/dim]\n"
        f"[dim]  ──────────────────────────────────────────────────────[/dim]\n"
        f"\n"
        f"[bold yellow]  Quick Tips[/bold yellow]\n"
        f"  [green]-u <URL>[/green]               Target URL (required)\n"
        f"  [green]-m quick[/green]               Fast scan, skip deep crawler\n"
        f"  [green]--headless[/green]             Run browser silently in background\n"
        f"  [green]--enable-idor[/green]          Detect IDOR/BOLA (add [cyan]--idor-user user:pass[/cyan])\n"
        f"  [green]--enable-mass-assign[/green]   Business logic test (destructive, opt-in)\n"
        f"  [green]--ignore-waf[/green]           Force scan even if WAF is detected\n"
        f"  [green]--no-open[/green]              Don't auto-open the report when done\n"
        f"  [green]-h, --help[/green]             Show all available options\n"
    )


class LiloTester:
    def __init__(self, url, output_dir="lilo_reports", mode="dashboard", max_pages=50,
                 headless=False, custom_login_url=None, open_report=True, skip_login=False,
                 enable_security=True, enable_idor=False, idor_user_b_creds=None,
                 oob_server=None, deep_enum=False, ignore_waf=False, enable_mass_assign=False,
                 xss_wordlist=None, sqli_wordlist=None, proxy=None, custom_headers=None, rate_limit=0, export_sarif=False):
        self.url = normalize_url(url)
        self.domain = urlparse(self.url).netloc
        self.output_dir = Path(output_dir)
        self.timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.report_dir = self.output_dir / f"report_{self.timestamp}"
        self.mode = mode
        self.max_pages = max_pages
        self.headless = headless
        self.custom_login_url = custom_login_url
        self.open_report = open_report
        self.skip_login = skip_login
        self.enable_security = enable_security
        self.enable_idor = enable_idor
        self.idor_user_b_creds = idor_user_b_creds
        self.oob_server = oob_server
        self.deep_enum = deep_enum
        self.ignore_waf = ignore_waf
        self.enable_mass_assign = enable_mass_assign
        self.xss_wordlist = xss_wordlist
        self.sqli_wordlist = sqli_wordlist
        self.proxy = proxy
        self.custom_headers = custom_headers or []
        self.rate_limit = rate_limit
        self.export_sarif = export_sarif
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.watermark = WatermarkEngine()
        self.error_tracker = ErrorTracker(self.report_dir)
        self.perf_tracker = AdvancedPerformanceTracker(self.domain)
        self.cred_manager = CredentialManager()
        self.screenshot_manager = ScreenshotManager(self.report_dir, self.watermark)
        self.results = {
            "app_name": APP_NAME,
            "version": APP_VERSION,
            "url": self.url,
            "domain": self.domain,
            "timestamp": self.timestamp,
            "mode": self.mode,
            "authenticated": False,
            "login_url_used": "",
            "recon": {},
            "vuln_analysis": {},
            "exploration": {},
            "errors_summary": {},
            "performance": {},
            "security": {},
            "total_time": 0,
        }

    async def run(self):
        start_time = time.time()
        console.print(get_banner())
        console.print(f"🎯 Target: {self.url}")

        async with async_playwright() as pw:
            pw_args = {"headless": self.headless}
            if self.proxy:
                pw_args["proxy"] = {"server": self.proxy}
            browser = await pw.chromium.launch(**pw_args)
            
            context_kwargs = {"viewport": {"width": 1920, "height": 1080}, "ignore_https_errors": True}
            if self.custom_headers:
                extra_headers = {}
                for header in self.custom_headers:
                    parts = header.split(":", 1)
                    if len(parts) == 2:
                        extra_headers[parts[0].strip()] = parts[1].strip()
                context_kwargs["extra_http_headers"] = extra_headers
                
            context_a = await browser.new_context(**context_kwargs)
            page = await context_a.new_page()

            # OOB
            oob_client = None
            if self.oob_server or self.enable_security:
                oob_client = OOBClient(self.oob_server)
                await oob_client.start()

            try:
                t0 = time.time()
                resp = await page.goto(self.url, wait_until="domcontentloaded", timeout=30000)
                self.perf_tracker.record_page_load(self.url, time.time()-t0, resp.status if resp else 0)
            except Exception as e:
                console.print(f"[red]Failed to load: {e}[/red]")
                if "aiohttp_session" in locals(): await aiohttp_session.close()
                await browser.close()
                return self.results

            # ════════════════════════════════════════
            # PHASE 1: INTELLIGENCE GATHERING (Recon)
            # ════════════════════════════════════════
            console.print("\n[bold magenta]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold magenta]")
            console.print("[bold magenta]🕵️  PHASE 1: INTELLIGENCE GATHERING[/bold magenta]")
            console.print("[bold magenta]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold magenta]")

            recon: Dict = {}

            # 1. Tech Stack Fingerprinting (needs loaded page)
            fingerprinter = TechStackFingerprinter(page, resp)
            recon["tech_stack"] = await fingerprinter.detect()

            # 2. WAF/CDN Detection (passive then active)
            waf_detector = WAFDetector(self.url, resp, context_a)
            recon["waf"] = await waf_detector.detect()

            # 3. Subdomain Enumeration (sequential - must finish before crawl)
            # Skip if target is an IP address
            is_ip = re.match(r'^\d{1,3}(?:\.\d{1,3}){3}$', self.domain.split(':')[0])
            if not is_ip:
                sub_enum = SubdomainEnumerator(self.domain, deep=self.deep_enum)
                sub_result = await sub_enum.enumerate()
                recon["subdomains"] = sub_result.get("subdomains", [])
                recon["selected_subdomains"] = sub_result.get("selected", [])
            else:
                console.print("  [dim]Subdomain enum skipped (IP target)[/dim]")
                recon["subdomains"] = []
                recon["selected_subdomains"] = []

            self.results["recon"] = recon
            self._save_json() # AUTO-SAVE

            # WAF Sync Check
            if recon.get("waf") and not self.ignore_waf:
                console.print("\n[bold red]🚨 WAF/CDN Active detected![/bold red]")
                console.print("[yellow]Aggressive fuzzing is blocked to prevent IP blocking.[/yellow]")
                if not Confirm.ask("Do you want to force scanning (risk of IP blocking)?", default=False):
                    console.print("[yellow]Scan stopped by user because WAF was detected.[/yellow]")
                    if "aiohttp_session" in locals(): await aiohttp_session.close()
                    await browser.close()
                    return self.results

            # ════════════════════════════════════════



            # Login
            handler = LoginHandler(page, context_a, self.url, self.custom_login_url, self.cred_manager, self.skip_login, self.screenshot_manager)
            logged_in = await handler.attempt_login()
            self.results["authenticated"] = logged_in
            self.results["login_url_used"] = handler.login_url_used

            if logged_in:
                async def block_write(route: Route):
                    if route.request.method in ["POST", "PUT", "PATCH", "DELETE"]:
                        await route.abort()
                    else:
                        await route.continue_()
                await page.route("**/*", block_write)
                await page.evaluate("""() => {
                    document.addEventListener('submit', function(e) {
                        e.preventDefault(); e.stopPropagation(); return false;
                    }, true);
                }""")
                console.print("[green]✅ Safe mode active[/green]")

            # Crawl
            crawler = DeepCrawler(page, context_a, self.domain, {"max_pages":self.max_pages}, self.error_tracker, self.perf_tracker, self.screenshot_manager)
            exploration = await crawler.explore()
            self.results["exploration"] = exploration
            self._save_json() # AUTO-SAVE

            # ════════════════════════════════════════
            # PHASE 2: VULNERABILITY ANALYSIS
            # ════════════════════════════════════════
            console.print("\n[bold magenta]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold magenta]")
            console.print("[bold magenta]☢️  PHASE 2: VULNERABILITY ANALYSIS[/bold magenta]")
            
            playwright_cookies = await context_a.cookies()
            cookie_dict = {c['name']: c['value'] for c in playwright_cookies}
            aiohttp_session = aiohttp.ClientSession(
                cookies=cookie_dict,
                headers=context_kwargs.get("extra_http_headers", {})
            )
            
            
            console.print("[bold magenta]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold magenta]")
            
            vuln: Dict = {}
            crawled_urls = [p["url"] for p in exploration.get("pages", [])]
            
            # 1. Smart Parameter Discovery
            param_discoverer = SmartParameterDiscoverer(context_a, self.url, max_urls=10)
            vuln["hidden_params"] = await param_discoverer.discover(crawled_urls)
            
            # 2. Context-Aware Payload Selection
            payload_selector = ContextAwarePayloadSelector(page, context_a, self.url, self.error_tracker)
            vuln["payloads"] = await payload_selector.analyze(crawled_urls, vuln["hidden_params"])
            
            # 3. Local Storage & JWT Analyzer
            storage_analyzer = LocalStorageJWTAnalyzer(page)
            vuln["storage_jwt"] = await storage_analyzer.analyze(crawled_urls)
            
            # Security scan (MOVED HERE)
            if self.enable_security:
                sec = SecurityScanner(page, context_a, self.url, self.error_tracker, self.screenshot_manager, oob_client, aiohttp_session, self.xss_wordlist, self.sqli_wordlist, self.rate_limit, self.proxy)
                sec.enable_mass_assign = getattr(self, "enable_mass_assign", False)
                
                # Always include the target URL; fallback if crawler found nothing
                scan_urls = crawled_urls if crawled_urls else [self.url]
                
                # Scan all crawled URLs
                console.print(f"[cyan]Scanning {len(scan_urls)} pages with SecurityScanner...[/cyan]")
                for u in scan_urls:
                    try:
                        await asyncio.wait_for(page.goto(u, wait_until="domcontentloaded", timeout=10000), timeout=15)
                        sec.base_url = u
                        await sec.run_all_tests()
                    except Exception as e:
                        console.print(f"[yellow]Failed to scan {u}: {e}[/yellow]")
                        
                self.results["security"] = sec.get_summary()
            
            self.results["vuln_analysis"] = vuln
            self._save_json() # AUTO-SAVE
            # ════════════════════════════════════════

            # IDOR
            if self.enable_idor and self.idor_user_b_creds:
                context_b = await browser.new_context(viewport={"width":1920,"height":1080}, ignore_https_errors=True)
                page_b = await context_b.new_page()
                victim_handler = LoginHandler(page_b, context_b, self.url, self.custom_login_url, self.cred_manager, False, self.screenshot_manager)
                if await victim_handler.attempt_login():
                    victim_crawler = DeepCrawler(page_b, context_b, self.domain, {"max_pages":10}, self.error_tracker, self.perf_tracker, self.screenshot_manager)
                    victim_exp = await victim_crawler.explore()
                    idor_engine = IDOREngine(context_a, context_b, self.url)
                    idor_findings = await idor_engine.run([p["url"] for p in victim_exp["pages"]])
                    self.results["idor"] = [f.to_dict() for f in idor_findings]
                await context_b.close()

            await page.close()
            if "aiohttp_session" in locals(): await aiohttp_session.close()
            await browser.close()
            
        # ════════════════════════════════════════
        # CONTEXT-DRIVEN REMEDIATION
        # ════════════════════════════════════════
        # Analyze findings and tech stack to provide specific recommendations
        tech_stack_names = []
        if "recon" in self.results and "tech_stack" in self.results["recon"]:
            for cat in self.results["recon"]["tech_stack"]:
                tech_stack_names.extend([t.lower() for t in self.results["recon"]["tech_stack"][cat]])
        
        has_laravel = any("laravel" in t for t in tech_stack_names)
        has_php = any("php" in t for t in tech_stack_names)
        has_react = any("react" in t for t in tech_stack_names)
        
        for finding_dict in self.results.get("security", {}).get("findings", []):
            cat = finding_dict.get("category", "")
            rec = finding_dict.get("recommendation", "")
            
            if "SQL Injection" in cat:
                if has_laravel:
                    finding_dict["recommendation"] = f"[{rec}] Use Eloquent ORM DB::table() instead of raw queries."
                elif has_php:
                    finding_dict["recommendation"] = f"[{rec}] Use PDO Prepared Statements."
            
            elif "XSS" in cat:
                if has_react:
                    finding_dict["recommendation"] = f"[{rec}] Avoid using dangerouslySetInnerHTML. React automatically escapes string variables."
                elif has_php:
                    finding_dict["recommendation"] = f"[{rec}] Use htmlspecialchars() when reflecting user input in PHP."

        self.results["total_time"] = time.time() - start_time
        self.results["errors_summary"] = self.error_tracker.get_summary()
        self.results["performance"] = self.perf_tracker.get_summary()
        self._save_json()
        report_path = self._generate_html()
        md_path = self._generate_markdown()
        console.print(f"\n[bold green]Report (HTML): {report_path}[/bold green]")
        console.print(f"[bold green]Report (Markdown): {md_path}[/bold green]")
        if self.open_report:
            console.print(f"[cyan]⏳ Generating PDF from HTML...[/cyan]")
            # Generate PDF via playwright
            await self._generate_pdf(report_path)
            webbrowser.open(f"file://{report_path.absolute()}")
            
        if self.export_sarif:
            self.export_to_sarif()
            
        return self.results

    def _save_json(self):
        with open(self.report_dir / "report.json", "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, default=str)

    def _generate_html(self) -> Path:
        env = Environment(loader=BaseLoader(), autoescape=select_autoescape(["html","xml"]))
        template = env.from_string(HTML_REPORT_V50)
        path = self.report_dir / "report.html"
        with open(path, "w", encoding="utf-8") as f:
            f.write(template.render(results=self.results))
        return path

    def export_to_sarif(self):
        sarif = {
            "version": "2.1.0",
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": APP_NAME,
                            "version": APP_VERSION,
                            "informationUri": "https://github.com/lilo/tester",
                            "rules": []
                        }
                    },
                    "results": []
                }
            ]
        }
        
        rules_added = set()
        for finding in self.results.get('security', {}).get('findings', []) + self.results.get('idor', []):
            if isinstance(finding, dict):
                rule_id = finding.get('category', 'VULN').replace(' ', '_').upper()
                if rule_id not in rules_added:
                    sarif["runs"][0]["tool"]["driver"]["rules"].append({
                        "id": rule_id,
                        "name": finding.get('category'),
                        "shortDescription": {"text": finding.get('category')},
                        "fullDescription": {"text": finding.get('category')}
                    })
                    rules_added.add(rule_id)
                    
                level_map = {"critical": "error", "high": "error", "medium": "warning", "low": "note", "info": "none"}
                
                sarif["runs"][0]["results"].append({
                    "ruleId": rule_id,
                    "level": level_map.get(finding.get('severity', 'info')),
                    "message": {
                        "text": f"{finding.get('title')}: {finding.get('description')}"
                    },
                    "locations": [{
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": finding.get('location', self.url)
                            }
                        }
                    }]
                })
            
        with open(self.report_dir / "report.sarif", "w") as f:
            json.dump(sarif, f, indent=2)
        console.print(f"[green]✅ SARIF report exported to {self.report_dir}/report.sarif[/green]")

    def _generate_markdown(self) -> Path:
        path = self.report_dir / "report.md"
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# 🦊 Lilo Tester v{APP_VERSION} - Security Report\n\n")
            f.write(f"**Target:** {self.url}\n")
            f.write(f"**Domain:** {self.domain}\n")
            f.write(f"**Date:** {self.timestamp}\n\n")
            
            f.write("## ⚡ Performance Summary\n")
            perf = self.results.get("performance", {})
            f.write(f"- Score: {perf.get('score', 0)}/100 ({perf.get('grade', '?')})\n")
            f.write(f"- TTFB: {perf.get('web_vitals', {}).get('ttfb_formatted', '?')}\n")
            f.write(f"- FCP: {perf.get('web_vitals', {}).get('fcp_formatted', '?')}\n")
            f.write(f"- LCP: {perf.get('web_vitals', {}).get('lcp_formatted', '?')}\n")
            f.write(f"- CLS: {perf.get('web_vitals', {}).get('cls', '?')}\n\n")
            
            f.write("## 🛡️ Security Findings\n")
            sec = self.results.get("security", {})
            findings = sec.get("findings", [])
            f.write(f"Total Issues: {sec.get('total', 0)} (Critical: {sec.get('critical', 0)}, High: {sec.get('high', 0)}, Medium: {sec.get('medium', 0)}, Low: {sec.get('low', 0)})\n\n")
            for i, finding in enumerate(findings):
                f.write(f"### {i+1}. [{finding.get('severity', 'info').upper()}] {finding.get('title')}\n")
                f.write(f"- **Description:** {finding.get('description')}\n")
                f.write(f"- **Location:** `{finding.get('location')}`\n")
                if finding.get('poc'): f.write(f"- **PoC:** `{finding.get('poc')}`\n")
                if finding.get('recommendation'): f.write(f"- **Recommendation:** {finding.get('recommendation')}\n")
                f.write("\n")
                
            f.write("## 🔀 IDOR / BOLA Findings\n")
            idor = self.results.get("idor", [])
            if not idor: f.write("No IDOR issues found.\n\n")
            for i, finding in enumerate(idor):
                f.write(f"### {i+1}. [{finding.get('severity', 'info').upper()}] {finding.get('title')}\n")
                f.write(f"- **Description:** {finding.get('description')}\n")
                f.write(f"- **Location:** `{finding.get('location')}`\n")
                if finding.get('poc'): f.write(f"- **PoC:** `{finding.get('poc')}`\n")
                f.write("\n")
        return path

    async def _generate_pdf(self, html_path: Path) -> Path:
        pdf_path = self.report_dir / "report.pdf"
        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(f"file://{html_path.absolute()}", wait_until="networkidle")
                await page.pdf(path=str(pdf_path), format="A4", print_background=True)
                if "aiohttp_session" in locals(): await aiohttp_session.close()
            await browser.close()
            console.print(f"[green]✅ PDF Report generated: {pdf_path}[/green]")
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not generate PDF: {e}[/yellow]")
        return pdf_path

# ═══════════════════════════════════════════
# HTML REPORT v5.0
# ═══════════════════════════════════════════

HTML_REPORT_V50 = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ results.app_name|default('Lilo Tester') }} v{{ results.version|default('5.0.0') }} - {{ results.domain }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        :root {
            --bg: #0f172a; --card: #fff; --text: #1e293b; --muted: #64748b;
            --border: #e2e8f0; --brand: #6366f1; --brand2: #8b5cf6;
            --green: #10b981; --red: #ef4444; --yellow: #f59e0b;
            --critical: #dc2626; --high: #ef4444; --medium: #f59e0b; --low: #10b981; --info: #3b82f6;
        }
        body {
            font-family: system-ui, -apple-system, sans-serif;
            background: linear-gradient(135deg, #0f172a, #1e293b);
            min-height: 100vh; padding: 24px; color: var(--text);
        }
        .container {
            max-width: 1500px; margin: 0 auto;
            background: rgba(255,255,255,0.95); border-radius: 24px;
            box-shadow: 0 25px 80px rgba(0,0,0,0.4); overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, var(--brand), var(--brand2));
            color: white; padding: 40px;
        }
        .header h1 { font-size: 2.2rem; margin-bottom: 8px; }
        .meta {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 10px; margin-top: 20px;
        }
        .meta-item {
            background: rgba(255,255,255,0.15); padding: 10px 14px;
            border-radius: 10px; border: 1px solid rgba(255,255,255,0.2);
        }
        .meta-item .label { font-size: 0.7rem; opacity: 0.7; text-transform: uppercase; }
        .meta-item .value { font-weight: 600; }
        .tab-nav {
            display: flex; gap: 0; background: #f8fafc; border-bottom: 2px solid var(--border);
            padding: 0 40px; overflow-x: auto;
        }
        .tab-btn {
            padding: 14px 20px; border: none; background: none; cursor: pointer;
            font-size: 0.85rem; font-weight: 600; color: var(--muted);
            border-bottom: 3px solid transparent; white-space: nowrap; transition: all 0.2s;
        }
        .tab-btn:hover { color: var(--brand); background: #f0f2ff; }
        .tab-btn.active { color: var(--brand); border-bottom-color: var(--brand); background: #eef2ff; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .collapsible { border: 1px solid var(--border); border-radius: 12px; margin-bottom: 14px; overflow: hidden; }
        .collapsible-header {
            padding: 14px 18px; background: #f8fafc; cursor: pointer;
            display: flex; justify-content: space-between; align-items: center;
            font-weight: 600; font-size: 0.95rem; user-select: none;
        }
        .collapsible-header:hover { background: #eef2ff; }
        .collapsible-header .arrow { transition: transform 0.3s; }
        .collapsible.open .collapsible-header .arrow { transform: rotate(180deg); }
        .collapsible-body { display: none; padding: 16px 18px; }
        .collapsible.open .collapsible-body { display: block; }
        .section { padding: 28px 40px; border-bottom: 1px solid var(--border); }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 12px; }
        .stat-card {
            padding: 18px; background: #f8fafc; border-radius: 14px;
            border: 1px solid var(--border); text-align: center;
        }
        .stat-card .number { font-size: 2.2rem; font-weight: 800; }
        .stat-card .label { font-size: 0.75rem; color: var(--muted); text-transform: uppercase; margin-top: 2px; }
        .perf-score { text-align: center; padding: 30px; }
        .perf-circle {
            display: inline-block; width: 120px; height: 120px; border-radius: 50%;
            border: 8px solid; line-height: 104px; font-size: 2.5rem; font-weight: 900; text-align: center;
        }
        .perf-grade { font-size: 1.5rem; font-weight: 800; margin-top: 8px; }
        .vitals-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; margin-top: 16px; }
        .vital-card { padding: 14px; background: white; border-radius: 10px; border: 1px solid var(--border); text-align: center; }
        .vital-card .vital-value { font-size: 1.5rem; font-weight: 800; }
        .vital-card .vital-label { font-size: 0.7rem; color: var(--muted); text-transform: uppercase; margin-top: 2px; }
        .good { color: var(--green); } .warn { color: var(--yellow); } .bad { color: var(--red); }
        .finding-card {
            padding: 14px; border-radius: 10px; margin-bottom: 10px;
            border: 1px solid var(--border); background: white;
        }
        .severity-critical { border-left: 5px solid var(--critical); background: #fef2f2; }
        .severity-high { border-left: 5px solid var(--high); background: #fff5f5; }
        .severity-medium { border-left: 5px solid var(--medium); background: #fffdf5; }
        .severity-low { border-left: 5px solid var(--low); background: #f5fff9; }
        .finding-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px; gap: 10px; }
        .finding-title { font-weight: 700; font-size: 1rem; flex: 1; }
        .finding-severity { padding: 3px 10px; border-radius: 20px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; white-space: nowrap; }
        .sev-critical { background: #dc2626; color: white; } .sev-high { background: #ef4444; color: white; }
        .sev-medium { background: #f59e0b; color: #1a1a1a; } .sev-low { background: #10b981; color: white; } .sev-info { background: #3b82f6; color: white; }
        .finding-location { font-size: 0.8rem; color: var(--brand); word-break: break-all; margin-bottom: 6px; }
        .finding-evidence { margin-top: 6px; padding: 8px 12px; background: #1e293b; border-radius: 6px; font-size: 0.78rem; color: #e2e8f0; font-family: monospace; }
        .finding-recommendation { margin-top: 6px; padding: 8px 12px; background: #ecfdf5; border-radius: 6px; font-size: 0.82rem; color: #065f46; border-left: 3px solid var(--green); }
        .finding-screenshot { margin-top: 10px; border-radius: 8px; overflow: hidden; border: 1px solid var(--border); }
        .finding-screenshot img { width: 100%; display: block; }
        .screenshot-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; }
        .screenshot-card { border: 1px solid var(--border); border-radius: 10px; overflow: hidden; background: white; }
        .screenshot-card img { width: 100%; display: block; max-height: 350px; object-fit: cover; }
        .screenshot-card .caption { padding: 8px 12px; font-size: 0.75rem; color: var(--muted); }
        table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
        th { background: #f8fafc; padding: 10px; text-align: left; font-weight: 600; border-bottom: 2px solid var(--border); }
        td { padding: 8px 10px; border-bottom: 1px solid var(--border); }
        tr:hover { background: #f8fafc; }
        .tested { color: var(--green); font-weight: 600; } .error { color: var(--red); font-weight: 600; }
        .error-item { padding: 12px; background: #fef2f2; border-radius: 8px; border-left: 4px solid var(--red); font-size: 0.82rem; margin-bottom: 6px; }
        .component-tags { display: flex; flex-wrap: wrap; gap: 6px; }
        .component-tag { padding: 5px 12px; background: #eef2ff; border-radius: 20px; font-size: 0.8rem; color: var(--brand); border: 1px solid #e0e7ff; }
        .rec-card { padding: 12px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid var(--brand); background: #f8fafc; }
        .api-item { padding: 8px 12px; background: #f0fdf4; border-radius: 8px; margin-bottom: 4px; font-family: monospace; font-size: 0.85rem; }
        .footer { background: linear-gradient(135deg, var(--brand), var(--brand2)); color: white; text-align: center; padding: 20px; }
    </style>
</head>
<body>
    <main class="container">
        <header class="header">
            <div style="display:inline-block;padding:4px 12px;border-radius:12px;background:rgba(255,255,255,0.2);font-size:0.75rem;margin-bottom:10px">
                🦊 {{ results.app_name|default('Lilo Tester') }} v{{ results.version|default('5.0.0') }}
            </div>
            <h1>Application Test Report</h1>
            <div class="meta">
                <div class="meta-item"><div class="label">Target</div><div class="value">{{ results.url[:45] }}</div></div>
                <div class="meta-item"><div class="label">Perf Score</div><div class="value">{% set ps = results.performance.score|default(0) %}<span style="color:{% if ps>=75 %}#10b981{% elif ps>=50 %}#f59e0b{% else %}#ef4444{% endif %}">{{ ps }}/100 {{ results.performance.grade|default('') }}</span></div></div>
                <div class="meta-item"><div class="label">Page Size</div><div class="value">{{ results.performance.total_page_size_formatted|default('N/A') }}</div></div>
                <div class="meta-item"><div class="label">Security</div><div class="value">{{ results.security.total|default(0) }} issues</div></div>
            </div>
        </header>

        <div class="tab-nav">
            <button class="tab-btn active" onclick="switchTab('performance')">⚡ Performance</button>
            <button class="tab-btn" onclick="switchTab('recon')">🕵️ Recon</button>
            <button class="tab-btn" onclick="switchTab('vuln')">☢️ Vuln Analysis</button>
            <button class="tab-btn" onclick="switchTab('security')">🛡️ Security</button>
            <button class="tab-btn" onclick="switchTab('deepapi')">🔍 Deep API</button>
            <button class="tab-btn" onclick="switchTab('idor')">🔀 IDOR</button>
            <button class="tab-btn" onclick="switchTab('screenshots')">📸 Screenshots</button>
            <button class="tab-btn" onclick="switchTab('exploration')">📊 Exploration</button>
            <button class="tab-btn" onclick="switchTab('microtests')">🧪 Micro-Tests</button>
            <button class="tab-btn" onclick="switchTab('errors')">🐞 Errors</button>
        </div>

        <!-- RECON TAB -->
        <div id="tab-recon" class="tab-content">
            {% set recon = results.recon or {} %}
            <section class="section">
                <h2>🕵️ Intelligence Gathering Report</h2>

                {# ── WAF / CDN Detection ── #}
                {% set waf = recon.waf or {} %}
                <div style="margin-bottom:28px">
                    <h3 style="margin-bottom:12px;font-size:1.1rem">🛡️ WAF / CDN Detection</h3>
                    {% if waf.detected %}
                    <div style="display:flex;align-items:center;gap:14px;padding:16px 20px;background:#fee2e2;border:1.5px solid #fca5a5;border-radius:12px">
                        <span style="font-size:2rem">🚨</span>
                        <div>
                            <div style="font-weight:700;font-size:1.1rem;color:#dc2626">{{ waf.name }}</div>
                            <div style="font-size:0.85rem;color:#991b1b;margin-top:2px">
                                Confidence: <strong>{{ waf.confidence }}</strong> &nbsp;|&nbsp; Method: {{ waf.method }}
                            </div>
                            {% if waf.details %}<div style="font-size:0.78rem;color:#7f1d1d;margin-top:4px;font-family:monospace">{{ waf.details }}</div>{% endif %}
                        </div>
                    </div>
                    {% else %}
                    <div style="display:flex;align-items:center;gap:14px;padding:16px 20px;background:#dcfce7;border:1.5px solid #86efac;border-radius:12px">
                        <span style="font-size:2rem">✅</span>
                        <div style="font-weight:600;color:#15803d">No WAF / CDN detected (or well-hidden)</div>
                    </div>
                    {% endif %}
                </div>

                {# ── Tech Stack ── #}
                {% set ts = recon.tech_stack or {} %}
                <div style="margin-bottom:28px">
                    <h3 style="margin-bottom:12px;font-size:1.1rem">🔬 Tech Stack</h3>
                    {% if ts %}
                    <div style="display:flex;flex-wrap:wrap;gap:16px">
                        {% set cat_icons = {'backend':'⚙️','frontend':'🎨','cms':'📝','server':'🖥️','cdn':'☁️','analytics':'📊'} %}
                        {% set cat_colors = {'backend':'#dbeafe','frontend':'#fce7f3','cms':'#fef3c7','server':'#f1f5f9','cdn':'#e0f2fe','analytics':'#f3e8ff'} %}
                        {% set cat_border = {'backend':'#93c5fd','frontend':'#f9a8d4','cms':'#fcd34d','server':'#cbd5e1','cdn':'#7dd3fc','analytics':'#d8b4fe'} %}
                        {% for cat, techs in ts.items() %}
                        <div style="background:{{ cat_colors.get(cat,'#f8fafc') }};border:1.5px solid {{ cat_border.get(cat,'#e2e8f0') }};border-radius:12px;padding:14px 18px;min-width:180px">
                            <div style="font-weight:700;font-size:0.75rem;text-transform:uppercase;color:#64748b;margin-bottom:8px">{{ cat_icons.get(cat,'🔧') }} {{ cat }}</div>
                            {% for t in techs %}
                            <div style="display:inline-block;background:white;border:1px solid #e2e8f0;border-radius:6px;padding:3px 10px;margin:2px;font-size:0.85rem;font-weight:500">{{ t }}</div>
                            {% endfor %}
                        </div>
                        {% endfor %}
                    </div>
                    {% else %}
                    <p style="color:var(--muted)">No tech stack signatures detected.</p>
                    {% endif %}
                </div>

                {# ── Subdomain Enumeration ── #}
                {% set subs = recon.subdomains or [] %}
                {% set sel = recon.selected_subdomains or [] %}
                <div>
                    <h3 style="margin-bottom:12px;font-size:1.1rem">🌐 Subdomain Enumeration</h3>
                    {% if subs %}
                    <p style="margin-bottom:10px;color:var(--muted);font-size:0.9rem">
                        Found <strong>{{ subs|selectattr('active')|list|length }}</strong> alive /
                        {{ subs|length }} total subdomains.
                        {% if sel %}<span style="color:#6366f1;font-weight:600">{{ sel|length }} selected for scan.</span>{% endif %}
                    </p>
                    <table style="width:100%;border-collapse:collapse;font-size:0.88rem">
                        <thead><tr style="background:#f8fafc;border-bottom:2px solid var(--border)">
                            <th style="text-align:left;padding:10px 14px">Subdomain</th>
                            <th style="text-align:center;padding:10px 14px;width:90px">Status</th>
                            <th style="text-align:center;padding:10px 14px;width:80px">Alive</th>
                            <th style="text-align:center;padding:10px 14px;width:90px">Selected</th>
                        </tr></thead>
                        <tbody>
                        {% for s in subs|sort(attribute='subdomain') %}
                        <tr style="border-bottom:1px solid var(--border);{% if s in sel %}background:#eef2ff;{% endif %}">
                            <td style="padding:9px 14px;font-family:monospace;font-size:0.82rem">{{ s.subdomain }}</td>
                            <td style="text-align:center;padding:9px 14px">
                                {% if s.status_code > 0 %}
                                <span style="padding:2px 8px;border-radius:5px;font-size:0.78rem;font-weight:600;background:{% if s.status_code < 400 %}#dcfce7;color:#15803d{% elif s.status_code < 500 %}#fef3c7;color:#92400e{% else %}#fee2e2;color:#991b1b{% endif %}">{{ s.status_code }}</span>
                                {% else %}-{% endif %}
                            </td>
                            <td style="text-align:center;padding:9px 14px">{% if s.active %}✅{% else %}❌{% endif %}</td>
                            <td style="text-align:center;padding:9px 14px">{% if s in sel %}🎯{% else %}-{% endif %}</td>
                        </tr>
                        {% endfor %}
                        </tbody>
                    </table>
                    {% else %}
                    <p style="color:var(--muted)">No subdomains enumerated.</p>
                    {% endif %}
                </div>
            </section>
        </div>

        <!-- VULN ANALYSIS TAB -->
        <div id="tab-vuln" class="tab-content">
            {% set vuln = results.vuln_analysis or {} %}
            <section class="section">
                <h2>☢️ Vulnerability Analysis (Phase 2)</h2>

                {# ── Context-Aware Payloads ── #}
                <div style="margin-bottom:28px;margin-top:16px">
                    <h3 style="margin-bottom:12px;font-size:1.1rem">🎯 Context-Aware Payload Injection</h3>
                    {% set payloads = vuln.payloads or [] %}
                    {% if payloads %}
                    <p style="margin-bottom:10px;color:var(--muted);font-size:0.9rem">Found <strong>{{ payloads|length }}</strong> injectable parameters with detectable HTML context.</p>
                    <table style="width:100%;border-collapse:collapse;font-size:0.88rem;background:white">
                        <thead><tr style="background:#f8fafc;border-bottom:2px solid var(--border)">
                            <th style="text-align:left;padding:10px 14px;width:30%">URL & Param</th>
                            <th style="text-align:left;padding:10px 14px;width:20%">Context</th>
                            <th style="text-align:left;padding:10px 14px">Suggested Payload</th>
                        </tr></thead>
                        <tbody>
                        {% for p in payloads %}
                        <tr style="border-bottom:1px solid var(--border)">
                            <td style="padding:10px 14px;word-break:break-all">
                                <div style="font-family:monospace;font-size:0.82rem;color:#333">{{ p.url }}</div>
                                <div style="margin-top:4px"><span style="background:#eef2ff;color:#4f46e5;padding:2px 6px;border-radius:4px;font-weight:600;font-size:0.75rem">?{{ p.parameter }}=</span></div>
                            </td>
                            <td style="padding:10px 14px">
                                {% set ctx_color = '#d97706' %}
                                {% if p.context in ['script_string','href_attribute'] %}{% set ctx_color = '#dc2626' %}{% endif %}
                                <span style="font-weight:600;color:{{ ctx_color }}">{{ p.context }}</span>
                            </td>
                            <td style="padding:10px 14px">
                                <code style="background:#f1f5f9;padding:4px 8px;border-radius:4px;color:#0f172a;display:block;white-space:pre-wrap;word-break:break-all">{{ p.payload }}</code>
                            </td>
                        </tr>
                        {% endfor %}
                        </tbody>
                    </table>
                    {% else %}
                    <div style="padding:16px;background:#f8fafc;border:1px solid var(--border);border-radius:8px;color:var(--muted)">No injectable parameters mapped to a vulnerable context.</div>
                    {% endif %}
                </div>

                {# ── Smart Parameter Discovery ── #}
                <div style="margin-bottom:28px">
                    <h3 style="margin-bottom:12px;font-size:1.1rem">🔎 Smart Parameter Discovery (Hidden Params)</h3>
                    {% set hidden = vuln.hidden_params or [] %}
                    {% if hidden %}
                    <p style="margin-bottom:10px;color:var(--muted);font-size:0.9rem">Fuzzed wordlist discovered <strong>{{ hidden|length }}</strong> active hidden parameters based on response size delta.</p>
                    <table style="width:100%;border-collapse:collapse;font-size:0.88rem;background:white">
                        <thead><tr style="background:#f8fafc;border-bottom:2px solid var(--border)">
                            <th style="text-align:left;padding:10px 14px">URL</th>
                            <th style="text-align:center;padding:10px 14px;width:120px">Parameter</th>
                            <th style="text-align:right;padding:10px 14px;width:100px">Base Size</th>
                            <th style="text-align:right;padding:10px 14px;width:100px">New Size</th>
                            <th style="text-align:right;padding:10px 14px;width:100px">Delta</th>
                        </tr></thead>
                        <tbody>
                        {% for h in hidden %}
                        <tr style="border-bottom:1px solid var(--border)">
                            <td style="padding:10px 14px;font-family:monospace;font-size:0.8rem;color:#475569;word-break:break-all">{{ h.url }}</td>
                            <td style="text-align:center;padding:10px 14px"><span style="background:#fef3c7;color:#b45309;padding:2px 8px;border-radius:12px;font-weight:600;font-size:0.75rem">{{ h.parameter }}</span></td>
                            <td style="text-align:right;padding:10px 14px;font-family:monospace;color:var(--muted)">{{ h.baseline_len }} B</td>
                            <td style="text-align:right;padding:10px 14px;font-family:monospace;color:var(--muted)">{{ h.found_len }} B</td>
                            <td style="text-align:right;padding:10px 14px;font-family:monospace;font-weight:600;color:#10b981">+{{ h.delta_pct }}%</td>
                        </tr>
                        {% endfor %}
                        </tbody>
                    </table>
                    {% else %}
                    <div style="padding:16px;background:#f8fafc;border:1px solid var(--border);border-radius:8px;color:var(--muted)">No active hidden parameters discovered via fuzzing.</div>
                    {% endif %}
                </div>

                {# ── Local Storage & JWT Analysis ── #}
                <div>
                    <h3 style="margin-bottom:12px;font-size:1.1rem">🔐 Local Storage & JWT Analysis</h3>
                    {% set storage = vuln.storage_jwt or [] %}
                    {% if storage %}
                    <p style="margin-bottom:10px;color:var(--muted);font-size:0.9rem">Found <strong>{{ storage|length }}</strong> sensitive/insecure items in browser storage.</p>
                    <div style="display:flex;flex-direction:column;gap:12px">
                        {% for s in storage %}
                        <div style="background:white;border:1px solid {% if 'CRITICAL' in s.issues|join %}#fca5a5{% else %}#fde047{% endif %};border-radius:8px;padding:16px">
                            <div style="display:flex;justify-content:space-between;margin-bottom:10px">
                                <div>
                                    <span style="font-weight:700;font-size:0.95rem;color:#1e293b">{{ s.type }}</span>
                                    <span style="color:var(--muted);font-size:0.85rem;margin-left:8px">in {{ s.storage }}</span>
                                </div>
                                <div style="font-family:monospace;background:#f1f5f9;padding:2px 8px;border-radius:4px;font-size:0.8rem">{{ s.key }}</div>
                            </div>
                            
                            {% if s.type == "JWT" %}
                            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px;background:#f8fafc;padding:10px;border-radius:6px;font-size:0.85rem">
                                <div><span style="color:var(--muted)">Alg:</span> <strong>{{ s.alg }}</strong></div>
                                <div><span style="color:var(--muted)">Sub:</span> <strong>{{ s.subject }}</strong></div>
                            </div>
                            {% endif %}
                            
                            <div style="margin-bottom:12px">
                                {% for issue in s.issues %}
                                <div style="color:{% if 'CRITICAL' in issue %}#dc2626{% else %}#b45309{% endif %};font-size:0.85rem;font-weight:600;margin-bottom:4px">{{ issue }}</div>
                                {% endfor %}
                            </div>
                            
                            <div style="font-family:monospace;font-size:0.75rem;color:#64748b;background:#f8fafc;padding:10px;border-radius:6px;word-break:break-all;border:1px solid #e2e8f0">
                                {{ s.preview }}...
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                    {% else %}
                    <div style="padding:16px;background:#dcfce7;border:1px solid #86efac;border-radius:8px;color:#15803d;font-weight:600">✅ No sensitive data or insecure JWTs found in browser storage.</div>
                    {% endif %}
                </div>
            </section>
        </div>

        <!-- PERFORMANCE TAB -->
        <div id="tab-performance" class="tab-content active">
            {% set perf = results.performance or {} %}
            <section class="section"><h2>⚡ Performance Score</h2><div class="perf-score">{% set ps = perf.score|default(0) %}<div class="perf-circle" style="border-color:{% if ps>=75 %}#10b981{% elif ps>=50 %}#f59e0b{% else %}#ef4444{% endif %};color:{% if ps>=75 %}#10b981{% elif ps>=50 %}#f59e0b{% else %}#ef4444{% endif %}">{{ ps }}</div><div class="perf-grade" style="color:{% if ps>=75 %}#10b981{% elif ps>=50 %}#f59e0b{% else %}#ef4444{% endif %}">Grade: {{ perf.grade|default('?') }}</div></div></section>
            <section class="section"><h2>📈 Core Web Vitals</h2>{% set wv = perf.web_vitals or {} %}<div class="vitals-grid"><div class="vital-card"><div class="vital-value {{ 'good' if wv.ttfb|default(0)<400 else 'warn' if wv.ttfb|default(0)<800 else 'bad' }}">{{ wv.ttfb_formatted|default('?') }}</div><div class="vital-label">TTFB</div></div><div class="vital-card"><div class="vital-value {{ 'good' if wv.fcp|default(0)<1800 else 'warn' if wv.fcp|default(0)<2500 else 'bad' }}">{{ wv.fcp_formatted|default('?') }}</div><div class="vital-label">FCP</div></div><div class="vital-card"><div class="vital-value {{ 'good' if wv.lcp|default(0)<2500 else 'warn' if wv.lcp|default(0)<4000 else 'bad' }}">{{ wv.lcp_formatted|default('?') }}</div><div class="vital-label">LCP</div></div><div class="vital-card"><div class="vital-value {{ 'good' if wv.cls|default(0)<0.1 else 'warn' if wv.cls|default(0)<0.25 else 'bad' }}">{{ wv.cls|default('?') }}</div><div class="vital-label">CLS</div></div></div></section>
            <section class="section"><h2>📊 Resource Breakdown</h2>{% set rb = perf.resource_breakdown or {} %}<div class="stats"><div class="stat-card"><div class="number">{{ perf.total_requests|default(0) }}</div><div class="label">Requests</div></div><div class="stat-card"><div class="number">{{ perf.total_page_size_formatted|default('0') }}</div><div class="label">Total Size</div></div><div class="stat-card"><div class="number">{{ rb.scripts.size_formatted|default('0') }}</div><div class="label">JS</div></div><div class="stat-card"><div class="number">{{ rb.stylesheets.size_formatted|default('0') }}</div><div class="label">CSS</div></div><div class="stat-card"><div class="number">{{ rb.images.size_formatted|default('0') }}</div><div class="label">Images</div></div><div class="stat-card"><div class="number">{{ rb.fonts.size_formatted|default('0') }}</div><div class="label">Fonts</div></div></div></section>
            {% if perf.dom_stats %}<section class="section"><h2>🏗️ DOM Complexity</h2><div class="stats"><div class="stat-card"><div class="number">{{ perf.dom_stats.elements|default(0) }}</div><div class="label">Elements</div></div><div class="stat-card"><div class="number">{{ perf.dom_stats.depth|default(0) }}</div><div class="label">Max Depth</div></div><div class="stat-card"><div class="number">{{ perf.dom_stats.scripts|default(0) }}</div><div class="label">Script Tags</div></div></div></section>{% endif %}
            {% if perf.slowest_resources %}<section class="section"><div class="collapsible"><div class="collapsible-header" onclick="toggleCollapsible(this)">🐌 Slowest Resources ({{ perf.slowest_resources|length }}) <span class="arrow">▼</span></div><div class="collapsible-body"><table><thead><tr><th>Resource</th><th>Type</th><th>Duration</th><th>Size</th></tr></thead><tbody>{% for r in perf.slowest_resources[:15] %}<tr><td style="word-break:break-all;font-size:0.8rem">{{ r.url[:80] }}</td><td>{{ r.type }}</td><td class="warn">{{ r.duration_ms }}ms</td><td>{{ r.size_formatted }}</td></tr>{% endfor %}</tbody></table></div></div></section>{% endif %}
            {% if perf.largest_resources %}<section class="section"><div class="collapsible"><div class="collapsible-header" onclick="toggleCollapsible(this)">📦 Largest Resources ({{ perf.largest_resources|length }}) <span class="arrow">▼</span></div><div class="collapsible-body"><table><thead><tr><th>Resource</th><th>Type</th><th>Size</th></tr></thead><tbody>{% for r in perf.largest_resources[:15] %}<tr><td style="word-break:break-all;font-size:0.8rem">{{ r.url[:80] }}</td><td>{{ r.type }}</td><td>{{ r.size_formatted }}</td></tr>{% endfor %}</tbody></table></div></div></section>{% endif %}
            {% if perf.third_party_domains %}<section class="section"><div class="collapsible"><div class="collapsible-header" onclick="toggleCollapsible(this)">🌐 Third-Party Domains ({{ perf.third_party_domains|length }}) <span class="arrow">▼</span></div><div class="collapsible-body"><table><thead><tr><th>Domain</th><th>Requests</th><th>Size</th></tr></thead><tbody>{% for domain, data in perf.third_party_domains.items() %}<tr><td>{{ domain }}</td><td>{{ data.count }}</td><td>{{ data.size }}</td></tr>{% endfor %}</tbody></table></div></div></section>{% endif %}
            {% if perf.recommendations %}<section class="section"><h2>💡 Recommendations ({{ perf.recommendations|length }})</h2>{% for rec in perf.recommendations %}<div class="rec-card"><div class="rec-priority" style="color:{% if rec.priority=='high' %}var(--red){% elif rec.priority=='medium' %}var(--yellow){% else %}var(--brand){% endif %}">{{ rec.priority }}</div><strong>{{ rec.title }}</strong><div style="font-size:0.85rem;color:var(--muted);margin-top:4px">{{ rec.description }}</div></div>{% endfor %}</section>{% endif %}
        </div>

        <!-- SECURITY TAB -->
        <div id="tab-security" class="tab-content">
            {% set sec = results.security or {} %}
            <section class="section"><h2>🛡️ Security Findings ({{ sec.total or 0 }})</h2>
            {% if sec.total %}
            <div class="stats" style="margin-bottom:20px"><div class="stat-card"><div class="number" style="color:var(--critical)">{{ sec.critical or 0 }}</div><div class="label">Critical</div></div><div class="stat-card"><div class="number" style="color:var(--high)">{{ sec.high or 0 }}</div><div class="label">High</div></div><div class="stat-card"><div class="number" style="color:var(--medium)">{{ sec.medium or 0 }}</div><div class="label">Medium</div></div><div class="stat-card"><div class="number" style="color:var(--low)">{{ sec.low or 0 }}</div><div class="label">Low</div></div></div>
            {% set ch = sec.findings|selectattr('severity','in',['critical','high'])|list %}
            {% if ch %}<div class="collapsible open"><div class="collapsible-header" onclick="toggleCollapsible(this)">🚨 Critical & High ({{ ch|length }}) <span class="arrow">▼</span></div><div class="collapsible-body">{% for f in ch %}<div class="finding-card severity-{{ f.severity }}"><div class="finding-header"><div class="finding-title">{{ f.title }} {% if f.cvss_score %}<span style="background:#1e293b;color:white;padding:2px 8px;border-radius:12px;font-size:0.75rem;margin-left:8px">CVSS {{ f.cvss_score }}</span>{% endif %}</div><span class="finding-severity sev-{{ f.severity }}">{{ f.severity }}</span></div><div>{{ f.description }}</div><div class="finding-location">📍 <a href="{{ f.location }}" target="_blank">{{ f.location[:100] }}</a></div>{% if f.poc %}<div style="margin-top:12px"><strong style="font-size:0.85rem">Auto-Generated PoC:</strong><code style="display:block;background:#0f172a;color:#10b981;padding:8px 12px;border-radius:6px;font-size:0.8rem;margin-top:4px;word-break:break-all">{{ f.poc }}</code></div>{% endif %}{% if f.evidence %}<div class="finding-evidence">🔍 {{ f.evidence[:200] }}</div>{% endif %}{% if f.recommendation %}<div class="finding-recommendation">💡 {{ f.recommendation }}</div>{% endif %}{% if f.screenshot %}<div class="finding-screenshot"><img src="{{ f.screenshot }}" loading="lazy" onerror="this.parentElement.style.display='none'"></div>{% endif %}</div>{% endfor %}</div></div>{% endif %}
            {% else %}<p style="text-align:center;padding:40px;color:var(--green);font-size:1.2rem">✅ No security issues!</p>{% endif %}
            </section>
        </div>

        <!-- DEEP API TAB -->
        <div id="tab-deepapi" class="tab-content">
            {% set apis = results.exploration.api_endpoints or [] %}
            <section class="section"><h2>🌐 Hidden API Endpoints ({{ apis|length }})</h2><p style="margin-bottom:16px;color:var(--muted)">Discovered from JS bundles, source maps, and runtime requests.</p>
            {% for ep in apis %}<div class="api-item">{{ ep }}</div>{% else %}<p style="text-align:center;padding:40px;color:var(--muted)">No hidden API endpoints discovered.</p>{% endfor %}</section>
        </div>

        <!-- IDOR TAB -->
        <div id="tab-idor" class="tab-content">
            {% set idor_findings = results.idor or [] %}
            <section class="section"><h2>🔀 IDOR / BOLA Findings ({{ idor_findings|length }})</h2>
            {% for f in idor_findings %}<div class="finding-card severity-{{ f.severity }}"><div class="finding-header"><div class="finding-title">{{ f.title }} {% if f.cvss_score %}<span style="background:#1e293b;color:white;padding:2px 8px;border-radius:12px;font-size:0.75rem;margin-left:8px">CVSS {{ f.cvss_score }}</span>{% endif %}</div><span class="finding-severity sev-{{ f.severity }}">{{ f.severity }}</span></div><div>{{ f.description }}</div><div class="finding-location">📍 {{ f.location[:100] }}</div>{% if f.poc %}<div style="margin-top:12px"><strong style="font-size:0.85rem">Auto-Generated PoC:</strong><code style="display:block;background:#0f172a;color:#10b981;padding:8px 12px;border-radius:6px;font-size:0.8rem;margin-top:4px;word-break:break-all">{{ f.poc }}</code></div>{% endif %}{% if f.evidence %}<div class="finding-evidence">🔍 {{ f.evidence[:200] }}</div>{% endif %}</div>
            {% else %}<p style="text-align:center;padding:40px;color:var(--muted)">No IDOR issues found, or IDOR testing was not enabled.</p>{% endfor %}</section>
        </div>

        <!-- SCREENSHOTS TAB -->
        <div id="tab-screenshots" class="tab-content">
            {% set ss = results.exploration.screenshots or [] %}
            <section class="section"><h2>📸 Screenshots ({{ ss|length }})</h2>
            {% if ss %}<div class="screenshot-grid">{% for s in ss %}<div class="screenshot-card"><img src="{{ s.screenshot }}" loading="lazy" onerror="this.parentElement.style.display='none'"><div class="caption"><strong>{{ s.title[:60] or 'Screenshot' }}</strong><br>{{ s.url[:80] }}</div></div>{% endfor %}</div>{% else %}<p style="text-align:center;padding:40px;color:var(--muted)">No screenshots captured.</p>{% endif %}</section>
        </div>

        <!-- EXPLORATION TAB -->
        <div id="tab-exploration" class="tab-content">
            {% set exp = results.exploration or {} %}
            <section class="section"><h2>📊 Exploration Summary</h2><div class="stats"><div class="stat-card"><div class="number">{{ exp.pages_explored or 0 }}</div><div class="label">Pages Visited</div></div><div class="stat-card"><div class="number">{{ exp.components|length if exp.components else 0 }}</div><div class="label">Components Found</div></div><div class="stat-card"><div class="number">{{ (exp.api_endpoints or [])|length }}</div><div class="label">API Endpoints</div></div></div></section>
            {% if exp.components %}<section class="section"><h2>🧩 Detected Components</h2><div class="component-tags">{% for name, count in exp.components.items() %}<span class="component-tag">{{ name }} ({{ count }})</span>{% endfor %}</div></section>{% endif %}
            {% if exp.pages %}<section class="section"><h2>📄 Discovered Pages ({{ exp.pages|length }})</h2><table><thead><tr><th>URL</th><th>Title</th></tr></thead><tbody>{% for p in exp.pages[:50] %}<tr><td style="word-break:break-all;font-size:0.85rem"><a href="{{ p.url }}" target="_blank">{{ p.url[:80] }}</a></td><td>{{ p.title[:60] or '—' }}</td></tr>{% endfor %}</tbody></table></section>{% endif %}
        </div>

        <!-- MICRO-TESTS TAB -->
        <div id="tab-microtests" class="tab-content">
            {% set mt = results.exploration.micro_tests or [] %}
            <section class="section"><h2>🧪 Micro-Interaction Tests ({{ mt|length }})</h2>
            {% if mt %}<table><thead><tr><th>Test</th><th>Status</th><th>Details</th></tr></thead><tbody>{% for t in mt %}<tr><td><strong>{{ t.name }}</strong></td><td>{% if t.status=='tested' %}<span class="tested">✅ Tested</span>{% elif t.status=='error' %}<span class="error">❌ Error</span>{% elif t.status=='found' %}🔍 Found{% else %}{{ t.status }}{% endif %}</td><td style="font-size:0.8rem">{{ t.details[:80] }}</td></tr>{% endfor %}</tbody></table>{% else %}<p style="text-align:center;padding:40px;color:var(--muted)">No micro-interaction tests performed.</p>{% endif %}</section>
        </div>

        <!-- ERRORS TAB -->
        <div id="tab-errors" class="tab-content">
            {% set es = results.errors_summary or {} %}
            <section class="section"><h2>🐞 Errors ({{ es.total or 0 }})</h2>
            {% if es.errors %}{% for e in es.errors[:50] %}<div class="error-item"><strong>#{{ e.id }} {{ e.type }}</strong>: {{ e.message[:200] }}<div style="font-size:0.7rem;color:var(--muted);margin-top:4px">📄 {{ e.page_url[:80] }}{% if e.extra.line %} | 📍 L:{{ e.extra.line }}{% endif %}</div></div>{% endfor %}{% else %}<p style="text-align:center;padding:40px;color:var(--green)">✅ No errors recorded.</p>{% endif %}</section>
        </div>

        <footer class="footer">
            <div style="font-weight:700">🦊 {{ results.app_name|default('Lilo Tester') }} v{{ results.version|default('5.0.0') }}</div>
            <div style="opacity:0.8;margin-top:4px">Deep DAST • Advanced Performance • Security • IDOR</div>
        </footer>
    </main>
    <script>
        function switchTab(n){
            document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c=>c.classList.remove('active'));
            document.getElementById('tab-'+n).classList.add('active');
            event.target.classList.add('active');
        }
        function toggleCollapsible(h){
            h.parentElement.classList.toggle('open');
        }
    </script>
</body>
</html>
"""

# ═══════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════

async def main_async():
    parser = argparse.ArgumentParser(
        description=f"Advanced Web Security Scanner & Performance Analyzer (v{APP_VERSION})",
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False
    )
    parser.add_argument("-h", "--help", action="store_true", help="show this help message and exit")
    parser.add_argument("--url", "-u", required=True, help="Target URL to test (e.g., https://target.com)")
    parser.add_argument("--login-url", "-l", help="Custom login URL (if different from target URL)")
    parser.add_argument("--output", "-o", default="lilo_reports", help="Directory to save HTML/PDF reports (default: lilo_reports)")
    parser.add_argument("--enable-mass-assign", action="store_true", help="Enable Business Logic & Mass Assignment testing (WARNING: Destructive, may pollute database!)")
    parser.add_argument("--mode", "-m", choices=["dashboard","public","performance","security","quick"], default="dashboard", help="Scan mode: dashboard (Full Auth), public (No Auth), quick (No Crawler), etc.")
    parser.add_argument("--max-pages", type=int, default=50, help="Maximum number of pages to crawl (default: 50)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode (no GUI)")
    parser.add_argument("--no-login", action="store_true", help="Skip the login process even if dashboard mode is active")
    parser.add_argument("--no-security", action="store_true", help="Skip the Vulnerability Analysis phase (only perform crawling & performance)")
    parser.add_argument("--no-open", action="store_true", help="Do not open the report automatically when finished")
    parser.add_argument("--enable-idor", action="store_true", help="Enable IDOR/BOLA Engine (requires --idor-user)")
    parser.add_argument("--idor-user", help="Victim credentials for IDOR testing in user:password format")
    parser.add_argument("--oob-server", help="Custom Interactsh server URL (default: public interact.sh, fallback: local server)")
    parser.add_argument("--deep-enum", action="store_true", help="Enable advanced Subdomain Enumeration (*.sub.domain.com)")
    parser.add_argument("--ignore-waf", action="store_true", help="Ignore active WAF detection and force execution (risk of IP ban)")
    parser.add_argument("--xss-wordlist", type=str, help="Path to custom XSS payloads")
    parser.add_argument("--sqli-wordlist", type=str, help="Path to custom SQLi payloads")
    parser.add_argument("--proxy", type=str, help="Upstream proxy URL (e.g., http://127.0.0.1:8080)")
    parser.add_argument("--header", action="append", help="Custom headers (e.g., 'Authorization: Bearer xxx')", default=[])
    parser.add_argument("--rate-limit", type=int, default=0, help="Max requests per second for fuzzing (0 = unlimited)")
    parser.add_argument("--sarif", action="store_true", help="Export report to SARIF format")
    if "-h" in sys.argv or "--help" in sys.argv:
        console.print(get_banner())
        parser.print_help()
        sys.exit(0)
        
    args = parser.parse_args()
    idor_creds = None
    if args.idor_user:
        parts = args.idor_user.split(":",1)
        if len(parts)==2: idor_creds = {"username":parts[0],"password":parts[1]}
    tester = LiloTester(
        url=args.url, output_dir=args.output, mode=args.mode,
        max_pages=args.max_pages, headless=args.headless,
        custom_login_url=args.login_url, open_report=not args.no_open,
        skip_login=args.no_login or args.mode in ["public","performance","security"],
        enable_security=not args.no_security,
        enable_idor=args.enable_idor, idor_user_b_creds=idor_creds,
        oob_server=args.oob_server,
        deep_enum=args.deep_enum,
        ignore_waf=args.ignore_waf,
        enable_mass_assign=args.enable_mass_assign,
        xss_wordlist=args.xss_wordlist,
        sqli_wordlist=args.sqli_wordlist,
        proxy=args.proxy,
        custom_headers=args.header,
        rate_limit=args.rate_limit,
        export_sarif=args.sarif
    )
    results = await tester.run()

    critical_count = results.get("security", {}).get("critical", 0)
    high_count = results.get("security", {}).get("high", 0)
    
    if critical_count > 0 or high_count > 0:
        console.print(f"\n[bold red]🚨 DEVSECOPS ALERT: Ditemukan {critical_count} Critical & {high_count} High issues![/bold red]")
        console.print("[red]Exiting with code 1 agar pipeline CI/CD gagal.[/red]")
        sys.exit(1)

def cli():
    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/yellow]")

if __name__ == "__main__":
    cli()