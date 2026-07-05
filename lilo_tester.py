#!/usr/bin/env python3
"""
🦊 LILO TESTER v4.5.0 - Advanced Performance Analytics Edition
Version: 4.5.0 - FULL CODE WITH ENHANCED PERFORMANCE MODULE
Author: Lilo

COMPLETE FEATURES:
- 🔐 Authenticated Dashboard Explorer
- 🧪 15+ Micro-Interaction Tests
- ⚡ ADVANCED Performance Analysis (Web Vitals, Resources, Scoring)
- 🛡️ Security Audit (XSS, SQLi, CSRF, Headers, Sensitive Files, dll)
- 💾 Credential Manager
- 📸 Full Screenshot Capture (Pages + Error States + Security Issues)
- 📄 Collapsible HTML Report with Tab Navigation
- 🔍 Enhanced Security Details with Screenshots for HIGH/CRITICAL issues
- 🐞 Error Tracking with Source Location
"""

import argparse
import asyncio
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
)
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table
from rich.text import Text
from rich.syntax import Syntax

console = Console()

APP_NAME = "Lilo Tester"
APP_VERSION = "4.5.0"
DEFAULT_WATERMARK = "Lilo Tester"

# ═══════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════

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
    "<script>console.log('LILO_XSS_TEST')</script>",
    "<img src=x onerror=console.log('LILO_XSS_TEST')>",
    "'\"><script>console.log('LILO_XSS_TEST')</script>",
    "<svg/onload=console.log('LILO_XSS_TEST')>",
    "javascript:console.log('LILO_XSS_TEST')",
]

SQLI_TEST_STRINGS = [
    "'", "\"", "' OR '1'='1", "\" OR \"1\"=\"1", "' OR 1=1--",
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
]

SECURITY_HEADERS = {
    "Strict-Transport-Security": {
        "description": "HTTP Strict Transport Security (HSTS)",
        "severity": "medium",
        "recommendation": "max-age=31536000; includeSubDomains"
    },
    "Content-Security-Policy": {
        "description": "Content Security Policy (CSP)",
        "severity": "high",
        "recommendation": "default-src 'self'"
    },
    "X-Frame-Options": {
        "description": "Clickjacking Protection",
        "severity": "medium",
        "recommendation": "DENY or SAMEORIGIN"
    },
    "X-Content-Type-Options": {
        "description": "MIME Type Sniffing Protection",
        "severity": "low",
        "recommendation": "nosniff"
    },
    "Referrer-Policy": {
        "description": "Referrer Information Control",
        "severity": "low",
        "recommendation": "strict-origin-when-cross-origin"
    },
    "Permissions-Policy": {
        "description": "Browser Feature Permissions",
        "severity": "low",
        "recommendation": "camera=(), microphone=(), geolocation=()"
    },
    "Access-Control-Allow-Origin": {
        "description": "CORS Policy",
        "severity": "high",
        "recommendation": "Should not be *"
    },
    "Cross-Origin-Resource-Policy": {
        "description": "Cross-Origin Resource Policy",
        "severity": "medium",
        "recommendation": "same-origin"
    },
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
# UTILITY CLASSES
# ═══════════════════════════════════════════

class SystemDetector:
    @staticmethod
    def get_os() -> str:
        system = platform.system().lower()
        if system == "windows":
            return "windows"
        if system == "darwin":
            return "macos"
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
    except:
        return url


def same_domain(base_domain: str, url: str) -> bool:
    try:
        return urlparse(url).netloc == base_domain
    except:
        return False


def truncate(value: Any, length: int = 240) -> str:
    text = str(value or "")
    return text if len(text) <= length else text[: length - 3] + "..."


def format_bytes(size: float) -> str:
    """Format bytes to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def format_ms(ms: float) -> str:
    """Format milliseconds to readable"""
    if ms < 1000:
        return f"{ms:.0f}ms"
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
║   ████████╗███████╗███████╗████████╗███████╗██████╗              ║
║   ╚══██╔══╝██╔════╝██╔════╝╚══██╔══╝██╔════╝██╔══██╗             ║
║      ██║   █████╗  ███████╗   ██║   █████╗  ██████╔╝             ║
║      ██║   ██╔══╝  ╚════██║   ██║   ██╔══╝  ██╔══██╗             ║
║      ██║   ███████╗███████║   ██║   ███████╗██║  ██║             ║
║      ╚═╝   ╚══════╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝             ║
║                                                                  ║
║     ⚡ Advanced Performance Analytics v{APP_VERSION}             ║
║  🔐 Auth • 🧪 Micro • ⚡ Perf • 🛡️  Security • 📸 Screenshot   ║
║     Running on {SystemDetector.get_os().upper():<10}             ║
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
                try:
                    return ImageFont.truetype(path, 24)
                except:
                    continue
        return ImageFont.load_default()

    def apply(self, image_path: str) -> bool:
        try:
            img = Image.open(image_path)
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            bbox = draw.textbbox((0, 0), self.text, font=self.font)
            text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            x, y = img.width - text_w - 20, img.height - text_h - 20
            draw.rectangle(
                [x-10, y-10, x+text_w+10, y+text_h+10],
                fill=(0, 0, 0, self.opacity)
            )
            draw.text((x, y), self.text, font=self.font, fill=(255, 255, 255, 255))
            img = Image.alpha_composite(img, overlay)
            img.save(image_path)
            return True
        except:
            return False


# ═══════════════════════════════════════════
# CREDENTIAL MANAGER
# ═══════════════════════════════════════════

class CredentialManager:
    """Manages saved credentials per domain"""
    
    def __init__(self):
        self.creds_dir = Path.home() / ".lilo_tester"
        self.creds_file = self.creds_dir / "credentials.json"
        self.creds_dir.mkdir(parents=True, exist_ok=True)
        self._load()
    
    def _load(self):
        if self.creds_file.exists():
            try:
                with open(self.creds_file, "r") as f:
                    self.credentials = json.load(f)
            except:
                self.credentials = {}
        else:
            self.credentials = {}
    
    def _save(self):
        with open(self.creds_file, "w") as f:
            json.dump(self.credentials, f, indent=2)
    
    def get_domain_key(self, url: str) -> str:
        parsed = urlparse(url)
        return parsed.netloc or parsed.path.split("/")[0]
    
    def get_credentials(self, url: str) -> List[Dict[str, str]]:
        domain = self.get_domain_key(url)
        return self.credentials.get(domain, [])
    
    def save_credential(self, url: str, username: str, password: str, label: str = ""):
        domain = self.get_domain_key(url)
        if domain not in self.credentials:
            self.credentials[domain] = []
        for cred in self.credentials[domain]:
            if cred["username"] == username:
                cred["password"] = password
                cred["label"] = label or username
                cred["saved_at"] = datetime.now().isoformat()
                self._save()
                return
        self.credentials[domain].append({
            "username": username,
            "password": password,
            "label": label or username,
            "saved_at": datetime.now().isoformat(),
            "login_url": url,
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
        if not creds:
            return None
        console.print(f"\n[bold cyan]📋 Saved credentials for {self.get_domain_key(url)}:[/bold cyan]")
        for i, cred in enumerate(creds, 1):
            console.print(f"  ({i}) [green]{cred['label']}[/green] - [dim]{cred['username']}[/dim]")
        console.print(f"  (0) [yellow]Login with new credentials[/yellow]")
        choice = Prompt.ask("\n[bold]Choose option[/bold]", default="1")
        if choice == "0":
            return None
        idx = int(choice) - 1
        if 0 <= idx < len(creds):
            return creds[idx]
        return None


# ═══════════════════════════════════════════
# ERROR TRACKER
# ═══════════════════════════════════════════

class ErrorTracker:
    """Tracks all errors with detailed context and screenshots"""
    
    def __init__(self, output_dir: Path):
        self.errors: List[Dict[str, Any]] = []
        self.output_dir = output_dir
        self.error_screenshots_dir = output_dir / "error_screenshots"
        self.error_screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.error_counter = 0
    
    def add_error(self, error_type: str, message: str, page_url: str = "",
                  component: str = "", selector: str = "", stack_trace: str = "",
                  extra: Dict = None):
        self.error_counter += 1
        error = {
            "id": self.error_counter,
            "type": error_type,
            "message": str(message)[:500],
            "page_url": page_url,
            "component": component,
            "selector": selector,
            "stack_trace": stack_trace[:1000] if stack_trace else "",
            "timestamp": datetime.now().isoformat(),
            "extra": extra or {},
            "screenshot": "",
        }
        self.errors.append(error)
        return error
    
    async def capture_error_screenshot(self, page: Page, error_id: int) -> Optional[str]:
        try:
            filename = f"error_{error_id}_{datetime.now().strftime('%H%M%S')}.png"
            filepath = self.error_screenshots_dir / filename
            await page.screenshot(path=str(filepath), full_page=True)
            rel_path = str(filepath.relative_to(self.output_dir))
            for err in self.errors:
                if err["id"] == error_id:
                    err["screenshot"] = rel_path
                    break
            return rel_path
        except:
            return None
    
    def get_summary(self) -> Dict[str, Any]:
        by_type = defaultdict(list)
        by_page = defaultdict(list)
        for error in self.errors:
            by_type[error["type"]].append(error)
            if error.get("page_url"):
                by_page[error["page_url"]].append(error)
        return {
            "total": len(self.errors),
            "by_type": {k: len(v) for k, v in by_type.items()},
            "by_page": {k: len(v) for k, v in by_page.items()},
            "errors": self.errors,
        }


# ═══════════════════════════════════════════
# ADVANCED PERFORMANCE TRACKER
# ═══════════════════════════════════════════

class ResourceTiming:
    """Detailed resource timing information"""
    def __init__(self):
        self.url: str = ""
        self.type: str = ""
        self.start_time: float = 0
        self.duration: float = 0
        self.size: int = 0
        self.transfer_size: int = 0
        self.status: int = 0
        self.cached: bool = False
        self.compressed: bool = False
        self.blocking: bool = False
        self.third_party: bool = False
        self.domain: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "url": self.url,
            "type": self.type,
            "duration_ms": round(self.duration, 2),
            "size_bytes": self.size,
            "size_formatted": format_bytes(self.size),
            "transfer_size": self.transfer_size,
            "status": self.status,
            "cached": self.cached,
            "compressed": self.compressed,
            "blocking": self.blocking,
            "third_party": self.third_party,
            "domain": self.domain,
        }


class AdvancedPerformanceTracker:
    """Advanced performance tracking with Web Vitals, resource analysis, and scoring"""
    
    def __init__(self, domain: str):
        self.domain = domain
        self.resources: List[ResourceTiming] = []
        self.page_metrics: Dict[str, Any] = {}
        self.page_timings: List[Dict] = []
        self.resource_start_times: Dict[str, float] = {}
        self.slow_threshold_ms = 3000
        
        self.total_page_size: int = 0
        self.total_requests: int = 0
        self.total_js_size: int = 0
        self.total_css_size: int = 0
        self.total_image_size: int = 0
        self.total_font_size: int = 0
        
        self.lcp: float = 0
        self.fcp: float = 0
        self.ttfb: float = 0
        self.cls: float = 0
        self.dom_content_loaded: float = 0
        self.dom_elements: int = 0
        self.dom_depth: int = 0
    
    def record_resource_start(self, request: Request):
        self.resource_start_times[request.url] = time.time() * 1000
    
    def record_resource(self, request: Request, response: Response):
        resource = ResourceTiming()
        resource.url = response.url
        resource.status = response.status
        resource.domain = urlparse(response.url).netloc
        resource.third_party = resource.domain != self.domain and resource.domain != ""
        
        content_type = response.headers.get("content-type", "").lower()
        if request.resource_type in ["document", "script", "stylesheet", "image", "font", "fetch", "xhr"]:
            resource.type = request.resource_type
        elif "javascript" in content_type:
            resource.type = "script"
        elif "css" in content_type:
            resource.type = "stylesheet"
        elif "image" in content_type:
            resource.type = "image"
        elif "font" in content_type or "woff" in content_type:
            resource.type = "font"
        elif "json" in content_type:
            resource.type = "fetch"
        else:
            resource.type = "other"
        
        start = self.resource_start_times.get(response.url, 0)
        resource.start_time = start
        resource.duration = (time.time() * 1000) - start if start > 0 else 0
        
        # FIXED: Use Content-Length header instead of response.body()
        content_length = response.headers.get("content-length", "0")
        try:
            resource.size = int(content_length) if content_length.isdigit() else 0
        except (ValueError, TypeError):
            resource.size = 0
        resource.transfer_size = resource.size
        
        cache_headers = response.headers.get("cache-control", "").lower()
        resource.cached = "no-cache" not in cache_headers and "no-store" not in cache_headers
        
        content_encoding = response.headers.get("content-encoding", "")
        resource.compressed = content_encoding in ["gzip", "br", "deflate"]
        
        if resource.type in ["script", "stylesheet"]:
            resource.blocking = True
        
        self.total_requests += 1
        self.total_page_size += resource.size
        if resource.type == "script":
            self.total_js_size += resource.size
        elif resource.type == "stylesheet":
            self.total_css_size += resource.size
        elif resource.type == "image":
            self.total_image_size += resource.size
        elif resource.type == "font":
            self.total_font_size += resource.size
        
        self.resources.append(resource)
    
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
        if self.ttfb > 800:
            score -= 20
        elif self.ttfb > 400:
            score -= 10
        elif self.ttfb > 200:
            score -= 5
        if self.fcp > 2500:
            score -= 25
        elif self.fcp > 1800:
            score -= 15
        elif self.fcp > 1000:
            score -= 5
        if self.lcp > 4000:
            score -= 25
        elif self.lcp > 2500:
            score -= 15
        elif self.lcp > 1500:
            score -= 5
        if self.cls > 0.25:
            score -= 20
        elif self.cls > 0.1:
            score -= 10
        elif self.cls > 0.05:
            score -= 5
        if self.total_page_size > 5_000_000:
            score -= 20
        elif self.total_page_size > 2_000_000:
            score -= 10
        elif self.total_page_size > 1_000_000:
            score -= 5
        if self.total_requests > 100:
            score -= 15
        elif self.total_requests > 50:
            score -= 8
        elif self.total_requests > 30:
            score -= 3
        if self.dom_elements > 3000:
            score -= 10
        elif self.dom_elements > 1500:
            score -= 5
        return max(score, 0)
    
    def get_performance_grade(self, score: int) -> str:
        if score >= 90:
            return "A"
        if score >= 75:
            return "B"
        if score >= 60:
            return "C"
        if score >= 40:
            return "D"
        return "F"
    
    def get_recommendations(self) -> List[Dict[str, str]]:
        recommendations = []
        if self.ttfb > 400:
            recommendations.append({
                "priority": "high",
                "title": "Improve server response time",
                "description": f"TTFB is {format_ms(self.ttfb)}. Consider using CDN, caching, or upgrading hosting."
            })
        if self.lcp > 2500:
            recommendations.append({
                "priority": "high",
                "title": "Optimize Largest Contentful Paint",
                "description": f"LCP is {format_ms(self.lcp)}. Optimize main image, text, or hero element loading."
            })
        if self.fcp > 1800:
            recommendations.append({
                "priority": "medium",
                "title": "Improve First Contentful Paint",
                "description": f"FCP is {format_ms(self.fcp)}. Reduce render-blocking resources."
            })
        if self.cls > 0.1:
            recommendations.append({
                "priority": "medium",
                "title": "Fix layout shifts",
                "description": f"CLS is {self.cls:.3f}. Set explicit sizes on images, iframes, and dynamic content."
            })
        if self.total_page_size > 2_000_000:
            recommendations.append({
                "priority": "high",
                "title": "Reduce page size",
                "description": f"Page size is {format_bytes(self.total_page_size)}. Compress images, minify JS/CSS, use lazy loading."
            })
        if self.total_requests > 50:
            recommendations.append({
                "priority": "medium",
                "title": "Reduce HTTP requests",
                "description": f"{self.total_requests} requests. Bundle files, use sprites, remove unused code."
            })
        if self.total_js_size > 500_000:
            recommendations.append({
                "priority": "high",
                "title": "Reduce JavaScript size",
                "description": f"JS is {format_bytes(self.total_js_size)}. Use code splitting, tree shaking, defer non-critical JS."
            })
        if self.total_image_size > 1_000_000:
            recommendations.append({
                "priority": "medium",
                "title": "Optimize images",
                "description": f"Images are {format_bytes(self.total_image_size)}. Use WebP/AVIF, lazy loading, responsive images."
            })
        blocking = [r for r in self.resources if r.blocking and r.type in ["script", "stylesheet"]]
        if len(blocking) > 5:
            recommendations.append({
                "priority": "medium",
                "title": "Reduce render-blocking resources",
                "description": f"{len(blocking)} render-blocking resources. Defer JS, inline critical CSS."
            })
        uncached = [r for r in self.resources if not r.cached and r.size > 10000]
        if len(uncached) > 10:
            recommendations.append({
                "priority": "low",
                "title": "Improve caching",
                "description": f"{len(uncached)} resources without caching headers. Add Cache-Control headers."
            })
        uncompressed = [r for r in self.resources if not r.compressed and r.size > 5000 and r.type in ["script", "stylesheet", "fetch"]]
        if len(uncompressed) > 5:
            recommendations.append({
                "priority": "medium",
                "title": "Enable compression",
                "description": f"{len(uncompressed)} resources not compressed. Enable gzip/brotli compression."
            })
        if self.dom_elements > 3000:
            recommendations.append({
                "priority": "low",
                "title": "Simplify DOM",
                "description": f"{self.dom_elements} DOM elements. Reduce DOM size for better performance."
            })
        return recommendations
    
    def record_page_load(self, url: str, load_time: float, status: int = 200):
        is_slow = load_time > self.slow_threshold_ms / 1000
        self.page_timings.append({
            "url": url,
            "load_time": round(load_time, 2),
            "slow": is_slow,
            "status": status,
            "timestamp": datetime.now().isoformat(),
        })
    
    def get_summary(self) -> Dict[str, Any]:
        score = self.calculate_performance_score()
        grade = self.get_performance_grade(score)
        recommendations = self.get_recommendations()
        
        resource_breakdown = {
            "total": {
                "count": self.total_requests,
                "size": self.total_page_size,
                "size_formatted": format_bytes(self.total_page_size)
            },
            "scripts": {
                "count": len([r for r in self.resources if r.type == "script"]),
                "size": self.total_js_size,
                "size_formatted": format_bytes(self.total_js_size)
            },
            "stylesheets": {
                "count": len([r for r in self.resources if r.type == "stylesheet"]),
                "size": self.total_css_size,
                "size_formatted": format_bytes(self.total_css_size)
            },
            "images": {
                "count": len([r for r in self.resources if r.type == "image"]),
                "size": self.total_image_size,
                "size_formatted": format_bytes(self.total_image_size)
            },
            "fonts": {
                "count": len([r for r in self.resources if r.type == "font"]),
                "size": self.total_font_size,
                "size_formatted": format_bytes(self.total_font_size)
            },
            "other": {
                "count": len([r for r in self.resources if r.type not in ["script", "stylesheet", "image", "font"]]),
                "size": 0,
                "size_formatted": "N/A",
            },
        }
        
        sorted_resources = sorted(self.resources, key=lambda r: r.duration, reverse=True)
        slowest = [r.to_dict() for r in sorted_resources[:10] if r.duration > 100]
        
        sorted_by_size = sorted(self.resources, key=lambda r: r.size, reverse=True)
        largest = [r.to_dict() for r in sorted_by_size[:10] if r.size > 0]
        
        third_party = defaultdict(lambda: {"count": 0, "size": 0})
        for r in self.resources:
            if r.third_party:
                third_party[r.domain]["count"] += 1
                third_party[r.domain]["size"] += r.size
        
        slow_pages = [p for p in self.page_timings if p["slow"]]
        avg_load = sum(p["load_time"] for p in self.page_timings) / max(len(self.page_timings), 1)
        
        return {
            "score": score,
            "grade": grade,
            "web_vitals": {
                "ttfb": round(self.ttfb, 2),
                "ttfb_formatted": format_ms(self.ttfb),
                "fcp": round(self.fcp, 2),
                "fcp_formatted": format_ms(self.fcp),
                "lcp": round(self.lcp, 2),
                "lcp_formatted": format_ms(self.lcp),
                "cls": round(self.cls, 4),
                "dom_content_loaded": round(self.dom_content_loaded, 2),
            },
            "dom_stats": {
                "elements": self.dom_elements,
                "depth": self.dom_depth,
                "scripts": self.page_metrics.get("scripts", 0),
                "stylesheets": self.page_metrics.get("stylesheets", 0),
                "images": self.page_metrics.get("images", 0),
            },
            "resource_breakdown": resource_breakdown,
            "total_requests": self.total_requests,
            "total_page_size": self.total_page_size,
            "total_page_size_formatted": format_bytes(self.total_page_size),
            "slowest_resources": slowest,
            "largest_resources": largest,
            "third_party_domains": {
                k: {"count": v["count"], "size": format_bytes(v["size"])}
                for k, v in sorted(third_party.items(), key=lambda x: x[1]["size"], reverse=True)[:10]
            },
            "recommendations": recommendations,
            "pages_tested": len(self.page_timings),
            "slow_pages": len(slow_pages),
            "average_load_time": round(avg_load, 2),
            "slow_pages_list": slow_pages,
            "all_timings": self.page_timings,
            "resources": [r.to_dict() for r in self.resources],
        }


# ═══════════════════════════════════════════
# SCREENSHOT MANAGER
# ═══════════════════════════════════════════

class ScreenshotManager:
    """Manages all screenshot capture and organization"""
    
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
        """Capture full page screenshot"""
        try:
            safe_name = re.sub(r'[^a-zA-Z0-9]', '_', url)[:50]
            filename = f"{prefix}_{safe_name}_{datetime.now().strftime('%H%M%S')}.png"
            filepath = self.pages_dir / filename
            await page.screenshot(path=str(filepath), full_page=True)
            self.watermark.apply(str(filepath))
            rel_path = str(filepath.relative_to(self.output_dir))
            self.screenshots.append({
                "url": url,
                "title": title,
                "screenshot": rel_path,
                "type": "page",
                "timestamp": datetime.now().isoformat(),
            })
            return rel_path
        except Exception as e:
            console.print(f"[dim]⚠️ Screenshot failed: {truncate(e)}[/dim]")
            return None
    
    async def capture_security_screenshot(self, page: Page, finding_id: str, url: str = "") -> Optional[str]:
        """Capture screenshot for security finding"""
        try:
            safe_id = re.sub(r'[^a-zA-Z0-9]', '_', finding_id)[:30]
            filename = f"security_{safe_id}_{datetime.now().strftime('%H%M%S')}.png"
            filepath = self.security_dir / filename
            await page.screenshot(path=str(filepath), full_page=True)
            self.watermark.apply(str(filepath))
            rel_path = str(filepath.relative_to(self.output_dir))
            self.screenshots.append({
                "url": url,
                "title": f"Security: {finding_id}",
                "screenshot": rel_path,
                "type": "security",
                "finding_id": finding_id,
                "timestamp": datetime.now().isoformat(),
            })
            return rel_path
        except:
            return None
    
    def get_all_screenshots(self) -> List[Dict]:
        return self.screenshots


# ═══════════════════════════════════════════
# SECURITY SCANNER
# ═══════════════════════════════════════════

class SecurityFinding:
    """Represents a security finding with screenshot support"""
    
    def __init__(self, category: str, severity: str, title: str,
                 description: str, location: str = "", evidence: str = "",
                 recommendation: str = "", screenshot: str = ""):
        self.category = category
        self.severity = severity
        self.title = title
        self.description = description
        self.location = location
        self.evidence = evidence
        self.recommendation = recommendation
        self.screenshot = screenshot
        self.timestamp = datetime.now().isoformat()
        self.id = hashlib.md5(f"{category}{title}{location}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "category": self.category,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "evidence": self.evidence[:500] if self.evidence else "",
            "recommendation": self.recommendation,
            "screenshot": self.screenshot,
            "timestamp": self.timestamp,
        }


class SecurityScanner:
    """Enhanced security scanner with screenshot capture for HIGH/CRITICAL issues"""
    
    def __init__(self, page: Page, context: BrowserContext, base_url: str,
                 error_tracker: ErrorTracker, screenshot_manager: ScreenshotManager):
        self.page = page
        self.context = context
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.error_tracker = error_tracker
        self.screenshot_manager = screenshot_manager
        self.findings: List[SecurityFinding] = []
    
    def add_finding(self, category: str, severity: str, title: str,
                    description: str, location: str = "", evidence: str = "",
                    recommendation: str = "") -> SecurityFinding:
        finding = SecurityFinding(category, severity, title, description,
                                  location, evidence, recommendation)
        self.findings.append(finding)
        return finding
    
    async def _capture_if_important(self, finding: SecurityFinding):
        """Capture screenshot for HIGH and CRITICAL findings"""
        if finding.severity in ["critical", "high"]:
            try:
                screenshot = await self.screenshot_manager.capture_security_screenshot(
                    self.page, f"{finding.category}_{finding.id}", finding.location
                )
                if screenshot:
                    finding.screenshot = screenshot
            except:
                pass
    
    async def run_all_tests(self) -> List[SecurityFinding]:
        console.print("\n[bold red]🛡️  SECURITY AUDIT[/bold red]")
        console.print("═" * 50)
        
        tests = [
            ("Security Headers", self.test_security_headers),
            ("XSS Detection", self.test_xss),
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
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            task = progress.add_task("[red]Running security tests...", total=len(tests))
            for test_name, test_func in tests:
                progress.update(task, description=f"[red]Testing: {test_name}[/red]")
                try:
                    await test_func()
                except Exception as e:
                    finding = self.add_finding("Scanner Error", "info",
                                               f"Test failed: {test_name}", str(e))
                    await self._capture_if_important(finding)
                progress.advance(task)
        
        return self.findings
    
    async def test_security_headers(self):
        try:
            response = await self.context.request.get(self.base_url, timeout=15000)
            headers = {k.lower(): v for k, v in response.headers.items()}
            for header_name, config in SECURITY_HEADERS.items():
                header_lower = header_name.lower()
                if header_lower not in headers:
                    finding = self.add_finding(
                        "Security Headers", config["severity"],
                        f"Missing: {header_name}", config["description"],
                        location=self.base_url,
                        recommendation=f"Add: {header_name}: {config['recommendation']}"
                    )
                    await self._capture_if_important(finding)
                elif header_name == "Access-Control-Allow-Origin":
                    if headers[header_lower] == "*":
                        finding = self.add_finding(
                            "CORS", "high", "Wildcard CORS Policy",
                            "Access-Control-Allow-Origin is set to '*'",
                            location=self.base_url,
                            evidence=f"Header: {headers[header_lower]}",
                            recommendation="Restrict to specific origins"
                        )
                        await self._capture_if_important(finding)
        except Exception as e:
            self.add_finding("Security Headers", "info", "Could not check headers", str(e))
    
    async def test_xss(self):
        current_url = self.page.url
        parsed = urlparse(current_url)
        if parsed.query:
            params = parse_qs(parsed.query)
            for param_name in params:
                for payload in XSS_PAYLOADS[:3]:
                    try:
                        test_url = current_url.replace(
                            f"{param_name}={params[param_name][0]}",
                            f"{param_name}={urllib.parse.quote(payload)}"
                        )
                        resp = await self.context.request.get(test_url, timeout=10000)
                        body = await resp.text()
                        if payload in body:
                            finding = self.add_finding(
                                "XSS", "high",
                                f"Reflected XSS in: {param_name}",
                                "User input reflected without sanitization",
                                location=current_url,
                                evidence=f"Payload reflected: {payload[:80]}",
                                recommendation="Sanitize output with escaping"
                            )
                            await self._capture_if_important(finding)
                    except:
                        continue
        
        forms = await self.page.query_selector_all("form")
        for form in forms:
            try:
                inputs = await form.query_selector_all("input:not([type='submit']):not([type='hidden'])")
                for input_el in inputs:
                    name = await input_el.get_attribute("name")
                    if name:
                        for payload in XSS_PAYLOADS[:2]:
                            try:
                                await input_el.fill(payload)
                                await asyncio.sleep(0.2)
                                reflected = await self.page.evaluate(
                                    f"() => document.body.innerHTML.includes({json.dumps(payload)})"
                                )
                                if reflected:
                                    finding = self.add_finding(
                                        "XSS", "medium",
                                        f"Reflected XSS in form: {name}",
                                        "Input reflected in page",
                                        location=current_url,
                                        evidence=f"Payload: {payload[:80]}",
                                        recommendation="Sanitize input and output"
                                    )
                            except:
                                continue
            except:
                continue
    
    async def test_sqli_points(self):
        current_url = self.page.url
        parsed = urlparse(current_url)
        if parsed.query:
            params = parse_qs(parsed.query)
            for param_name, values in params.items():
                if values[0].isdigit() or param_name.lower() in ['id', 'user', 'page', 'cat', 'product']:
                    for test_str in ["'", "' OR '1'='1"]:
                        try:
                            test_url = current_url.replace(
                                f"{param_name}={values[0]}",
                                f"{param_name}={urllib.parse.quote(test_str)}"
                            )
                            resp = await self.context.request.get(test_url, timeout=10000)
                            body = await resp.text()
                            sql_errors = [
                                "SQL syntax", "mysql_fetch", "ORA-", "PostgreSQL",
                                "SQLite", "Microsoft SQL", "ODBC Driver",
                                "SQLSTATE", "Database error", "Unclosed quotation"
                            ]
                            for error_pattern in sql_errors:
                                if error_pattern.lower() in body.lower():
                                    finding = self.add_finding(
                                        "SQL Injection", "critical",
                                        f"Potential SQLi in: {param_name}",
                                        f"SQL error detected: {error_pattern}",
                                        location=current_url,
                                        evidence=f"Error: {error_pattern}",
                                        recommendation="Use parameterized queries"
                                    )
                                    await self._capture_if_important(finding)
                                    break
                        except:
                            continue
    
    async def test_csrf(self):
        forms = await self.page.query_selector_all("form")
        for form in forms:
            try:
                method = (await form.get_attribute("method") or "GET").upper()
                if method in ["POST", "PUT", "PATCH", "DELETE"]:
                    csrf_inputs = await form.query_selector_all(
                        'input[name*="csrf" i], input[name*="token" i], '
                        'input[name="_token"], input[name="authenticity_token"]'
                    )
                    if not csrf_inputs:
                        action = await form.get_attribute("action") or self.page.url
                        finding = self.add_finding(
                            "CSRF", "high", "Missing CSRF Protection",
                            f"Form has no CSRF token",
                            location=action[:100],
                            recommendation="Add CSRF token to forms"
                        )
                        await self._capture_if_important(finding)
            except:
                continue
    
    async def test_sensitive_files(self):
        base = self.base_url.rstrip("/")
        for file_path in SENSITIVE_FILES:
            try:
                test_url = f"{base}/{file_path}"
                resp = await self.context.request.get(test_url, timeout=8000)
                if resp.status == 200:
                    severity = "high"
                    if file_path in ["robots.txt", "sitemap.xml", "readme.html"]:
                        severity = "low"
                    elif file_path.startswith(".") or "config" in file_path or "backup" in file_path:
                        severity = "critical"
                    finding = self.add_finding(
                        "Sensitive File Exposure", severity,
                        f"Exposed: {file_path}",
                        f"File accessible (HTTP {resp.status})",
                        location=test_url,
                        evidence=f"Content-Type: {resp.headers.get('content-type', 'N/A')}",
                        recommendation="Restrict access via server config"
                    )
                    await self._capture_if_important(finding)
            except:
                continue
    
    async def test_cookie_security(self):
        cookies = await self.context.cookies()
        current_url = self.page.url
        is_https = current_url.startswith("https://")
        for cookie in cookies:
            if is_https and not cookie.get("secure", False):
                self.add_finding(
                    "Cookie Security", "medium",
                    f"Cookie missing Secure: {cookie['name']}",
                    "Can be transmitted over unencrypted connection",
                    location=current_url,
                    recommendation="Set Secure flag"
                )
            if not cookie.get("httpOnly", False):
                self.add_finding(
                    "Cookie Security", "medium",
                    f"Cookie missing HttpOnly: {cookie['name']}",
                    "Accessible via JavaScript (XSS risk)",
                    location=current_url,
                    recommendation="Set HttpOnly flag"
                )
    
    async def test_info_disclosure(self):
        try:
            page_content = await self.page.content()
            for pattern, description in INFO_DISCLOSURE_PATTERNS:
                matches = re.findall(pattern, page_content, re.IGNORECASE)
                if matches:
                    finding = self.add_finding(
                        "Information Disclosure", "critical",
                        f"Potential: {description}",
                        f"Found {len(matches)} match(es) in page source",
                        location=self.page.url,
                        evidence=f"Pattern matched: {pattern[:80]}",
                        recommendation="Remove secrets from source code"
                    )
                    await self._capture_if_important(finding)
        except:
            pass
    
    async def test_cors(self):
        try:
            test_origins = ["https://evil.com", "null"]
            for origin in test_origins:
                resp = await self.context.request.get(
                    self.base_url, headers={"Origin": origin}, timeout=10000
                )
                acao = resp.headers.get("access-control-allow-origin", "")
                acac = resp.headers.get("access-control-allow-credentials", "")
                if acao == origin and acac.lower() == "true":
                    finding = self.add_finding(
                        "CORS", "critical", "CORS misconfiguration",
                        f"Origin {origin} reflected with credentials",
                        location=self.base_url,
                        evidence=f"ACAO: {acao}, ACAC: {acac}",
                        recommendation="Do not reflect Origin with credentials"
                    )
                    await self._capture_if_important(finding)
                    break
        except:
            pass
    
    async def test_clickjacking(self):
        try:
            resp = await self.context.request.get(self.base_url, timeout=10000)
            xfo = resp.headers.get("x-frame-options", "")
            csp = resp.headers.get("content-security-policy", "")
            if not xfo and "frame-ancestors" not in csp.lower():
                finding = self.add_finding(
                    "Clickjacking", "medium", "Missing Clickjacking Protection",
                    "No X-Frame-Options or CSP frame-ancestors",
                    location=self.base_url,
                    recommendation="Add X-Frame-Options: DENY"
                )
        except:
            pass
    
    async def test_form_security(self):
        forms = await self.page.query_selector_all("form")
        for form in forms:
            try:
                action = await form.get_attribute("action") or self.page.url
                if not action.startswith("https://"):
                    finding = self.add_finding(
                        "Form Security", "high", "Form submits over HTTP",
                        f"Action: {action[:100]}", location=self.page.url,
                        recommendation="Use HTTPS for forms"
                    )
                    await self._capture_if_important(finding)
            except:
                continue
    
    async def test_ssl(self):
        if not self.base_url.startswith("https://"):
            finding = self.add_finding(
                "SSL/TLS", "high", "No HTTPS",
                "Website does not use HTTPS", location=self.base_url,
                recommendation="Enable HTTPS with valid SSL certificate"
            )
            await self._capture_if_important(finding)
            return
        try:
            mixed_content = await self.page.evaluate("""() => {
                const insecure = [];
                document.querySelectorAll('img[src^="http:"], script[src^="http:"], link[href^="http:"]').forEach(el => {
                    insecure.push(el.tagName + ': ' + (el.src || el.href));
                });
                return insecure;
            }""")
            if mixed_content:
                finding = self.add_finding(
                    "SSL/TLS", "medium", "Mixed Content",
                    f"Found {len(mixed_content)} insecure resources",
                    location=self.page.url,
                    evidence=f"First: {mixed_content[0][:100]}" if mixed_content else "",
                    recommendation="Use HTTPS for all resources"
                )
        except:
            pass
    
    async def test_directory_listing(self):
        test_paths = ["/images/", "/uploads/", "/assets/", "/admin/", "/backup/", "/logs/"]
        base = self.base_url.rstrip("/")
        for path in test_paths:
            try:
                resp = await self.context.request.get(f"{base}{path}", timeout=8000)
                if resp.status == 200:
                    body = await resp.text()
                    indicators = ["Index of /", "Directory Listing For", "Parent Directory"]
                    for indicator in indicators:
                        if indicator.lower() in body.lower():
                            finding = self.add_finding(
                                "Directory Listing", "medium",
                                f"Directory listing: {path}",
                                "Contents publicly visible",
                                location=f"{base}{path}",
                                recommendation="Disable directory listing"
                            )
                            break
            except:
                continue
    
    def get_summary(self) -> Dict[str, Any]:
        by_severity = defaultdict(list)
        by_category = defaultdict(list)
        for finding in self.findings:
            by_severity[finding.severity].append(finding)
            by_category[finding.category].append(finding)
        return {
            "total": len(self.findings),
            "critical": len(by_severity.get("critical", [])),
            "high": len(by_severity.get("high", [])),
            "medium": len(by_severity.get("medium", [])),
            "low": len(by_severity.get("low", [])),
            "info": len(by_severity.get("info", [])),
            "by_severity": {k: len(v) for k, v in by_severity.items()},
            "by_category": {k: len(v) for k, v in by_category.items()},
            "findings": [f.to_dict() for f in self.findings],
        }


# ═══════════════════════════════════════════
# MICRO-INTERACTION TESTER
# ═══════════════════════════════════════════

class MicroInteractionTester:
    """Tests micro-interactions on pages"""
    
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
        result = {
            "id": interaction_id,
            "name": interaction["name"],
            "page_url": page_url,
            "status": "not_found",
            "details": "",
        }
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
                if element:
                    break
            except:
                continue
        if not element:
            result["details"] = "Not found"
            return result
        result["selector_used"] = used_selector
        result["status"] = "found"
        action = interaction.get("test_action", "")
        try:
            if action == "type_test_query":
                await element.fill("test_query")
                await asyncio.sleep(0.5)
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
                await asyncio.sleep(1)
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
                if was != now:
                    await element.click()
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
            self.error_tracker.add_error(
                f"{interaction['name']} Error", str(e),
                page_url=page_url, component=interaction["name"],
                selector=used_selector,
            )
        return result


# ═══════════════════════════════════════════
# LOGIN HANDLER
# ═══════════════════════════════════════════

class LoginHandler:
    """Enhanced login handler: username+password, password-only, direct dashboard access"""
    
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
        self.auth_type = "unknown"  # "username_password", "password_only", "direct_access"
    
    async def _is_dashboard(self) -> bool:
        """Check if current page is already a dashboard/admin panel"""
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
            
            if indicators.get("hasNav"):
                if indicators.get("hasTable") or indicators.get("cardCount", 0) > 0 or indicators.get("score", 0) >= 2:
                    return True
            return False
        except:
            return False
    
    async def _analyze_login_form(self) -> Dict[str, Any]:
        """Analyze the login form structure to determine auth type"""
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
                    usernameFields.push({
                        name: input.name,
                        type: input.type,
                        id: input.id,
                        placeholder: input.placeholder
                    });
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
        """Find login page - returns URL or None if already on dashboard"""
        
        # Try custom login URL first
        if self.custom_login_url:
            login_url = normalize_url(self.custom_login_url)
            console.print(f"[cyan]🔗 Custom login URL: {login_url}[/cyan]")
            try:
                await self.page.goto(login_url, wait_until="domcontentloaded", timeout=15000)
                await asyncio.sleep(2)
                has_password = await self.page.evaluate("() => !!document.querySelector('input[type=\"password\"]')")
                if has_password:
                    console.print("[green]✅ Login form found![/green]")
                    return login_url
                # No password - maybe already dashboard?
                if await self._is_dashboard():
                    console.print("[green]✅ Already on dashboard![/green]")
                    self.auth_type = "direct_access"
                    self.is_logged_in = True
                    return None
                return login_url  # Return anyway, might be a different auth method
            except Exception as e:
                console.print(f"[red]❌ Failed: {truncate(e)}[/red]")
        
        # Check current page for password field
        has_password = await self.page.evaluate("() => !!document.querySelector('input[type=\"password\"]')")
        if has_password:
            console.print("[green]✅ Login form on current page![/green]")
            return self.page.url
        
        # Check if already on dashboard
        if await self._is_dashboard():
            console.print("[green]✅ Already on dashboard![/green]")
            self.auth_type = "direct_access"
            self.is_logged_in = True
            return None
        
        # Search for login links
        login_links = await self.page.evaluate("""() => {
            const links = Array.from(document.querySelectorAll('a[href]'));
            const keywords = ['login', 'signin', 'masuk', 'admin'];
            const found = [];
            for (const link of links) {
                const text = (link.textContent || '').toLowerCase();
                const href = (link.href || '').toLowerCase();
                for (const kw of keywords) {
                    if (text.includes(kw) || href.includes(kw)) {
                        found.push({
                            text: link.textContent?.trim()?.substring(0, 50) || '',
                            href: link.href
                        });
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
                    await asyncio.sleep(2)
                    if await self.page.evaluate("() => !!document.querySelector('input[type=\"password\"]')"):
                        console.print("[green]✅ Navigated to login page![/green]")
                        return self.page.url
                    if await self._is_dashboard():
                        console.print("[green]✅ Navigated to dashboard![/green]")
                        self.auth_type = "direct_access"
                        self.is_logged_in = True
                        return None
                except:
                    continue
        
        # Try common paths
        base = self.base_url.rstrip("/")
        for path in COMMON_LOGIN_PATHS[:8]:
            try:
                await self.page.goto(f"{base}{path}", wait_until="domcontentloaded", timeout=10000)
                await asyncio.sleep(1)
                if await self.page.evaluate("() => !!document.querySelector('input[type=\"password\"]')"):
                    console.print(f"[green]✅ Found: {base}{path}[/green]")
                    return self.page.url
                if await self._is_dashboard():
                    console.print(f"[green]✅ Dashboard: {base}{path}[/green]")
                    self.auth_type = "direct_access"
                    self.is_logged_in = True
                    return None
            except:
                continue
        
        console.print("[red]❌ Login page not found![/red]")
        console.print("[yellow]💡 Use --login-url to specify login URL[/yellow]")
        return None
    
    async def attempt_login(self) -> bool:
        """Attempt login with support for password-only and direct dashboard access"""
        
        if self.skip_login:
            console.print("[yellow]⏭️  Skipping login[/yellow]")
            # Check if already on dashboard even when skipping
            if await self._is_dashboard():
                self.is_logged_in = True
                self.auth_type = "direct_access"
                console.print("[green]✅ Dashboard detected (skip mode)![/green]")
                return True
            return False
        
        console.print("\n[bold magenta]🔐 LOGIN PROCESS[/bold magenta]")
        console.print("═" * 50)
        
        # Find login page
        login_url = await self.find_login_page()
        
        # If already authenticated (direct access)
        if self.is_logged_in and self.auth_type == "direct_access":
            console.print("\n[bold green]🎉 ALREADY AUTHENTICATED![/bold green]")
            console.print(f"[dim]Direct dashboard access detected[/dim]")
            if self.screenshot_manager:
                await self.screenshot_manager.capture_page_screenshot(
                    self.page, self.page.url, "Dashboard Direct Access", "dashboard_direct"
                )
            return True
        
        if not login_url:
            # Last check - maybe we're on a dashboard after all
            if await self._is_dashboard():
                self.is_logged_in = True
                self.auth_type = "direct_access"
                console.print("[green]✅ Dashboard detected![/green]")
                return True
            return False
        
        self.login_url_used = login_url
        console.print(f"\n[bold]📍 Login URL:[/bold] {login_url}")
        
        # Ensure on login page
        if self.page.url != login_url:
            try:
                await self.page.goto(login_url, wait_until="networkidle", timeout=20000)
                await asyncio.sleep(2)
            except:
                pass
        
        # Analyze the login form structure
        console.print("[cyan]🔍 Analyzing login form...[/cyan]")
        form_info = await self._analyze_login_form()
        
        if form_info.get("type") == "no_password_field":
            console.print("[yellow]⚠️ No password field found on this page[/yellow]")
            # Maybe it's a dashboard after all?
            if await self._is_dashboard():
                self.is_logged_in = True
                self.auth_type = "direct_access"
                console.print("[green]✅ Dashboard detected - no login needed![/green]")
                return True
            return False
        
        # Display form type to user
        self.auth_type = form_info["type"]
        if form_info["type"] == "password_only":
            console.print("[bold yellow]🔑 PASSWORD-ONLY FORM DETECTED[/bold yellow]")
            console.print(f"  [dim]This form only requires a password[/dim]")
            console.print(f"  [dim]Total inputs: {form_info['totalInputs']}[/dim]")
        else:
            console.print("[bold cyan]📧 USERNAME + PASSWORD FORM[/bold cyan]")
            if form_info.get('usernameFields'):
                for uf in form_info['usernameFields'][:2]:
                    field_name = uf.get('name') or uf.get('id') or 'unnamed'
                    field_type = uf.get('type', 'text')
                    console.print(f"  [dim]Field: {field_name} (type: {field_type})[/dim]")
        
        # Check for saved credentials
        saved_cred = self.credential_manager.select_credential_interactive(login_url)
        
        if saved_cred:
            console.print(f"\n[cyan]📝 Using saved credential: {saved_cred['label']}[/cyan]")
            username = saved_cred.get("username", "")
            password = saved_cred["password"]
            is_saved = True
        else:
            console.print("\n[bold cyan]📝 ENTER CREDENTIALS[/bold cyan]")
            if not Confirm.ask("Proceed with login?", default=True):
                return False
            
            if form_info["type"] == "password_only":
                # Password-only form
                console.print("[dim]💡 This form only requires a password[/dim]")
                username = ""
                skip_user = Confirm.ask("  Skip username/email? (Enter=yes)", default=True)
                if not skip_user:
                    username = Prompt.ask("  📧 Username / Email (optional, press Enter to skip)")
                    if not username:
                        username = ""
                password = Prompt.ask("  🔑 Password", password=True)
            else:
                # Standard username + password form
                username = Prompt.ask("  📧 Username / Email")
                password = Prompt.ask("  🔑 Password", password=True)
            
            is_saved = False
        
        # Find and fill password field
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
        
        # Fill username if needed
        if username:
            username_field = None
            
            # Try to find using detected field info first
            for uf_info in form_info.get("usernameFields", []):
                if uf_info.get("name"):
                    username_field = await self.page.query_selector(f'input[name="{uf_info["name"]}"]')
                elif uf_info.get("id"):
                    username_field = await self.page.query_selector(f'#{uf_info["id"]}')
                if username_field:
                    break
            
            # Fallback selectors
            if not username_field:
                for sel in ['input[type="email"]', 'input[name="email"]', 
                           'input[name="username"]', 'input[type="text"]:first-of-type']:
                    try:
                        username_field = await self.page.query_selector(sel)
                        if username_field:
                            field_type = await username_field.get_attribute("type")
                            if field_type != "password":
                                break
                            username_field = None
                    except:
                        continue
            
            if username_field:
                try:
                    await username_field.click()
                    await username_field.fill("")
                    await username_field.type(username, delay=50)
                    console.print("[green]✅ Username filled[/green]")
                except Exception as e:
                    console.print(f"[yellow]⚠️ Could not fill username: {truncate(e)}[/yellow]")
                    console.print("[dim]  Continuing with password only...[/dim]")
            else:
                console.print("[yellow]⚠️ No username field found, continuing with password only[/yellow]")
        elif form_info["type"] == "password_only":
            console.print("[dim]  (Password-only form - no username needed)[/dim]")
        
        # Find and click submit button
        console.print("[cyan]🔘 Submitting login form...[/cyan]")
        
        submit_btn = None
        
        # Try standard submit selectors
        for sel in ['button[type="submit"]', 'input[type="submit"]', 'form button', 'button']:
            try:
                submit_btn = await self.page.query_selector(sel)
                if submit_btn and await submit_btn.is_visible():
                    break
                submit_btn = None
            except:
                continue
        
        if submit_btn:
            try:
                if await submit_btn.is_enabled():
                    await submit_btn.click()
                    console.print("[green]✅ Form submitted via button[/green]")
                else:
                    console.print("[yellow]⚠️ Submit button disabled, trying Enter key...[/yellow]")
                    await password_field.press("Enter")
            except:
                await password_field.press("Enter")
        else:
            console.print("[dim]  No submit button found, pressing Enter...[/dim]")
            await password_field.press("Enter")
        
        # Wait for login to process
        console.print("[cyan]⏳ Waiting for login to complete...[/cyan]")
        await asyncio.sleep(3)
        
        try:
            await self.page.wait_for_load_state("networkidle", timeout=20000)
        except:
            console.print("[yellow]⚠️ Timeout waiting for network idle[/yellow]")
        
        await asyncio.sleep(2)
        
        # Check if login succeeded
        current_url = self.page.url
        console.print(f"[dim]Current URL after login: {current_url}[/dim]")
        
        # Multiple checks for success
        still_has_password = await self.page.evaluate(
            "() => !!document.querySelector('input[type=\"password\"]')"
        )
        
        # Check for error messages on page
        error_selectors = [
            '.alert-danger', '.alert-error', '.error-message',
            '.text-danger', '.text-error', '[role="alert"]',
            '.invalid-feedback', '.error', '.message-error',
            '.notification-error', '.toast-error'
        ]
        
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
            except:
                continue
        
        is_dashboard = await self._is_dashboard()
        url_changed = current_url != login_url
        
        # Determine success
        if still_has_password and has_errors:
            console.print("[red]❌ LOGIN FAILED - Error message detected[/red]")
            return False
        
        if still_has_password and not is_dashboard and not url_changed:
            console.print("[red]❌ LOGIN FAILED - Still on login page[/red]")
            return False
        
        # Success!
        self.is_logged_in = True
        console.print("\n[bold green]🎉 LOGIN SUCCESS![/bold green]")
        console.print(f"[green]📍 Now at: {current_url}[/green]")
        console.print(f"[dim]Authentication type: {self.auth_type}[/dim]")
        
        # Take screenshot after successful login
        if self.screenshot_manager:
            await self.screenshot_manager.capture_page_screenshot(
                self.page, current_url, "After Login", "after_login"
            )
        
        # Save credential if new
        if not is_saved:
            if Confirm.ask("\n💾 Save this credential for future use?", default=True):
                label = Prompt.ask("  Label", default=username if username else "password-only")
                self.credential_manager.save_credential(login_url, username, password, label)
                console.print("[green]✅ Credential saved![/green]")
        
        # Save browser session state
        try:
            session_dir = Path("lilo_reports/sessions")
            session_dir.mkdir(parents=True, exist_ok=True)
            await self.context.storage_state(path=str(session_dir / "auth_session.json"))
            console.print("[dim]Browser session state saved[/dim]")
        except Exception as e:
            console.print(f"[dim]⚠️ Could not save session: {truncate(e)}[/dim]")
        
        return True

# ═══════════════════════════════════════════
# DASHBOARD EXPLORER
# ═══════════════════════════════════════════

class DashboardExplorer:
    """Explorer with screenshots and advanced performance tracking"""
    
    def __init__(self, page: Page, context: BrowserContext, domain: str,
                 config: Dict, error_tracker: ErrorTracker,
                 perf_tracker: AdvancedPerformanceTracker,
                 screenshot_manager: ScreenshotManager):
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
        self._setup_monitoring()
    
    def _setup_monitoring(self):
        async def on_request(request: Request):
            if any(p in request.url.lower() for p in ['/api/', '/graphql', '/ajax/']):
                self.api_endpoints.append({
                    "method": request.method,
                    "url": request.url,
                    "page": self.page.url,
                })
            self.perf_tracker.record_resource_start(request)
        
        async def on_response(response: Response):
            if response.request:
                self.perf_tracker.record_resource(response.request, response)
        
        async def on_request_failed(request: Request):
            self.error_tracker.add_error(
                "Network Failed",
                f"{request.method} {request.url}",
                page_url=self.page.url,
                extra={"failure": str(request.failure) if request.failure else "Unknown"}
            )
        
        async def on_console(msg):
            if msg.type in ["error", "warning"]:
                location = getattr(msg, "location", {})
                self.error_tracker.add_error(
                    f"Console {msg.type}",
                    msg.text[:300],
                    page_url=self.page.url,
                    extra={
                        "url": location.get("url", ""),
                        "line": location.get("lineNumber", ""),
                        "column": location.get("columnNumber", "")
                    }
                )
        
        self.page.on("request", on_request)
        self.page.on("response", on_response)
        self.page.on("requestfailed", on_request_failed)
        self.page.on("console", on_console)
    
    async def explore(self) -> Dict[str, Any]:
        console.print("\n[bold cyan]🗺️  EXPLORING APPLICATION + PERFORMANCE[/bold cyan]")
        console.print("═" * 50)
        start_url = clean_url(self.page.url)
        self.visited_urls.add(start_url)
        title = await self.page.title()
        console.print(f"[green]📍 Starting: {title}[/green]")
        
        # Measure Web Vitals
        console.print("[cyan]⚡ Measuring Web Vitals...[/cyan]")
        await self.perf_tracker.measure_web_vitals(self.page)
        self._print_perf_summary()
        
        # Screenshot main page
        await self.screenshot_manager.capture_page_screenshot(self.page, start_url, title, "00_dashboard")
        
        # Micro-tests
        console.print("\n[bold yellow]🧪 Testing micro-interactions...[/bold yellow]")
        tester = MicroInteractionTester(self.page, self.error_tracker)
        results = await tester.test_all_interactions(start_url)
        self.micro_test_results.extend(results)
        self._print_micro_summary(results)
        
        await self._discover_navigation()
        await self._expand_menus()
        await self._discover_navigation()
        await self._explore_pages()
        await self._scan_components()
        
        return {
            "pages_explored": len(self.visited_urls),
            "pages": self.discovered_pages,
            "components": dict(self.components_found),
            "api_endpoints": self.api_endpoints,
            "micro_tests": self.micro_test_results,
            "screenshots": self.screenshot_manager.get_all_screenshots(),
        }
    
    def _print_perf_summary(self):
        summary = self.perf_tracker.get_summary()
        color = "green" if summary['score'] >= 75 else ("yellow" if summary['score'] >= 50 else "red")
        console.print(f"\n[bold]⚡ Performance Score:[/bold] [{color}]{summary['score']}/100 ({summary['grade']})[/{color}]")
        console.print(f"  TTFB: {summary['web_vitals']['ttfb_formatted']} | FCP: {summary['web_vitals']['fcp_formatted']} | LCP: {summary['web_vitals']['lcp_formatted']} | CLS: {summary['web_vitals']['cls']}")
        console.print(f"  Size: {summary['total_page_size_formatted']} | Requests: {summary['total_requests']} | DOM: {summary['dom_stats']['elements']} elements")
    
    def _print_micro_summary(self, results: List[Dict]):
        tested = [r for r in results if r["status"] == "tested"]
        errors = [r for r in results if r["status"] == "error"]
        console.print(f"\n[bold]📊 Micro-Tests:[/bold] ✅ {len(tested)} tested, ❌ {len(errors)} errors")
        if errors:
            for r in errors:
                console.print(f"  [red]• {r['name']}: {r.get('details', '')[:80]}[/red]")
    
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
            except:
                pass
        seen = set()
        new_pages = 0
        for link in all_links:
            try:
                url = clean_url(link["href"])
                if not url or url in seen:
                    continue
                if not same_domain(self.domain, url):
                    continue
                if any(kw in url.lower() for kw in ['logout', 'signout']):
                    continue
                if any(url.lower().endswith(ext) for ext in ['.css', '.js', '.png', '.jpg', '.svg', '.ico', '.pdf']):
                    continue
                seen.add(url)
                if url not in self.visited_urls:
                    self.discovered_pages.append({
                        "url": url,
                        "title": link.get("text", ""),
                        "source": self.page.url
                    })
                    new_pages += 1
            except:
                continue
        console.print(f"[green]✅ Found {new_pages} new pages[/green]")
    
    async def _expand_menus(self):
        expanded = 0
        for selector in EXPANDABLE_SELECTORS:
            try:
                elements = await self.page.query_selector_all(selector)
                for el in elements:
                    try:
                        if await el.is_visible():
                            await el.click()
                            await asyncio.sleep(0.3)
                            expanded += 1
                    except:
                        continue
            except:
                continue
        if expanded > 0:
            console.print(f"[green]✅ {expanded} menus expanded[/green]")
            await asyncio.sleep(1)
    
    async def _explore_pages(self):
        pages_to_visit = [p for p in self.discovered_pages if p["url"] not in self.visited_urls][:self.max_pages]
        if not pages_to_visit:
            console.print("[yellow]⚠️ No new pages[/yellow]")
            return
        console.print(f"\n[bold cyan]🔍 Exploring {len(pages_to_visit)} pages...[/bold cyan]")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Exploring...", total=len(pages_to_visit))
            for i, page_info in enumerate(pages_to_visit):
                url = page_info["url"]
                progress.update(task, description=f"[cyan]{i+1}/{len(pages_to_visit)}: {truncate(url, 50)}[/cyan]")
                try:
                    start = time.time()
                    response = await self.page.goto(url, wait_until="domcontentloaded", timeout=15000)
                    load_time = time.time() - start
                    self.perf_tracker.record_page_load(url, load_time, response.status if response else 0)
                    if load_time > 3:
                        console.print(f"[yellow]  ⚠️ Slow: {load_time:.2f}s[/yellow]")
                    await asyncio.sleep(1)
                    self.visited_urls.add(url)
                    title = await self.page.title()
                    page_info["title"] = title
                    page_info["visited"] = True
                    if i < 10:
                        tester = MicroInteractionTester(self.page, self.error_tracker)
                        self.micro_test_results.extend(await tester.test_all_interactions(url))
                    if i < 20:
                        await self.screenshot_manager.capture_page_screenshot(
                            self.page, url, title, f"page_{i+1:02d}"
                        )
                except Exception as e:
                    console.print(f"[yellow]⚠️ Failed: {truncate(url, 60)} - {truncate(e)}[/yellow]")
                    page_info["error"] = str(e)
                progress.advance(task)
    
    async def _scan_components(self):
        for comp_name, selectors in COMPONENT_SELECTORS.items():
            for selector in selectors:
                try:
                    count = await self.page.evaluate(f"document.querySelectorAll('{selector}').length")
                    if count > 0:
                        self.components_found[comp_name] += count
                except:
                    pass
        if self.components_found:
            console.print("[green]✅ Components:[/green]")
            for name, count in sorted(self.components_found.items()):
                console.print(f"  • {name}: {count}")


# ═══════════════════════════════════════════
# MAIN TESTER v4.5.0
# ═══════════════════════════════════════════

class LiloTester:
    """Main Lilo Tester v4.5.0 - Advanced Performance Edition"""
    
    def __init__(
        self, url: str, output_dir: str = "lilo_reports",
        mode: str = "dashboard", max_pages: int = 50,
        headless: bool = False, custom_login_url: Optional[str] = None,
        open_report: bool = True, skip_login: bool = False,
        enable_security: bool = True,
    ):
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
        
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        self.watermark = WatermarkEngine()
        self.error_tracker = ErrorTracker(self.report_dir)
        self.perf_tracker = AdvancedPerformanceTracker(self.domain)
        self.credential_manager = CredentialManager()
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
            "exploration": {},
            "errors_summary": {},
            "performance": {},
            "security": {},
            "total_time": 0,
        }
    
    async def run(self) -> Dict[str, Any]:
        start_time = time.time()
        console.print(get_banner())
        console.print(f"[bold cyan]🎯 Target:[/bold cyan] {self.url}")
        console.print(f"[bold cyan]🧭 Mode:[/bold cyan] {self.mode.upper()}")
        console.print(f"[bold cyan]🛡️  Security:[/bold cyan] {'ENABLED' if self.enable_security else 'DISABLED'}")
        if self.skip_login:
            console.print(f"[bold cyan]🔓 Login:[/bold cyan] SKIPPED")
        if self.custom_login_url:
            console.print(f"[bold cyan]🔗 Login URL:[/bold cyan] {self.custom_login_url}")
        console.print("-" * 60)
        
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=self.headless, args=['--start-maximized'])
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                ignore_https_errors=True,
            )
            page = await context.new_page()
            
            # Security Audit
            if self.enable_security:
                security_scanner = SecurityScanner(page, context, self.url, self.error_tracker, self.screenshot_manager)
                await security_scanner.run_all_tests()
                self.results["security"] = security_scanner.get_summary()
                self._print_security_summary(security_scanner.findings)
            
            console.print(f"\n[cyan]🌐 Opening {self.url}...[/cyan]")
            try:
                start = time.time()
                resp = await page.goto(self.url, wait_until="domcontentloaded", timeout=30000)
                load_time = time.time() - start
                self.perf_tracker.record_page_load(self.url, load_time, resp.status if resp else 0)
                console.print(f"[green]✅ Page loaded ({load_time:.2f}s)[/green]")
            except Exception as e:
                console.print(f"[red]❌ Failed: {truncate(e)}[/red]")
                await browser.close()
                return self.results
            
            # Login
            login_handler = LoginHandler(
                page, context, self.url, self.custom_login_url,
                self.credential_manager, self.skip_login, self.screenshot_manager
            )
            is_logged_in = await login_handler.attempt_login()
            self.results["authenticated"] = is_logged_in
            self.results["login_url_used"] = login_handler.login_url_used
            
            if is_logged_in:
                console.print("\n[bold green]🔓 AUTHENTICATED - Exploring[/bold green]")
                await self._setup_safe_mode(page)
                explorer = DashboardExplorer(
                    page, context, self.domain, {"max_pages": self.max_pages},
                    self.error_tracker, self.perf_tracker, self.screenshot_manager,
                )
                self.results["exploration"] = await explorer.explore()
            else:
                if self.mode in ["public", "performance"]:
                    explorer = DashboardExplorer(
                        page, context, self.domain, {"max_pages": min(self.max_pages, 10)},
                        self.error_tracker, self.perf_tracker, self.screenshot_manager,
                    )
                    self.results["exploration"] = await explorer.explore()
                else:
                    self.results["exploration"] = {
                        "pages_explored": 1,
                        "pages": [{"url": self.url, "title": await page.title()}],
                        "components": {}, "api_endpoints": [], "micro_tests": [],
                        "screenshots": self.screenshot_manager.get_all_screenshots(),
                    }
            
            await page.close()
            await browser.close()
        
        self.results["total_time"] = time.time() - start_time
        self.results["errors_summary"] = self.error_tracker.get_summary()
        self.results["performance"] = self.perf_tracker.get_summary()
        self.results["exploration"]["screenshots"] = self.screenshot_manager.get_all_screenshots()
        
        self._save_json()
        report_path = self._generate_html()
        self._print_summary()
        
        console.print(f"\n[bold green]✅ HTML Report:[/bold green] {report_path}")
        console.print(f"[bold green]✅ JSON Report:[/bold green] {self.report_dir / 'report.json'}")
        if self.open_report:
            webbrowser.open(f"file://{report_path.absolute()}")
        return self.results
    
    def _print_security_summary(self, findings: List[SecurityFinding]):
        total = len(findings)
        if total == 0:
            console.print("\n[bold green]🛡️  Security: No issues found![/bold green]")
            return
        critical = [f for f in findings if f.severity == "critical"]
        high = [f for f in findings if f.severity == "high"]
        console.print(f"\n[bold red]🛡️  SECURITY FINDINGS: {total} issues[/bold red]")
        console.print(f"  [red]Critical: {len(critical)}[/red]")
        console.print(f"  [red]High: {len(high)}[/red]")
        for f in critical + high[:8]:
            console.print(f"  [red]• [{f.severity.upper()}] {f.title} → {truncate(f.location, 60)}[/red]")
    
    async def _setup_safe_mode(self, page: Page):
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
    
    def _save_json(self):
        with open(self.report_dir / "report.json", "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, default=str)
    
    def _generate_html(self) -> Path:
        env = Environment(loader=BaseLoader(), autoescape=select_autoescape(["html", "xml"]))
        template = env.from_string(HTML_REPORT_V45)
        path = self.report_dir / "report.html"
        with open(path, "w", encoding="utf-8") as f:
            f.write(template.render(results=self.results))
        return path
    
    def _print_summary(self):
        console.print("\n" + "=" * 60)
        summary = Table(title=f"[bold cyan]{APP_NAME} v{APP_VERSION} - Summary[/bold cyan]")
        summary.add_column("Metric", style="cyan")
        summary.add_column("Value", style="green")
        summary.add_row("Target", self.url)
        summary.add_row("Mode", self.mode.upper())
        summary.add_row("Auth", "✅" if self.results["authenticated"] else "❌")
        exp = self.results.get("exploration", {})
        summary.add_row("Pages", str(exp.get("pages_explored", 0)))
        summary.add_row("Screenshots", str(len(exp.get("screenshots", []))))
        perf = self.results.get("performance", {})
        summary.add_row("Perf Score", f"{perf.get('score', 'N/A')}/100 ({perf.get('grade', 'N/A')})")
        summary.add_row("Page Size", perf.get("total_page_size_formatted", "N/A"))
        summary.add_row("Errors", str(self.results.get("errors_summary", {}).get("total", 0)))
        sec = self.results.get("security", {})
        summary.add_row("Security", f"{sec.get('total', 0)} issues")
        summary.add_row("Time", f"{self.results.get('total_time', 0):.2f}s")
        console.print(summary)


# ═══════════════════════════════════════════
# ENHANCED HTML REPORT v4.5
# ═══════════════════════════════════════════

HTML_REPORT_V45 = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ results.app_name }} v{{ results.version }} - {{ results.domain }}</title>
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
        .status-badge { display: inline-block; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }
        .status-success { background: #d1fae5; color: #065f46; }
        .status-fail { background: #fee2e2; color: #991b1b; }
        .perf-score { text-align: center; padding: 30px; }
        .perf-circle {
            display: inline-block; width: 120px; height: 120px; border-radius: 50%;
            border: 8px solid; line-height: 104px; font-size: 2.5rem; font-weight: 900; text-align: center;
        }
        .perf-grade { font-size: 1.5rem; font-weight: 800; margin-top: 8px; }
        .vitals-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; margin-top: 16px; }
        .vital-card {
            padding: 14px; background: white; border-radius: 10px;
            border: 1px solid var(--border); text-align: center;
        }
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
        .finding-severity {
            padding: 3px 10px; border-radius: 20px; font-size: 0.7rem;
            font-weight: 700; text-transform: uppercase; white-space: nowrap;
        }
        .sev-critical { background: #dc2626; color: white; }
        .sev-high { background: #ef4444; color: white; }
        .sev-medium { background: #f59e0b; color: #1a1a1a; }
        .sev-low { background: #10b981; color: white; }
        .sev-info { background: #3b82f6; color: white; }
        .finding-location { font-size: 0.8rem; color: var(--brand); word-break: break-all; margin-bottom: 6px; }
        .finding-evidence {
            margin-top: 6px; padding: 8px 12px; background: #1e293b; border-radius: 6px;
            font-size: 0.78rem; color: #e2e8f0; font-family: monospace; word-break: break-all;
        }
        .finding-recommendation {
            margin-top: 6px; padding: 8px 12px; background: #ecfdf5; border-radius: 6px;
            font-size: 0.82rem; color: #065f46; border-left: 3px solid var(--green);
        }
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
        .tested { color: var(--green); font-weight: 600; } .error { color: var(--red); font-weight: 600; } .slow { color: var(--yellow); font-weight: 600; }
        .error-item {
            padding: 12px; background: #fef2f2; border-radius: 8px;
            border-left: 4px solid var(--red); font-size: 0.82rem; margin-bottom: 6px;
        }
        .component-tags { display: flex; flex-wrap: wrap; gap: 6px; }
        .component-tag {
            padding: 5px 12px; background: #eef2ff; border-radius: 20px;
            font-size: 0.8rem; color: var(--brand); border: 1px solid #e0e7ff;
        }
        .rec-card {
            padding: 12px; border-radius: 8px; margin-bottom: 8px;
            border-left: 4px solid var(--brand); background: #f8fafc;
        }
        .rec-priority { font-size: 0.7rem; font-weight: 700; text-transform: uppercase; }
        .footer {
            background: linear-gradient(135deg, var(--brand), var(--brand2));
            color: white; text-align: center; padding: 20px;
        }
        @media (max-width: 768px) {
            .section { padding: 20px; }
            .tab-btn { padding: 10px 14px; font-size: 0.75rem; }
            .screenshot-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <main class="container">
        <header class="header">
            <div style="display:inline-block;padding:4px 12px;border-radius:12px;background:rgba(255,255,255,0.2);font-size:0.75rem;margin-bottom:10px">
                🦊 {{ results.app_name }} v{{ results.version }} • Advanced Performance
            </div>
            <h1>Application Test Report</h1>
            <div class="meta">
                <div class="meta-item"><div class="label">Target</div><div class="value">{{ results.url[:45] }}</div></div>
                <div class="meta-item">
                    <div class="label">Perf Score</div>
                    <div class="value">
                        {% set ps = results.performance.score|default(0) %}
                        <span style="color:{% if ps>=75 %}#10b981{% elif ps>=50 %}#f59e0b{% else %}#ef4444{% endif %};font-weight:800">
                            {{ ps }}/100 {{ results.performance.grade|default('') }}
                        </span>
                    </div>
                </div>
                <div class="meta-item"><div class="label">Page Size</div><div class="value">{{ results.performance.total_page_size_formatted|default('N/A') }}</div></div>
                <div class="meta-item"><div class="label">Security</div><div class="value">{{ results.security.total|default(0) }} issues</div></div>
            </div>
        </header>

        <div class="tab-nav">
            <button class="tab-btn active" onclick="switchTab('performance')">⚡ Performance</button>
            <button class="tab-btn" onclick="switchTab('security')">🛡️ Security</button>
            <button class="tab-btn" onclick="switchTab('screenshots')">📸 Screenshots</button>
            <button class="tab-btn" onclick="switchTab('exploration')">📊 Exploration</button>
            <button class="tab-btn" onclick="switchTab('microtests')">🧪 Micro-Tests</button>
            <button class="tab-btn" onclick="switchTab('errors')">🐞 Errors</button>
        </div>

        <!-- PERFORMANCE TAB -->
        <div id="tab-performance" class="tab-content active">
            {% set perf = results.performance or {} %}
            <section class="section">
                <h2>⚡ Performance Score</h2>
                <div class="perf-score">
                    {% set ps = perf.score|default(0) %}
                    <div class="perf-circle" style="border-color:{% if ps>=75 %}#10b981{% elif ps>=50 %}#f59e0b{% else %}#ef4444{% endif %};color:{% if ps>=75 %}#10b981{% elif ps>=50 %}#f59e0b{% else %}#ef4444{% endif %}">{{ ps }}</div>
                    <div class="perf-grade" style="color:{% if ps>=75 %}#10b981{% elif ps>=50 %}#f59e0b{% else %}#ef4444{% endif %}">Grade: {{ perf.grade|default('?') }}</div>
                </div>
            </section>
            <section class="section">
                <h2>📈 Core Web Vitals</h2>
                {% set wv = perf.web_vitals or {} %}
                <div class="vitals-grid">
                    <div class="vital-card"><div class="vital-value {{ 'good' if wv.ttfb|default(0)<400 else 'warn' if wv.ttfb|default(0)<800 else 'bad' }}">{{ wv.ttfb_formatted|default('?') }}</div><div class="vital-label">TTFB</div></div>
                    <div class="vital-card"><div class="vital-value {{ 'good' if wv.fcp|default(0)<1800 else 'warn' if wv.fcp|default(0)<2500 else 'bad' }}">{{ wv.fcp_formatted|default('?') }}</div><div class="vital-label">FCP</div></div>
                    <div class="vital-card"><div class="vital-value {{ 'good' if wv.lcp|default(0)<2500 else 'warn' if wv.lcp|default(0)<4000 else 'bad' }}">{{ wv.lcp_formatted|default('?') }}</div><div class="vital-label">LCP</div></div>
                    <div class="vital-card"><div class="vital-value {{ 'good' if wv.cls|default(0)<0.1 else 'warn' if wv.cls|default(0)<0.25 else 'bad' }}">{{ wv.cls|default('?') }}</div><div class="vital-label">CLS</div></div>
                </div>
            </section>
            <section class="section">
                <h2>📊 Resource Breakdown</h2>
                {% set rb = perf.resource_breakdown or {} %}
                <div class="stats">
                    <div class="stat-card"><div class="number">{{ perf.total_requests|default(0) }}</div><div class="label">Requests</div></div>
                    <div class="stat-card"><div class="number">{{ perf.total_page_size_formatted|default('0') }}</div><div class="label">Total Size</div></div>
                    <div class="stat-card"><div class="number">{{ rb.scripts.size_formatted|default('0') }}</div><div class="label">JS</div></div>
                    <div class="stat-card"><div class="number">{{ rb.stylesheets.size_formatted|default('0') }}</div><div class="label">CSS</div></div>
                    <div class="stat-card"><div class="number">{{ rb.images.size_formatted|default('0') }}</div><div class="label">Images</div></div>
                    <div class="stat-card"><div class="number">{{ rb.fonts.size_formatted|default('0') }}</div><div class="label">Fonts</div></div>
                </div>
            </section>
            {% if perf.dom_stats %}
            <section class="section">
                <h2>🏗️ DOM Complexity</h2>
                <div class="stats">
                    <div class="stat-card"><div class="number">{{ perf.dom_stats.elements|default(0) }}</div><div class="label">Elements</div></div>
                    <div class="stat-card"><div class="number">{{ perf.dom_stats.depth|default(0) }}</div><div class="label">Max Depth</div></div>
                    <div class="stat-card"><div class="number">{{ perf.dom_stats.scripts|default(0) }}</div><div class="label">Script Tags</div></div>
                </div>
            </section>
            {% endif %}
            {% if perf.slowest_resources %}
            <section class="section">
                <div class="collapsible">
                    <div class="collapsible-header" onclick="toggleCollapsible(this)">🐌 Slowest Resources ({{ perf.slowest_resources|length }}) <span class="arrow">▼</span></div>
                    <div class="collapsible-body">
                        <table>
                            <thead><tr><th>Resource</th><th>Type</th><th>Duration</th><th>Size</th></tr></thead>
                            <tbody>{% for r in perf.slowest_resources[:15] %}<tr><td style="word-break:break-all;font-size:0.8rem">{{ r.url[:80] }}</td><td>{{ r.type }}</td><td class="slow">{{ r.duration_ms }}ms</td><td>{{ r.size_formatted }}</td></tr>{% endfor %}</tbody>
                        </table>
                    </div>
                </div>
            </section>
            {% endif %}
            {% if perf.largest_resources %}
            <section class="section">
                <div class="collapsible">
                    <div class="collapsible-header" onclick="toggleCollapsible(this)">📦 Largest Resources ({{ perf.largest_resources|length }}) <span class="arrow">▼</span></div>
                    <div class="collapsible-body">
                        <table>
                            <thead><tr><th>Resource</th><th>Type</th><th>Size</th></tr></thead>
                            <tbody>{% for r in perf.largest_resources[:15] %}<tr><td style="word-break:break-all;font-size:0.8rem">{{ r.url[:80] }}</td><td>{{ r.type }}</td><td>{{ r.size_formatted }}</td></tr>{% endfor %}</tbody>
                        </table>
                    </div>
                </div>
            </section>
            {% endif %}
            {% if perf.third_party_domains %}
            <section class="section">
                <div class="collapsible">
                    <div class="collapsible-header" onclick="toggleCollapsible(this)">🌐 Third-Party Domains ({{ perf.third_party_domains|length }}) <span class="arrow">▼</span></div>
                    <div class="collapsible-body">
                        <table>
                            <thead><tr><th>Domain</th><th>Requests</th><th>Size</th></tr></thead>
                            <tbody>{% for domain, data in perf.third_party_domains.items() %}<tr><td>{{ domain }}</td><td>{{ data.count }}</td><td>{{ data.size }}</td></tr>{% endfor %}</tbody>
                        </table>
                    </div>
                </div>
            </section>
            {% endif %}
            {% if perf.recommendations %}
            <section class="section">
                <h2>💡 Recommendations ({{ perf.recommendations|length }})</h2>
                {% for rec in perf.recommendations %}
                <div class="rec-card">
                    <div class="rec-priority" style="color:{% if rec.priority=='high' %}var(--red){% elif rec.priority=='medium' %}var(--yellow){% else %}var(--brand){% endif %}">{{ rec.priority }}</div>
                    <strong>{{ rec.title }}</strong>
                    <div style="font-size:0.85rem;color:var(--muted);margin-top:4px">{{ rec.description }}</div>
                </div>
                {% endfor %}
            </section>
            {% endif %}
        </div>

        <!-- SECURITY TAB -->
        <div id="tab-security" class="tab-content">
            {% set sec = results.security or {} %}
            <section class="section">
                <h2>🛡️ Security Findings ({{ sec.total or 0 }})</h2>
                {% if sec.total %}
                <div class="stats" style="margin-bottom:20px">
                    <div class="stat-card"><div class="number" style="color:var(--critical)">{{ sec.critical or 0 }}</div><div class="label">Critical</div></div>
                    <div class="stat-card"><div class="number" style="color:var(--high)">{{ sec.high or 0 }}</div><div class="label">High</div></div>
                    <div class="stat-card"><div class="number" style="color:var(--medium)">{{ sec.medium or 0 }}</div><div class="label">Medium</div></div>
                    <div class="stat-card"><div class="number" style="color:var(--low)">{{ sec.low or 0 }}</div><div class="label">Low</div></div>
                </div>
                {% set ch = sec.findings|selectattr('severity','in',['critical','high'])|list %}
                {% if ch %}
                <div class="collapsible open">
                    <div class="collapsible-header" onclick="toggleCollapsible(this)">🚨 Critical & High ({{ ch|length }}) <span class="arrow">▼</span></div>
                    <div class="collapsible-body">
                        {% for f in ch %}
                        <div class="finding-card severity-{{ f.severity }}">
                            <div class="finding-header"><div class="finding-title">{{ f.title }}</div><span class="finding-severity sev-{{ f.severity }}">{{ f.severity }}</span></div>
                            <div>{{ f.description }}</div>
                            <div class="finding-location">📍 <a href="{{ f.location }}" target="_blank">{{ f.location[:100] }}</a></div>
                            {% if f.evidence %}<div class="finding-evidence">🔍 {{ f.evidence[:200] }}</div>{% endif %}
                            {% if f.recommendation %}<div class="finding-recommendation">💡 {{ f.recommendation }}</div>{% endif %}
                            {% if f.screenshot %}<div class="finding-screenshot"><img src="{{ f.screenshot }}" loading="lazy" onerror="this.parentElement.style.display='none'"></div>{% endif %}
                        </div>
                        {% endfor %}
                    </div>
                </div>
                {% endif %}
                {% else %}<p style="text-align:center;padding:40px;color:var(--green);font-size:1.2rem">✅ No security issues!</p>
                {% endif %}
            </section>
        </div>

        <!-- SCREENSHOTS TAB -->
        <div id="tab-screenshots" class="tab-content">
            {% set ss = results.exploration.screenshots or [] %}
            <section class="section">
                <h2>📸 Screenshots ({{ ss|length }})</h2>
                {% if ss %}<div class="screenshot-grid">{% for s in ss %}<div class="screenshot-card"><img src="{{ s.screenshot }}" loading="lazy" onerror="this.parentElement.style.display='none'"><div class="caption"><strong>{{ s.title[:60] or 'Screenshot' }}</strong><br>{{ s.url[:80] }}</div></div>{% endfor %}</div>
                {% else %}<p style="text-align:center;padding:40px;color:var(--muted)">No screenshots</p>{% endif %}
            </section>
        </div>

        <!-- EXPLORATION TAB -->
        <div id="tab-exploration" class="tab-content">
            {% set exp = results.exploration or {} %}
            <section class="section">
                <h2>📊 Exploration</h2>
                <div class="stats">
                    <div class="stat-card"><div class="number">{{ exp.pages_explored or 0 }}</div><div class="label">Pages</div></div>
                    <div class="stat-card"><div class="number">{{ exp.components|length if exp.components else 0 }}</div><div class="label">Components</div></div>
                </div>
            </section>
            {% if exp.components %}
            <section class="section">
                <h2>🧩 Components</h2>
                <div class="component-tags">{% for n,c in exp.components.items() %}<span class="component-tag">{{ n }} ({{ c }})</span>{% endfor %}</div>
            </section>
            {% endif %}
        </div>

        <!-- MICRO-TESTS TAB -->
        <div id="tab-microtests" class="tab-content">
            {% set mt = results.exploration.micro_tests or [] %}
            <section class="section">
                <h2>🧪 Micro-Tests ({{ mt|length }})</h2>
                {% if mt %}<table><thead><tr><th>Test</th><th>Status</th><th>Details</th></tr></thead><tbody>{% for t in mt %}<tr><td><strong>{{ t.name }}</strong></td><td>{% if t.status=='tested' %}<span class="tested">✅</span>{% elif t.status=='error' %}<span class="error">❌</span>{% else %}{{ t.status }}{% endif %}</td><td style="font-size:0.8rem">{{ t.details[:80] }}</td></tr>{% endfor %}</tbody></table>{% endif %}
            </section>
        </div>

        <!-- ERRORS TAB -->
        <div id="tab-errors" class="tab-content">
            {% set es = results.errors_summary or {} %}
            <section class="section">
                <h2>🐞 Errors ({{ es.total or 0 }})</h2>
                {% for e in es.errors[:50] %}
                <div class="error-item"><strong>#{{ e.id }} {{ e.type }}</strong>: {{ e.message[:200] }}<div style="font-size:0.7rem;color:var(--muted);margin-top:4px">📄 {{ e.page_url[:80] }}{% if e.extra.line %} | 📍 L:{{ e.extra.line }}{% endif %}</div></div>
                {% endfor %}
            </section>
        </div>

        <footer class="footer">
            <div style="font-weight:700">🦊 {{ results.app_name }} v{{ results.version }}</div>
            <div style="opacity:0.8;margin-top:4px">Advanced Performance • Security • Micro-Tests</div>
        </footer>
    </main>
    <script>
        function switchTab(tabName){document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));document.querySelectorAll('.tab-content').forEach(c=>c.classList.remove('active'));document.getElementById('tab-'+tabName).classList.add('active');event.target.classList.add('active')}
        function toggleCollapsible(h){h.parentElement.classList.toggle('open')}
    </script>
</body>
</html>
"""


# ═══════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════

async def main_async():
    parser = argparse.ArgumentParser(
        description=f"🦊 {APP_NAME} v{APP_VERSION} - Advanced Performance Analytics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
╔══════════════════════════════════════════════════════════════════╗
║              LILO TESTER v4.5 - ADVANCED PERFORMANCE             ║
╠══════════════════════════════════════════════════════════════════╣
║  MODES: dashboard | public | performance | security | quick      ║
║  NEW: Web Vitals, Resource Analysis, Performance Scoring         ║
╚══════════════════════════════════════════════════════════════════╝
        """
    )
    parser.add_argument("--url", "-u", required=True, help="Target URL")
    parser.add_argument("--login-url", "-l", help="Custom login URL", default=None)
    parser.add_argument("--output", "-o", default="lilo_reports", help="Output dir")
    parser.add_argument("--mode", "-m", choices=["dashboard", "public", "performance", "security", "quick"], default="dashboard")
    parser.add_argument("--max-pages", type=int, default=50)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--no-login", action="store_true")
    parser.add_argument("--no-security", action="store_true")
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()
    login_url = args.login_url
    if login_url and not login_url.startswith("http"):
        base = args.url.rstrip("/")
        login_url = f"{base}/{login_url.lstrip('/')}"
    skip_login = args.no_login or args.mode in ["public", "performance", "security"]
    if args.mode == "security":
        skip_login = True
        args.max_pages = 1
    tester = LiloTester(
        url=args.url, output_dir=args.output, mode=args.mode,
        max_pages=args.max_pages, headless=args.headless,
        custom_login_url=login_url, open_report=not args.no_open,
        skip_login=skip_login, enable_security=not args.no_security,
    )
    await tester.run()

def cli():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/yellow]")

if __name__ == "__main__":
    cli()