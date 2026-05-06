#!/usr/bin/env python3
"""
🦊 LILO TESTER - Web Automation Testing Suite
Version: 3.0.2
Author: Lilo
Compatible: Windows / macOS / Linux

Highlights:
- Quick Scan / Full Scan mode
- Internal crawler for full scan
- Broken link details with source page + selector
- Console + network error capture
- Safe form fill simulation without real submission
- Collapsible HTML report
- Can be installed as `liloit` via pyproject console script
"""

import argparse
import asyncio
import json
import os
import platform
import re
import sys
import time
import webbrowser
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse, urlunparse

from jinja2 import BaseLoader, Environment, select_autoescape
from PIL import Image, ImageDraw, ImageFont
from playwright.async_api import Browser, BrowserContext, Page, async_playwright
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.prompt import Prompt
from rich.text import Text

console = Console()

APP_NAME = "Lilo Tester"
APP_VERSION = "3.0.3"
DEFAULT_WATERMARK = "Lilo Tester"


# ═══════════════════════════════════════════
# SYSTEM DETECTION & HELPERS
# ═══════════════════════════════════════════

class SystemDetector:
    """Auto-detect OS and return appropriate settings."""

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
            return [
                "C:\\Windows\\Fonts\\segoeui.ttf",
                "C:\\Windows\\Fonts\\Arial.ttf",
                "C:\\Windows\\Fonts\\Calibri.ttf",
                "arial.ttf",
            ]

        if os_type == "macos":
            return [
                "/System/Library/Fonts/SFNS.ttf",
                "/System/Library/Fonts/SFNSDisplay.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
                "/Library/Fonts/Arial.ttf",
                "~/Library/Fonts/Arial.ttf",
            ]

        return [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
        ]


def normalize_url(url: str) -> str:
    """Normalize target URL for consistent crawling."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def clean_url(url: str) -> str:
    """Remove fragments and normalize trailing slash lightly."""
    parsed = urlparse(url)
    parsed = parsed._replace(fragment="")
    cleaned = urlunparse(parsed)
    if cleaned.endswith("/") and parsed.path not in ("", "/"):
        cleaned = cleaned.rstrip("/")
    return cleaned


def is_probably_page(url: str) -> bool:
    """Avoid crawling obvious assets/files."""
    parsed = urlparse(url)
    path = parsed.path.lower()
    blocked_extensions = (
        ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico",
        ".pdf", ".zip", ".rar", ".7z", ".tar", ".gz",
        ".mp4", ".mp3", ".mov", ".avi", ".webm",
        ".css", ".js", ".json", ".xml", ".txt",
        ".woff", ".woff2", ".ttf", ".otf", ".eot",
    )
    return not path.endswith(blocked_extensions)


def same_domain(base_domain: str, url: str) -> bool:
    return urlparse(url).netloc == base_domain


def truncate(value: Any, length: int = 240) -> str:
    text = str(value or "")
    return text if len(text) <= length else text[: length - 3] + "..."


def safe_request_failure_text(request: Any) -> str:
    """Return Playwright request failure text safely across versions.

    Some Playwright versions expose request.failure as a string, some as a
    dictionary-like object, and some as a callable. Event handlers must never
    raise because Playwright will print a noisy internal traceback.
    """
    try:
        failure = getattr(request, "failure", None)
        if callable(failure):
            failure = failure()

        if isinstance(failure, dict):
            return str(failure.get("errorText") or failure.get("error_text") or "Unknown network error")

        if failure:
            return str(failure)

        return "Unknown network error"
    except Exception as exc:
        return f"Unknown network error ({type(exc).__name__})"


# ═══════════════════════════════════════════
# BANNER & WATERMARK ENGINE
# ═══════════════════════════════════════════

def get_banner() -> str:
    return f"""
[bold cyan]
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   ██╗     ██╗██╗      ██████╗                                    ║
║   ██║     ██║██║     ██╔═══██╗                                   ║
║   ██║     ██║██║     ██║   ██║                                   ║
║   ██║     ██║██║     ██║   ██║                                   ║
║   ███████╗██║███████╗╚██████╔╝                                   ║
║   ╚══════╝╚═╝╚══════╝ ╚═════╝                                    ║
║                                                                  ║
║   ████████╗███████╗███████╗████████╗███████╗██████╗              ║
║   ╚══██╔══╝██╔════╝██╔════╝╚══██╔══╝██╔════╝██╔══██╗             ║
║      ██║   █████╗  ███████╗   ██║   █████╗  ██████╔╝             ║
║      ██║   ██╔══╝  ╚════██║   ██║   ██╔══╝  ██╔══██╗             ║
║      ██║   ███████╗███████║   ██║   ███████╗██║  ██║             ║
║      ╚═╝   ╚══════╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝             ║
║                                                                  ║
║              Web Automation Testing Suite                        ║
║                      v{APP_VERSION} Universal                           ║
║              Running on {SystemDetector.get_os().upper():<10}                              ║
╚══════════════════════════════════════════════════════════════════╝
[/bold cyan]
"""


class WatermarkEngine:
    """Apply Lilo Tester branding watermark to screenshots."""

    def __init__(self, text: str = DEFAULT_WATERMARK, opacity: int = 170, position: str = "bottom-right"):
        self.text = text
        self.opacity = opacity
        self.position = position
        self.font = self._load_font()

    def _load_font(self):
        for font_path in SystemDetector.get_font_paths():
            expanded_path = os.path.expanduser(font_path)
            if os.path.exists(expanded_path):
                try:
                    return ImageFont.truetype(expanded_path, 28)
                except Exception:
                    continue

        try:
            return ImageFont.truetype("arial.ttf", 28)
        except Exception:
            return ImageFont.load_default()

    def apply(self, image_path: str, output_path: Optional[str] = None) -> bool:
        try:
            img = Image.open(image_path)
            if img.mode != "RGBA":
                img = img.convert("RGBA")

            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)

            text_bbox = draw.textbbox((0, 0), self.text, font=self.font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]

            padding = 25
            badge_padding = 12
            pos = self._calculate_position(img.width, img.height, text_width, text_height, padding)

            badge_x = pos["text_x"] - badge_padding
            badge_y = pos["text_y"] - badge_padding
            badge_width = text_width + badge_padding * 2
            badge_height = text_height + badge_padding * 2

            draw.rounded_rectangle(
                [badge_x, badge_y, badge_x + badge_width, badge_y + badge_height],
                radius=12,
                fill=(20, 20, 30, self.opacity),
                outline=(120, 120, 140, min(self.opacity + 30, 255)),
                width=2,
            )
            draw.rectangle(
                [badge_x, badge_y + 8, badge_x + 4, badge_y + badge_height - 8],
                fill=(0, 180, 255, 210),
            )
            draw.text((pos["text_x"] + 2, pos["text_y"] + 2), self.text, font=self.font, fill=(0, 0, 0, 120))
            draw.text((pos["text_x"], pos["text_y"]), self.text, font=self.font, fill=(255, 255, 255, 235))

            img = Image.alpha_composite(img, overlay)
            output_path = output_path or image_path

            if output_path.lower().endswith(".png"):
                img.save(output_path, "PNG")
            else:
                img.convert("RGB").save(output_path, "JPEG", quality=95)

            return True
        except Exception as exc:
            console.print(f"[yellow]⚠️ Watermark error: {exc}[/yellow]")
            return False

    def _calculate_position(self, img_width: int, img_height: int, text_width: int, text_height: int, padding: int) -> Dict[str, int]:
        positions = {
            "bottom-right": {"text_x": img_width - text_width - padding, "text_y": img_height - text_height - padding},
            "bottom-left": {"text_x": padding, "text_y": img_height - text_height - padding},
            "top-right": {"text_x": img_width - text_width - padding, "text_y": padding},
            "top-left": {"text_x": padding, "text_y": padding},
        }
        return positions.get(self.position, positions["bottom-right"])


# ═══════════════════════════════════════════
# CORE TESTER
# ═══════════════════════════════════════════

class LiloTester:
    def __init__(
        self,
        url: str,
        output_dir: str = "lilo_reports",
        devices: Optional[List[str]] = None,
        headless: bool = True,
        mode: str = "quick",
        max_pages: int = 25,
        depth: int = 1,
        test_forms: bool = True,
        open_report: bool = True,
    ):
        self.url = normalize_url(url)
        self.domain = urlparse(self.url).netloc
        self.output_dir = Path(output_dir)
        self.timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.report_dir = self.output_dir / f"report_{self.timestamp}"
        self.screenshots_dir = self.report_dir / "screenshots"
        self.headless = headless
        self.mode = mode
        self.max_pages = max(1, max_pages)
        self.depth = max(0, depth)
        self.test_forms = test_forms
        self.open_report = open_report

        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

        self.watermark = WatermarkEngine(text=DEFAULT_WATERMARK, opacity=170, position="bottom-right")

        self.results: Dict[str, Any] = {
            "app_name": APP_NAME,
            "version": APP_VERSION,
            "url": self.url,
            "domain": self.domain,
            "timestamp": self.timestamp,
            "os": SystemDetector.get_os(),
            "mode": self.mode,
            "max_pages": self.max_pages,
            "depth": self.depth,
            "tests": [],
            "pages_scanned": [],
            "screenshots": [],
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "total_time": 0,
        }

        self.devices = devices or ["desktop", "tablet", "mobile"]
        self.device_configs = {
            "desktop": {"width": 1920, "height": 1080, "name": "Desktop"},
            "tablet": {"width": 768, "height": 1024, "name": "Tablet"},
            "mobile": {"width": 375, "height": 812, "name": "Mobile"},
        }

    def add_result(
        self,
        name: str,
        passed: bool,
        message: str = "",
        warning: bool = False,
        details: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        result = {
            "name": name,
            "passed": passed,
            "message": message,
            "warning": warning,
            "details": details or [],
            "time": datetime.now().strftime("%H:%M:%S"),
        }
        self.results["tests"].append(result)

        if warning:
            self.results["warnings"] += 1
        elif passed:
            self.results["passed"] += 1
        else:
            self.results["failed"] += 1

    def print_status(self, name: str, passed: bool, message: str = "", warning: bool = False) -> None:
        if warning:
            icon, color = "⚠️", "yellow"
        elif passed:
            icon, color = "✅", "green"
        else:
            icon, color = "❌", "red"

        console.print(f"  {icon} [{color}]{name}[/{color}]")
        if message:
            console.print(f"     [dim]{message}[/dim]")

    async def run(self) -> Dict[str, Any]:
        start_time = time.time()

        console.print(get_banner())
        console.print(f"[bold cyan]🎯 Target:[/bold cyan] {self.url}")
        console.print(f"[bold cyan]🧭 Mode:[/bold cyan] {self.mode.upper()}")
        console.print(f"[bold cyan]💻 System:[/bold cyan] {platform.system()} {platform.release()}")
        console.print(f"[bold cyan]📁 Output:[/bold cyan] {self.report_dir}")
        console.print("-" * 60)

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=f"LiloTester/{APP_VERSION} ({platform.system()})",
                ignore_https_errors=True,
            )
            page = await context.new_page()

            if self.mode == "full":
                await self._run_full_scan(context, page)
            else:
                await self._run_quick_scan(context, page)

            await browser.close()

        self.results["total_time"] = time.time() - start_time

        json_path = self.save_json_report()
        report_path = self.generate_html_report()
        self.print_summary()

        console.print(f"\n[bold green]✅ HTML Report:[/bold green] {report_path}")
        console.print(f"[bold green]✅ JSON Report:[/bold green] {json_path}")

        if self.open_report:
            self._open_report(report_path)

        console.print(f"[bold cyan]🦊 {APP_NAME} completed![/bold cyan]\n")
        return self.results

    async def _run_quick_scan(self, context: BrowserContext, page: Page) -> None:
        steps = [
            ("Testing page load...", lambda: self.test_page_load(page, self.url)),
            ("Checking title...", lambda: self.test_title(page, self.url)),
            ("Analyzing meta tags...", lambda: self.test_meta_tags(page, self.url)),
            ("Scanning console + network...", lambda: self.test_runtime_issues(context, [self.url])),
            ("Checking security headers...", lambda: self.test_security_headers(context, self.url)),
            ("Detecting forms...", lambda: self.test_forms(page, self.url)),
            ("Testing accessibility...", lambda: self.test_accessibility(page, self.url)),
            ("Checking links...", lambda: self.test_links(context, [self.url])),
            ("Testing responsive design...", lambda: self.test_responsive(context)),
            ("Capturing full page screenshot...", lambda: self.capture_full_page(context)),
        ]
        await self._run_steps(steps)

    async def _run_full_scan(self, context: BrowserContext, page: Page) -> None:
        pages = await self.crawl_internal_pages(page)
        page_urls = [item["url"] for item in pages] or [self.url]
        self.results["pages_scanned"] = pages

        crawl_details = [
            {
                "type": "Crawled Page",
                "page": item["url"],
                "status": item.get("status"),
                "depth": item.get("depth"),
                "hint": item.get("hint", "Page discovered during internal crawl"),
            }
            for item in pages
        ]

        self.add_result(
            "Internal Crawl",
            True,
            f"{len(page_urls)} page(s) queued for full scan",
            details=crawl_details,
        )
        self.print_status("Internal Crawl", True, f"{len(page_urls)} page(s) found")

        steps = [
            ("Testing main page load...", lambda: self.test_page_load(page, self.url)),
            ("Checking title...", lambda: self.test_title(page, self.url)),
            ("Analyzing meta tags...", lambda: self.test_meta_tags(page, self.url)),
            ("Scanning console + network across pages...", lambda: self.test_runtime_issues(context, page_urls)),
            ("Checking security headers...", lambda: self.test_security_headers(context, self.url)),
            ("Detecting and safely filling forms...", lambda: self.test_forms_across_pages(context, page_urls)),
            ("Testing accessibility...", lambda: self.test_accessibility(page, self.url)),
            ("Checking internal broken links...", lambda: self.test_links(context, page_urls)),
            ("Testing responsive design...", lambda: self.test_responsive(context)),
            ("Capturing full page screenshot...", lambda: self.capture_full_page(context)),
        ]
        await self._run_steps(steps)

    async def _run_steps(self, steps: List[Tuple[str, Any]]) -> None:
        with Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=38),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]🦊 Lilo is scanning...[/cyan]", total=len(steps))
            for description, action in steps:
                progress.update(task, description=f"[cyan]{description}[/cyan]")
                try:
                    await asyncio.wait_for(action(), timeout=75)
                except asyncio.TimeoutError:
                    self.add_result(description.replace("...", ""), False, "Step timed out after 75 seconds", warning=True)
                    self.print_status(description.replace("...", ""), False, "Step timeout after 75s", warning=True)
                except Exception as exc:
                    self.add_result(description.replace("...", ""), False, truncate(exc), warning=True)
                    self.print_status(description.replace("...", ""), False, truncate(exc, 80), warning=True)
                progress.advance(task)

    async def test_page_load(self, page: Page, url: str) -> bool:
        start_time = time.time()
        try:
            response = await page.goto(url, wait_until="networkidle", timeout=30000)
            load_time = time.time() - start_time

            if response and response.ok:
                details = [{
                    "type": "Page Load",
                    "page": url,
                    "status": response.status,
                    "duration": f"{load_time:.2f}s",
                    "hint": "Good if under 3 seconds. Acceptable depends on the site type.",
                }]
                if load_time < 3:
                    self.add_result("Page Load Speed", True, f"Loaded in {load_time:.2f}s", details=details)
                    self.print_status("Page Load Speed", True, f"{load_time:.2f}s ⚡")
                else:
                    self.add_result("Page Load Speed", False, f"Slow load: {load_time:.2f}s", warning=True, details=details)
                    self.print_status("Page Load Speed", False, f"Slow: {load_time:.2f}s 🐌", warning=True)
                return True

            status = response.status if response else "No response"
            self.add_result(
                "Page Load",
                False,
                f"Failed to load: HTTP {status}",
                details=[{"type": "Page Load Failed", "page": url, "status": status, "hint": "Main URL did not return a successful HTTP response."}],
            )
            self.print_status("Page Load", False, f"HTTP {status}")
            return False
        except Exception as exc:
            self.add_result(
                "Page Load",
                False,
                truncate(exc),
                details=[{"type": "Page Load Exception", "page": url, "status": "Failed", "hint": truncate(exc)}],
            )
            self.print_status("Page Load", False, truncate(exc, 80))
            return False

    async def test_title(self, page: Page, url: str) -> None:
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            title = await page.title()
            title_length = len(title or "")
            details = [{"type": "Title", "page": url, "text": title or "", "length": title_length}]

            if title and 10 <= title_length <= 70:
                self.add_result("Page Title", True, f'"{title}" ({title_length} chars)', details=details)
                self.print_status("Page Title", True, f'"{truncate(title, 50)}" - Optimal')
            elif title:
                issue = "Too short" if title_length < 10 else "Too long"
                self.add_result("Page Title", True, f"{issue}: {title_length} chars", warning=True, details=details)
                self.print_status("Page Title", True, f"{issue}: {title_length} chars", warning=True)
            else:
                self.add_result("Page Title", False, "Empty title", warning=True, details=details)
                self.print_status("Page Title", False, "Empty title", warning=True)
        except Exception as exc:
            self.add_result("Page Title", False, truncate(exc), warning=True)
            self.print_status("Page Title", False, truncate(exc, 80), warning=True)

    async def test_meta_tags(self, page: Page, url: str) -> None:
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            meta = await page.evaluate("""() => {
                const getMeta = (name) => {
                    const el = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
                    return el ? el.content : null;
                };
                return {
                    description: getMeta('description'),
                    viewport: document.querySelector('meta[name="viewport"]')?.content || null,
                    charset: document.characterSet || null,
                    og_title: getMeta('og:title'),
                    og_description: getMeta('og:description'),
                    og_image: getMeta('og:image'),
                    robots: getMeta('robots')
                };
            }""")

            issues: List[Dict[str, Any]] = []
            description = meta.get("description")
            if not description:
                issues.append({"type": "SEO Meta", "page": url, "target": "meta[name=description]", "status": "Missing", "hint": "Add a concise meta description."})
            elif len(description) < 50:
                issues.append({"type": "SEO Meta", "page": url, "target": "meta[name=description]", "status": "Too short", "text": description, "hint": "Aim for roughly 50-160 characters."})
            elif len(description) > 160:
                issues.append({"type": "SEO Meta", "page": url, "target": "meta[name=description]", "status": "Too long", "text": description, "hint": "Aim for roughly 50-160 characters."})

            if not meta.get("viewport"):
                issues.append({"type": "Responsive Meta", "page": url, "target": "meta[name=viewport]", "status": "Missing", "hint": "Add viewport meta tag for responsive behavior."})
            if not meta.get("og_title"):
                issues.append({"type": "Open Graph", "page": url, "target": "og:title", "status": "Missing", "hint": "Add OG title for social sharing previews."})
            if not meta.get("og_image"):
                issues.append({"type": "Open Graph", "page": url, "target": "og:image", "status": "Missing", "hint": "Add OG image for richer sharing previews."})

            if issues:
                self.add_result("Meta Tags", False, f"{len(issues)} issue(s)", warning=True, details=issues)
                self.print_status("Meta Tags", False, f"{len(issues)} issue(s)", warning=True)
            else:
                self.add_result("Meta Tags", True, "All basic meta tags look good")
                self.print_status("Meta Tags", True, "Well optimized ✓")
        except Exception as exc:
            self.add_result("Meta Tags", False, truncate(exc), warning=True)
            self.print_status("Meta Tags", False, truncate(exc, 80), warning=True)

    async def test_security_headers(self, context: BrowserContext, url: str) -> None:
        """Check security headers with timeout-safe request + browser fallback."""
        security_headers = {
            "Strict-Transport-Security": None,
            "Content-Security-Policy": None,
            "X-Frame-Options": None,
            "X-Content-Type-Options": None,
            "Referrer-Policy": None,
            "Permissions-Policy": None,
        }

        details: List[Dict[str, Any]] = []
        headers: Dict[str, str] = {}
        source = "API request"

        try:
            # Some sites stall APIRequestContext while the browser can still load them.
            # Keep this short so the whole scan never feels frozen.
            response = await asyncio.wait_for(
                context.request.get(url, timeout=12000, max_redirects=5),
                timeout=15,
            )
            headers = response.headers or {}
        except Exception as first_exc:
            source = "Browser fallback"
            try:
                page = await context.new_page()
                try:
                    response = await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                    headers = response.headers if response else {}
                    if not headers:
                        details.append({
                            "type": "Security Header Scan",
                            "page": url,
                            "status": "No headers captured",
                            "hint": "The page loaded but response headers were not available.",
                        })
                finally:
                    await page.close()
            except Exception as fallback_exc:
                self.add_result(
                    "Security Headers",
                    False,
                    "Could not read security headers",
                    warning=True,
                    details=[{
                        "type": "Security Header Scan Failed",
                        "page": url,
                        "status": "Failed",
                        "hint": f"API request: {truncate(first_exc)} | Browser fallback: {truncate(fallback_exc)}",
                    }],
                )
                self.print_status("Security Headers", False, "Could not read headers", warning=True)
                return

        for name in security_headers:
            security_headers[name] = headers.get(name.lower()) or headers.get(name)

        missing = [name for name, value in security_headers.items() if not value]
        present = [name for name, value in security_headers.items() if value]

        details.extend([
            {
                "type": "Security Header",
                "page": url,
                "target": name,
                "status": "Present" if security_headers[name] else "Missing",
                "source": source,
                "hint": "Missing security headers are warnings, not always critical for every site.",
            }
            for name in security_headers
        ])

        if missing:
            self.add_result(
                "Security Headers",
                False,
                f"Present: {len(present)}/{len(security_headers)}",
                warning=True,
                details=details,
            )
            self.print_status("Security Headers", False, f"Missing {len(missing)} header(s)", warning=True)
        else:
            self.add_result("Security Headers", True, "All common security headers present", details=details)
            self.print_status("Security Headers", True, "All headers present ✓")

    async def test_accessibility(self, page: Page, url: str) -> None:
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            issues = await page.evaluate("""() => {
                const result = [];
                document.querySelectorAll('img:not([alt]), img[alt=""]').forEach((img, index) => {
                    result.push({
                        type: 'Accessibility',
                        target: img.src || `image-${index + 1}`,
                        selector: img.id ? `img#${img.id}` : `img:nth-of-type(${index + 1})`,
                        status: 'Missing alt',
                        hint: 'Add descriptive alt text for screen readers.'
                    });
                });

                const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'));
                if (!headings.some(h => h.tagName === 'H1')) {
                    result.push({
                        type: 'Accessibility',
                        target: 'h1',
                        status: 'Missing H1',
                        hint: 'Add exactly one clear H1 heading for the page.'
                    });
                }

                document.querySelectorAll('input:not([type="hidden"]), textarea, select').forEach((input, index) => {
                    const hasAria = input.getAttribute('aria-label') || input.getAttribute('aria-labelledby');
                    const hasLabel = input.id ? document.querySelector(`label[for="${input.id}"]`) : null;
                    const wrapped = input.closest('label');
                    if (!hasAria && !hasLabel && !wrapped) {
                        result.push({
                            type: 'Accessibility',
                            target: input.name || input.id || `field-${index + 1}`,
                            selector: input.id ? `#${input.id}` : `${input.tagName.toLowerCase()}:nth-of-type(${index + 1})`,
                            status: 'Missing label',
                            hint: 'Connect field to a label or add aria-label.'
                        });
                    }
                });
                return result;
            }""")

            for item in issues:
                item["page"] = url

            if issues:
                self.add_result("Accessibility", False, f"{len(issues)} issue(s)", warning=True, details=issues[:120])
                self.print_status("Accessibility", True, f"{len(issues)} issue(s) found", warning=True)
            else:
                self.add_result("Accessibility", True, "Basic checks passed")
                self.print_status("Accessibility", True, "Basic checks passed ✓")
        except Exception as exc:
            self.add_result("Accessibility", False, truncate(exc), warning=True)
            self.print_status("Accessibility", False, truncate(exc, 80), warning=True)

    async def crawl_internal_pages(self, page: Page) -> List[Dict[str, Any]]:
        visited: Set[str] = set()
        queued: Set[str] = {clean_url(self.url)}
        queue: deque[Tuple[str, int]] = deque([(clean_url(self.url), 0)])
        pages: List[Dict[str, Any]] = []

        console.print(f"[dim]🔎 Crawling internal pages: max_pages={self.max_pages}, depth={self.depth}[/dim]")

        while queue and len(pages) < self.max_pages:
            current_url, current_depth = queue.popleft()
            if current_url in visited:
                continue
            visited.add(current_url)

            try:
                response = await page.goto(current_url, wait_until="domcontentloaded", timeout=30000)
                status = response.status if response else "No response"
                pages.append({"url": current_url, "status": status, "depth": current_depth})

                if current_depth >= self.depth:
                    continue

                links = await self.extract_links(page)
                for link in links:
                    href = clean_url(link.get("href", ""))
                    if not href or href in queued:
                        continue
                    if not same_domain(self.domain, href):
                        continue
                    if not is_probably_page(href):
                        continue
                    queued.add(href)
                    queue.append((href, current_depth + 1))

            except Exception as exc:
                pages.append({"url": current_url, "status": "Failed", "depth": current_depth, "hint": truncate(exc)})

        return pages

    async def extract_links(self, page: Page) -> List[Dict[str, Any]]:
        links = await page.evaluate("""() => {
            const makeSelector = (a, index) => {
                if (a.id) return `a#${a.id}`;
                if (a.getAttribute('aria-label')) return `a[aria-label="${a.getAttribute('aria-label')}"]`;
                if (a.className && typeof a.className === 'string') {
                    const classes = a.className.trim().split(/\\s+/).slice(0, 3).join('.');
                    if (classes) return `a.${classes}`;
                }
                return `a:nth-of-type(${index + 1})`;
            };

            return Array.from(document.querySelectorAll('a[href]')).map((a, index) => ({
                href: a.href,
                rawHref: a.getAttribute('href'),
                text: a.textContent.trim().substring(0, 120),
                selector: makeSelector(a, index),
                isExternal: !a.href.includes(window.location.hostname)
            })).filter(link => {
                const href = link.href || '';
                const raw = link.rawHref || '';
                return href.startsWith('http') && !raw.startsWith('mailto:') && !raw.startsWith('tel:') && !raw.startsWith('javascript:');
            });
        }""")
        return links or []

    async def test_links(self, context: BrowserContext, source_pages: List[str]) -> None:
        broken_links: List[Dict[str, Any]] = []
        checked: Set[str] = set()
        total_found = 0
        page = await context.new_page()

        try:
            for source_page in source_pages[: self.max_pages if self.mode == "full" else 1]:
                try:
                    await page.goto(source_page, wait_until="domcontentloaded", timeout=30000)
                    links = await self.extract_links(page)
                    total_found += len(links)

                    for link in links:
                        target = clean_url(link.get("href", ""))
                        if not target or target in checked:
                            continue

                        # Keep scan focused and safer: check internal links only.
                        if not same_domain(self.domain, target):
                            continue

                        checked.add(target)

                        try:
                            response = await context.request.get(target, timeout=15000, max_redirects=5)
                            status = response.status
                            if status >= 400:
                                broken_links.append({
                                    "type": "Broken Link",
                                    "page": source_page,
                                    "target": target,
                                    "status": status,
                                    "text": link.get("text") or "No text",
                                    "selector": link.get("selector"),
                                    "hint": f"Internal link returns HTTP {status}.",
                                })
                        except Exception as exc:
                            broken_links.append({
                                "type": "Broken Link",
                                "page": source_page,
                                "target": target,
                                "status": "Connection failed",
                                "text": link.get("text") or "No text",
                                "selector": link.get("selector"),
                                "hint": truncate(exc),
                            })
                except Exception as exc:
                    broken_links.append({
                        "type": "Page Link Scan Failed",
                        "page": source_page,
                        "target": source_page,
                        "status": "Failed",
                        "hint": truncate(exc),
                    })
        finally:
            await page.close()

        if broken_links:
            self.add_result(
                "Full Link Scan" if self.mode == "full" else "Link Check",
                False,
                f"{len(broken_links)} broken internal link(s) found from {len(checked)} checked",
                warning=True,
                details=broken_links[:200],
            )
            self.print_status("Link Check", False, f"{len(broken_links)} broken link(s)", warning=True)
        else:
            self.add_result(
                "Full Link Scan" if self.mode == "full" else "Link Check",
                True,
                f"No broken internal links — {len(checked)} checked, {total_found} found",
            )
            self.print_status("Link Check", True, f"{len(checked)} internal links checked")

    async def test_runtime_issues(self, context: BrowserContext, pages: List[str]) -> None:
        issues: List[Dict[str, Any]] = []
        pages_to_scan = pages[: self.max_pages if self.mode == "full" else 1]

        for url in pages_to_scan:
            page = await context.new_page()

            def on_console(msg):
                try:
                    msg_type = getattr(msg, "type", "")
                    if msg_type not in ("error", "warning"):
                        return
                    location = getattr(msg, "location", None) or {}
                    issues.append({
                        "type": "Console Error" if msg_type == "error" else "Console Warning",
                        "page": url,
                        "target": location.get("url") or "browser console",
                        "status": msg_type,
                        "line": location.get("lineNumber", "-"),
                        "column": location.get("columnNumber", "-"),
                        "text": truncate(getattr(msg, "text", ""), 500),
                        "hint": "Open DevTools console and check this source location.",
                    })
                except Exception:
                    # Event handlers must never raise; otherwise Playwright prints a huge internal traceback.
                    return

            def on_request_failed(request):
                try:
                    issues.append({
                        "type": "Network Request Failed",
                        "page": url,
                        "target": getattr(request, "url", "unknown request"),
                        "status": "Failed",
                        "method": getattr(request, "method", "-"),
                        "resource": getattr(request, "resource_type", "-"),
                        "hint": truncate(safe_request_failure_text(request)),
                    })
                except Exception:
                    return

            def on_response(response):
                try:
                    status = getattr(response, "status", 0)
                    if status >= 400:
                        # Ignore the actual document response here; page load test handles that.
                        issues.append({
                            "type": "Bad HTTP Response",
                            "page": url,
                            "target": getattr(response, "url", "unknown response"),
                            "status": status,
                            "resource": "network",
                            "hint": f"Request returned HTTP {status}.",
                        })
                except Exception:
                    return

            page.on("console", on_console)
            page.on("requestfailed", on_request_failed)
            page.on("response", on_response)

            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(1500)
            except Exception as exc:
                issues.append({
                    "type": "Runtime Scan Failed",
                    "page": url,
                    "target": url,
                    "status": "Failed",
                    "hint": truncate(exc),
                })
            finally:
                await page.close()

        # Deduplicate repeated issue signatures.
        deduped: List[Dict[str, Any]] = []
        seen: Set[Tuple[str, str, str, str]] = set()
        for item in issues:
            key = (
                str(item.get("type")),
                str(item.get("page")),
                str(item.get("target")),
                str(item.get("text") or item.get("status")),
            )
            if key not in seen:
                seen.add(key)
                deduped.append(item)

        if deduped:
            self.add_result(
                "Runtime Issues",
                False,
                f"{len(deduped)} console/network issue(s) found",
                warning=True,
                details=deduped[:250],
            )
            self.print_status("Runtime Issues", False, f"{len(deduped)} issue(s)", warning=True)
        else:
            self.add_result("Runtime Issues", True, "No console or network errors detected")
            self.print_status("Runtime Issues", True, "Clean runtime ✓")

    async def test_forms(self, page: Page, url: str) -> None:
        await self._test_forms_on_page(page, url, aggregate=False)

    async def test_forms_across_pages(self, context: BrowserContext, urls: List[str]) -> None:
        all_issues: List[Dict[str, Any]] = []
        forms_found = 0
        pages_to_scan = urls[: self.max_pages]

        for url in pages_to_scan:
            page = await context.new_page()
            try:
                result = await self._test_forms_on_page(page, url, aggregate=True)
                forms_found += result.get("forms_found", 0)
                all_issues.extend(result.get("issues", []))
            finally:
                await page.close()

        if all_issues:
            self.add_result(
                "Form Test",
                False,
                f"{forms_found} form(s), {len(all_issues)} issue(s)",
                warning=True,
                details=all_issues[:200],
            )
            self.print_status("Form Test", False, f"{forms_found} form(s), {len(all_issues)} issue(s)", warning=True)
        else:
            self.add_result("Form Test", True, f"{forms_found} form(s) checked safely")
            self.print_status("Form Test", True, f"{forms_found} form(s) checked safely")

    async def _test_forms_on_page(self, page: Page, url: str, aggregate: bool = False) -> Dict[str, Any]:
        issues: List[Dict[str, Any]] = []
        forms_found = 0
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            data = await page.evaluate("""() => {
                const makeFieldSelector = (field, index) => {
                    if (field.id) return `#${field.id}`;
                    if (field.name) return `${field.tagName.toLowerCase()}[name="${field.name}"]`;
                    return `${field.tagName.toLowerCase()}:nth-of-type(${index + 1})`;
                };

                return Array.from(document.querySelectorAll('form')).map((form, formIndex) => {
                    const fields = Array.from(form.querySelectorAll('input, textarea, select')).filter(field => {
                        const type = (field.getAttribute('type') || '').toLowerCase();
                        return !['hidden', 'submit', 'button', 'reset', 'image', 'file'].includes(type) && !field.disabled;
                    }).map((field, index) => {
                        const type = (field.getAttribute('type') || field.tagName || 'text').toLowerCase();
                        const hasLabel = field.id ? !!document.querySelector(`label[for="${field.id}"]`) : false;
                        const hasAria = !!(field.getAttribute('aria-label') || field.getAttribute('aria-labelledby'));
                        return {
                            selector: makeFieldSelector(field, index),
                            name: field.name || field.id || `field-${index + 1}`,
                            type,
                            required: !!field.required,
                            placeholder: field.getAttribute('placeholder') || '',
                            hasLabel: hasLabel || !!field.closest('label') || hasAria,
                        };
                    });

                    return {
                        index: formIndex + 1,
                        id: form.id || '',
                        action: form.action || '',
                        method: (form.method || 'get').toUpperCase(),
                        hasSubmit: !!form.querySelector('button[type="submit"], input[type="submit"], button:not([type])'),
                        fields,
                    };
                });
            }""")

            forms_found = len(data)
            if not data:
                if not aggregate:
                    self.add_result("Form Test", True, "No forms detected")
                    self.print_status("Form Test", True, "No forms on page")
                return {"forms_found": 0, "issues": []}

            for form in data:
                form_label = f"form #{form['index']}" + (f" ({form['id']})" if form.get("id") else "")

                if not form.get("hasSubmit"):
                    issues.append({
                        "type": "Form Issue",
                        "page": url,
                        "target": form_label,
                        "status": "Missing submit button",
                        "hint": "Add a submit button so users can submit this form clearly.",
                    })

                for field in form.get("fields", []):
                    if not field.get("hasLabel"):
                        issues.append({
                            "type": "Form Accessibility",
                            "page": url,
                            "target": field.get("name"),
                            "selector": field.get("selector"),
                            "status": "Missing label",
                            "hint": "Add label/aria-label so this field is accessible.",
                        })

            if self.test_forms:
                simulation_issues = await self.safe_fill_and_validate_forms(page, url)
                issues.extend(simulation_issues)

            if not aggregate:
                if issues:
                    self.add_result("Form Test", False, f"{forms_found} form(s), {len(issues)} issue(s)", warning=True, details=issues[:120])
                    self.print_status("Form Test", False, f"{forms_found} form(s), {len(issues)} issue(s)", warning=True)
                else:
                    self.add_result("Form Test", True, f"{forms_found} form(s) checked safely")
                    self.print_status("Form Test", True, f"{forms_found} form(s) checked safely")

            return {"forms_found": forms_found, "issues": issues}
        except Exception as exc:
            issue = {"type": "Form Scan Failed", "page": url, "status": "Failed", "hint": truncate(exc)}
            if not aggregate:
                self.add_result("Form Test", False, truncate(exc), warning=True, details=[issue])
                self.print_status("Form Test", False, truncate(exc, 80), warning=True)
            return {"forms_found": forms_found, "issues": [issue]}

    async def safe_fill_and_validate_forms(self, page: Page, url: str) -> List[Dict[str, Any]]:
        """
        Safely fill forms with dummy data and validate HTML5 constraints.
        It prevents real submission, so it will not create bookings/messages/orders.
        """
        try:
            return await page.evaluate("""() => {
                const issues = [];
                const dummy = {
                    email: 'lilo.tester@example.com',
                    tel: '081234567890',
                    number: '1',
                    date: '2026-01-01',
                    time: '10:00',
                    url: 'https://example.com',
                    password: 'LiloTester123!',
                    text: 'Lilo Tester automated safe form check',
                    search: 'test',
                };

                document.querySelectorAll('form').forEach((form, formIndex) => {
                    const formName = form.id || form.getAttribute('name') || `form-${formIndex + 1}`;

                    form.addEventListener('submit', event => {
                        event.preventDefault();
                        event.stopImmediatePropagation();
                    }, true);

                    const fields = Array.from(form.querySelectorAll('input, textarea, select')).filter(field => {
                        const type = (field.getAttribute('type') || '').toLowerCase();
                        return !['hidden', 'submit', 'button', 'reset', 'image', 'file', 'checkbox', 'radio'].includes(type) && !field.disabled && !field.readOnly;
                    });

                    fields.forEach((field, index) => {
                        try {
                            const tag = field.tagName.toLowerCase();
                            const type = (field.getAttribute('type') || 'text').toLowerCase();

                            if (tag === 'select') {
                                const option = Array.from(field.options).find(opt => !opt.disabled && opt.value !== '');
                                if (option) field.value = option.value;
                            } else if (tag === 'textarea') {
                                field.value = dummy.text;
                            } else {
                                field.value = dummy[type] || dummy.text;
                            }

                            field.dispatchEvent(new Event('input', { bubbles: true }));
                            field.dispatchEvent(new Event('change', { bubbles: true }));
                        } catch (err) {
                            issues.push({
                                type: 'Form Fill Failed',
                                page: window.location.href,
                                target: field.name || field.id || `field-${index + 1}`,
                                selector: field.id ? `#${field.id}` : (field.name ? `${field.tagName.toLowerCase()}[name="${field.name}"]` : `${field.tagName.toLowerCase()}:nth-of-type(${index + 1})`),
                                status: 'Failed',
                                hint: String(err)
                            });
                        }
                    });

                    const valid = form.checkValidity();
                    if (!valid) {
                        Array.from(form.elements).forEach((field, index) => {
                            if (field.willValidate && !field.validity.valid) {
                                issues.push({
                                    type: 'Form Validation',
                                    page: window.location.href,
                                    target: field.name || field.id || `field-${index + 1}`,
                                    selector: field.id ? `#${field.id}` : (field.name ? `${field.tagName.toLowerCase()}[name="${field.name}"]` : `${field.tagName.toLowerCase()}:nth-of-type(${index + 1})`),
                                    status: 'Invalid after dummy fill',
                                    text: field.validationMessage || '',
                                    hint: 'Field is still invalid after safe dummy fill. Check required/type/pattern/min/max rules.'
                                });
                            }
                        });
                    }

                    try {
                        const submitEvent = new Event('submit', { bubbles: true, cancelable: true });
                        form.dispatchEvent(submitEvent);
                    } catch (err) {
                        issues.push({
                            type: 'Form Submit Simulation Failed',
                            page: window.location.href,
                            target: formName,
                            status: 'Failed',
                            hint: String(err)
                        });
                    }
                });
                return issues;
            }""")
        except Exception as exc:
            return [{"type": "Form Safe Fill Failed", "page": url, "status": "Failed", "hint": truncate(exc)}]

    async def _prepare_page_for_screenshot(self, page: Page, viewport: Dict[str, int]) -> None:
        """Open the page in a screenshot-safe way.

        Some modern websites never reach Playwright's `networkidle` state because
        analytics, chat widgets, long polling, or tracking pixels keep network
        requests alive. This helper falls back to `domcontentloaded`, waits a bit,
        scrolls the page to trigger lazy-loaded content, then returns to top.
        """
        await page.set_viewport_size({"width": viewport["width"], "height": viewport["height"]})

        try:
            await page.goto(self.url, wait_until="networkidle", timeout=45000)
        except Exception as first_error:
            try:
                await page.goto(self.url, wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_timeout(2500)
            except Exception as second_error:
                raise RuntimeError(
                    f"Could not prepare page for screenshot. networkidle failed: {truncate(first_error, 140)}; "
                    f"domcontentloaded failed: {truncate(second_error, 140)}"
                )

        try:
            await page.evaluate("""async () => {
                await new Promise((resolve) => {
                    const height = Math.max(
                        document.body?.scrollHeight || 0,
                        document.documentElement?.scrollHeight || 0
                    );
                    let current = 0;
                    const step = Math.max(500, Math.floor(window.innerHeight * 0.75));
                    const timer = setInterval(() => {
                        window.scrollBy(0, step);
                        current += step;
                        if (current >= height) {
                            clearInterval(timer);
                            window.scrollTo(0, 0);
                            setTimeout(resolve, 700);
                        }
                    }, 120);
                });
            }""")
        except Exception:
            # Scrolling is only an enhancement. Screenshot should still continue.
            pass

        await page.wait_for_timeout(700)

    async def _capture_screenshot_file(
        self,
        context: BrowserContext,
        label: str,
        filename: str,
        viewport: Dict[str, int],
        full_page: bool = True,
    ) -> Dict[str, Any]:
        """Capture one screenshot and register it for the HTML report."""
        screenshot_path = self.screenshots_dir / filename
        page = await context.new_page()

        try:
            await self._prepare_page_for_screenshot(page, viewport)
            await page.screenshot(
                path=str(screenshot_path),
                full_page=full_page,
                animations="disabled",
                timeout=45000,
            )

            if not screenshot_path.exists() or screenshot_path.stat().st_size == 0:
                raise RuntimeError("Screenshot file was not created or is empty.")

            # Watermark failure should not make the screenshot test fail.
            self.watermark.apply(str(screenshot_path))

            item = {
                "type": "Screenshot",
                "label": label,
                "page": self.url,
                "target": f"screenshots/{filename}",
                "filename": filename,
                "status": "Captured",
                "viewport": f"{viewport['width']}x{viewport['height']}",
                "hint": f"Saved at screenshots/{filename}",
            }
            self.results["screenshots"].append(item)
            return item

        except Exception as exc:
            return {
                "type": "Screenshot",
                "label": label,
                "page": self.url,
                "target": f"screenshots/{filename}",
                "filename": filename,
                "status": "Failed",
                "viewport": f"{viewport['width']}x{viewport['height']}",
                "hint": truncate(exc),
            }
        finally:
            await page.close()

    async def test_responsive(self, context: BrowserContext) -> None:
        details: List[Dict[str, Any]] = []

        for device_key in self.devices:
            config = self.device_configs.get(device_key)
            if not config:
                continue

            filename = f"{device_key}_{self.timestamp}.png"
            details.append(await self._capture_screenshot_file(
                context=context,
                label=config["name"],
                filename=filename,
                viewport={"width": config["width"], "height": config["height"]},
                full_page=True,
            ))

        failed = [item for item in details if item.get("status") == "Failed"]
        captured = [item for item in details if item.get("status") == "Captured"]

        if failed:
            self.add_result(
                "Responsive Screenshots",
                False,
                f"{len(captured)} captured, {len(failed)} failed",
                warning=True,
                details=details,
            )
            self.print_status("Responsive Screenshots", False, f"{len(captured)} captured, {len(failed)} failed", warning=True)
        else:
            self.add_result("Responsive Screenshots", True, f"{len(captured)} device screenshot(s) captured", details=details)
            self.print_status("Responsive Screenshots", True, f"{len(captured)} captured")

    async def capture_full_page(self, context: BrowserContext) -> None:
        filename = f"fullpage_{self.timestamp}.png"
        item = await self._capture_screenshot_file(
            context=context,
            label="Full Page",
            filename=filename,
            viewport={"width": 1920, "height": 1080},
            full_page=True,
        )

        if item.get("status") == "Captured":
            self.add_result("Full Page Screenshot", True, "Captured full page screenshot", details=[item])
            self.print_status("Full Page Screenshot", True, "Captured")
        else:
            self.add_result("Full Page Screenshot", False, "Failed to capture full page screenshot", warning=True, details=[item])
            self.print_status("Full Page Screenshot", False, truncate(item.get("hint"), 80), warning=True)

    def save_json_report(self) -> Path:
        json_path = self.report_dir / "report.json"
        with open(json_path, "w", encoding="utf-8") as file:
            json.dump(self.results, file, ensure_ascii=False, indent=2)
        return json_path

    def generate_html_report(self) -> Path:
        env = Environment(loader=BaseLoader(), autoescape=select_autoescape(["html", "xml"]))
        template = env.from_string(REPORT_TEMPLATE)
        report_path = self.report_dir / "report.html"
        with open(report_path, "w", encoding="utf-8") as file:
            file.write(template.render(results=self.results))
        return report_path

    def _open_report(self, report_path: Path) -> None:
        try:
            webbrowser.open(f"file://{report_path.absolute()}")
            console.print("[dim]📂 Report opened in browser[/dim]")
        except Exception:
            pass

    def print_summary(self) -> None:
        console.print("\n" + "=" * 60)
        summary_text = Text()
        summary_text.append("📊 TEST SUMMARY\n", style="bold cyan")
        summary_text.append("─" * 40 + "\n", style="dim")
        summary_text.append(f"Mode:          {self.results['mode'].upper()}\n")
        summary_text.append(f"Total Tests:   {len(self.results['tests'])}\n")
        summary_text.append(f"✅ Passed:     {self.results['passed']}\n", style="green")
        summary_text.append(f"❌ Failed:     {self.results['failed']}\n", style="red")
        summary_text.append(f"⚠️  Warnings:  {self.results['warnings']}\n", style="yellow")
        summary_text.append(f"⏱️  Duration:  {self.results['total_time']:.2f}s\n")
        summary_text.append(f"💻 Platform:   {platform.system()}\n", style="dim")

        panel = Panel(summary_text, title=f"[bold]{APP_NAME}[/bold]", border_style="cyan", padding=(1, 2))
        console.print(panel)

        if self.results["failed"] == 0 and self.results["warnings"] == 0:
            console.print("[bold green]🎉 PERFECT! All tests passed![/bold green]")
        elif self.results["failed"] == 0:
            console.print(f"[bold yellow]⚠️ {self.results['warnings']} warning(s), but no critical failures.[/bold yellow]")
        else:
            console.print(f"[bold red]💀 {self.results['failed']} failed test(s). Check report for details.[/bold red]")


# ═══════════════════════════════════════════
# HTML REPORT TEMPLATE
# ═══════════════════════════════════════════

REPORT_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ results.app_name }} Report - {{ results.domain }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        :root {
            --bg-1: #060816;
            --bg-2: #111827;
            --card: rgba(255,255,255,0.92);
            --muted: #667085;
            --text: #101828;
            --line: #e5e7eb;
            --brand: #667eea;
            --brand-2: #764ba2;
            --green: #12b76a;
            --red: #f04438;
            --yellow: #f79009;
        }
        body {
            font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Ubuntu, sans-serif;
            background:
                radial-gradient(circle at 15% 10%, rgba(102,126,234,.35), transparent 28%),
                radial-gradient(circle at 85% 0%, rgba(118,75,162,.32), transparent 30%),
                linear-gradient(135deg, var(--bg-1), var(--bg-2));
            min-height: 100vh;
            color: var(--text);
            padding: 28px;
        }
        .container {
            max-width: 1180px;
            margin: 0 auto;
            background: rgba(255,255,255,0.82);
            border: 1px solid rgba(255,255,255,.45);
            border-radius: 28px;
            box-shadow: 0 30px 100px rgba(0,0,0,.38);
            overflow: hidden;
            backdrop-filter: blur(18px);
        }
        .header {
            position: relative;
            overflow: hidden;
            padding: 58px 44px;
            color: white;
            background: linear-gradient(135deg, var(--brand), var(--brand-2));
        }
        .header::before {
            content: '';
            position: absolute;
            inset: -45%;
            background: radial-gradient(circle, rgba(255,255,255,.18), transparent 62%);
            animation: rotate 24s linear infinite;
        }
        @keyframes rotate { to { transform: rotate(360deg); } }
        .header-content { position: relative; z-index: 1; }
        .eyebrow {
            display: inline-flex;
            gap: 8px;
            align-items: center;
            padding: 8px 14px;
            border-radius: 999px;
            background: rgba(255,255,255,.16);
            border: 1px solid rgba(255,255,255,.2);
            font-size: .9rem;
            margin-bottom: 18px;
        }
        h1 { font-size: clamp(2rem, 5vw, 4.2rem); line-height: 1; letter-spacing: -0.05em; margin-bottom: 16px; }
        .subtitle { font-size: 1.15rem; opacity: .92; max-width: 780px; line-height: 1.55; }
        .meta-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 14px;
            margin-top: 28px;
        }
        .meta-pill {
            padding: 13px 14px;
            border-radius: 16px;
            background: rgba(255,255,255,.13);
            border: 1px solid rgba(255,255,255,.18);
            overflow-wrap: anywhere;
        }
        .meta-pill span { display: block; opacity: .7; font-size: .78rem; margin-bottom: 4px; }
        .summary {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 18px;
            padding: 34px;
            background: #f8fafc;
            border-bottom: 1px solid var(--line);
        }
        .summary-card {
            background: white;
            padding: 24px;
            border-radius: 22px;
            box-shadow: 0 8px 25px rgba(15,23,42,.07);
            border: 1px solid #eef2f7;
        }
        .summary-card .number { font-size: 3rem; font-weight: 900; line-height: 1; letter-spacing: -0.06em; }
        .summary-card .label { margin-top: 8px; color: var(--muted); font-size: .85rem; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; }
        .total .number { color: var(--brand); }
        .passed .number { color: var(--green); }
        .failed .number { color: var(--red); }
        .warning .number { color: var(--yellow); }
        .section { padding: 38px; }
        .section-title {
            font-size: 1.45rem;
            margin-bottom: 22px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .section-title::before {
            content: '';
            width: 5px;
            height: 28px;
            border-radius: 999px;
            background: linear-gradient(180deg, var(--brand), var(--brand-2));
        }
        .test-list { display: grid; gap: 12px; }
        .test-item {
            display: grid;
            grid-template-columns: 44px 1fr auto;
            gap: 16px;
            align-items: start;
            padding: 18px;
            background: #fff;
            border: 1px solid #eef2f7;
            border-radius: 18px;
            box-shadow: 0 6px 18px rgba(15,23,42,.045);
        }
        .icon { width: 44px; height: 44px; border-radius: 14px; display: grid; place-items: center; background: #f8fafc; font-size: 1.35rem; }
        .name { font-weight: 800; font-size: 1rem; }
        .message { color: var(--muted); font-size: .92rem; margin-top: 4px; line-height: 1.5; }
        .time { color: #98a2b3; font-size: .82rem; padding-top: 4px; }
        details.test-details { margin-top: 13px; }
        details.test-details > summary {
            cursor: pointer;
            display: inline-flex;
            padding: 8px 11px;
            border-radius: 999px;
            background: #eef2ff;
            color: #4f46e5;
            font-size: .86rem;
            font-weight: 800;
            user-select: none;
        }
        .detail-list { margin-top: 12px; display: grid; gap: 10px; }
        .detail-card {
            padding: 14px;
            border-radius: 14px;
            background: #f8fafc;
            border: 1px solid #e5e7eb;
            border-left: 5px solid var(--brand);
            font-size: .9rem;
            line-height: 1.55;
        }
        .detail-row { margin-bottom: 5px; }
        .detail-row:last-child { margin-bottom: 0; }
        .detail-row strong { color: #111827; }
        .code {
            display: inline-block;
            max-width: 100%;
            word-break: break-all;
            color: #344054;
            background: white;
            border: 1px solid #e5e7eb;
            padding: 2px 6px;
            border-radius: 7px;
        }
        .screenshots-section { background: #f8fafc; border-top: 1px solid var(--line); }
        .screenshot-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
        }
        .screenshot-card {
            background: white;
            border-radius: 20px;
            overflow: hidden;
            border: 1px solid #eef2f7;
            box-shadow: 0 8px 25px rgba(15,23,42,.07);
        }
        .device-name { padding: 14px 16px; font-weight: 900; color: var(--brand); letter-spacing: .04em; font-size: .82rem; text-transform: uppercase; }
        .screenshot-card img { width: 100%; display: block; border-top: 1px solid #eef2f7; }
        .footer {
            color: white;
            text-align: center;
            padding: 30px;
            background: linear-gradient(135deg, var(--brand), var(--brand-2));
        }
        .footer .brand { font-weight: 900; font-size: 1.15rem; margin-bottom: 5px; }
        .footer .info { opacity: .82; font-size: .9rem; }
        @media (max-width: 820px) {
            body { padding: 14px; }
            .summary, .meta-grid { grid-template-columns: repeat(2, 1fr); }
            .section { padding: 24px; }
            .test-item { grid-template-columns: 36px 1fr; }
            .time { grid-column: 2; }
        }
        @media (max-width: 520px) {
            .summary, .meta-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <main class="container">
        <header class="header">
            <div class="header-content">
                <div class="eyebrow">🦊 {{ results.app_name }} v{{ results.version }}</div>
                <h1>Automation Test Report</h1>
                <p class="subtitle">A complete diagnostic snapshot for performance, SEO, links, runtime issues, forms, accessibility, and responsive screenshots.</p>
                <div class="meta-grid">
                    <div class="meta-pill"><span>Target</span>{{ results.url }}</div>
                    <div class="meta-pill"><span>Mode</span>{{ results.mode | upper }}</div>
                    <div class="meta-pill"><span>Platform</span>{{ results.os | upper }}</div>
                    <div class="meta-pill"><span>Generated</span>{{ results.timestamp }}</div>
                </div>
            </div>
        </header>

        <section class="summary">
            <div class="summary-card total"><div class="number">{{ results.tests | length }}</div><div class="label">Total Tests</div></div>
            <div class="summary-card passed"><div class="number">{{ results.passed }}</div><div class="label">Passed</div></div>
            <div class="summary-card failed"><div class="number">{{ results.failed }}</div><div class="label">Failed</div></div>
            <div class="summary-card warning"><div class="number">{{ results.warnings }}</div><div class="label">Warnings</div></div>
        </section>

        <section class="section">
            <h2 class="section-title">Detailed Test Results</h2>
            <div class="test-list">
                {% for test in results.tests %}
                <article class="test-item">
                    <div class="icon">{% if test.warning %}⚠️{% elif test.passed %}✅{% else %}❌{% endif %}</div>
                    <div class="info">
                        <div class="name">{{ test.name }}</div>
                        {% if test.message %}<div class="message">{{ test.message }}</div>{% endif %}

                        {% if test.details and test.details|length > 0 %}
                        <details class="test-details">
                            <summary>View {{ test.details|length }} detail(s)</summary>
                            <div class="detail-list">
                                {% for item in test.details %}
                                <div class="detail-card">
                                    {% for key, value in item.items() %}
                                        {% if value is not none and value != '' %}
                                        <div class="detail-row">
                                            <strong>{{ key | replace('_', ' ') | title }}:</strong>
                                            <span class="code">{{ value }}</span>
                                        </div>
                                        {% endif %}
                                    {% endfor %}
                                </div>
                                {% endfor %}
                            </div>
                        </details>
                        {% endif %}
                    </div>
                    <div class="time">{{ test.time }}</div>
                </article>
                {% endfor %}
            </div>
        </section>

        <section class="section screenshots-section">
            <h2 class="section-title">Screenshots</h2>
            {% if results.screenshots and results.screenshots|length > 0 %}
            <div class="screenshot-grid">
                {% for shot in results.screenshots %}
                <div class="screenshot-card">
                    <div class="device-name">{{ shot.label }} • {{ shot.viewport }}</div>
                    <img src="{{ shot.target }}" alt="{{ shot.label }} screenshot" onerror="this.parentElement.style.display='none'">
                </div>
                {% endfor %}
            </div>
            {% else %}
            <div class="detail-card">
                <strong>No screenshot files were captured.</strong><br>
                Check the "Responsive Screenshots" and "Full Page Screenshot" detail dropdowns above for the exact failure reason.
            </div>
            {% endif %}
        </section>

        <footer class="footer">
            <div class="brand">🦊 {{ results.app_name }}</div>
            <div class="info">Web Automation Testing Suite • Universal Edition</div>
        </footer>
    </main>
</body>
</html>
"""


# ═══════════════════════════════════════════
# CLI ENTRY POINT
# ═══════════════════════════════════════════

async def main_async() -> None:
    parser = argparse.ArgumentParser(
        description="🦊 Lilo Tester - Web Automation Testing Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  liloit -u example.com
  liloit -u example.com --mode quick
  liloit -u example.com --mode full --max-pages 30 --depth 2
  liloit -u example.com -d desktop mobile
  liloit -u example.com --no-headless

Notes:
  If --mode is not provided, Lilo Tester will ask you to choose Quick Scan or Full Scan.
  Form testing is safe by default: it fills dummy data and prevents real submission.
        """,
    )

    parser.add_argument("--url", "-u", required=True, help="Target website URL")
    parser.add_argument("--output", "-o", default="lilo_reports", help="Output directory")
    parser.add_argument("--mode", choices=["quick", "full"], help="Scan mode. If omitted, you will be asked interactively.")
    parser.add_argument("--full-scan", action="store_true", help="Shortcut for --mode full")
    parser.add_argument("--max-pages", type=int, default=25, help="Maximum internal pages for full scan")
    parser.add_argument("--depth", type=int, default=1, help="Internal crawl depth for full scan")
    parser.add_argument(
        "--devices",
        "-d",
        nargs="+",
        default=["desktop", "tablet", "mobile"],
        choices=["desktop", "tablet", "mobile"],
        help="Devices to screenshot/test",
    )
    parser.add_argument("--no-headless", action="store_true", help="Show browser window while testing")
    parser.add_argument("--no-form-test", action="store_true", help="Disable safe dummy form fill validation")
    parser.add_argument("--no-open-report", action="store_true", help="Do not open report automatically")

    args = parser.parse_args()

    if args.full_scan:
        mode = "full"
    elif args.mode:
        mode = args.mode
    else:
        if sys.stdin.isatty():
            mode = Prompt.ask("Choose scan mode", choices=["quick", "full"], default="quick")
        else:
            mode = "quick"

    tester = LiloTester(
        url=args.url,
        output_dir=args.output,
        devices=args.devices,
        headless=not args.no_headless,
        mode=mode,
        max_pages=args.max_pages,
        depth=args.depth,
        test_forms=not args.no_form_test,
        open_report=not args.no_open_report,
    )

    await tester.run()


def cli() -> None:
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        console.print("\n[yellow]Scan cancelled by user.[/yellow]")


if __name__ == "__main__":
    cli()
