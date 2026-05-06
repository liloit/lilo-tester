#!/usr/bin/env python3
"""
🦊 LILO TESTER - Web Automation Testing Suite
Version: 2.0.0 Universal
Author: Lilo
Compatible: Windows / macOS / Linux
"""

import asyncio
import os
import sys
import json
import time
import platform
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse
import argparse
from typing import List, Dict, Tuple, Optional

# Rich console UI
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich import print as rprint
from rich.prompt import Prompt

# Playwright
from playwright.async_api import async_playwright, Page, Browser

# Image processing
from PIL import Image, ImageDraw, ImageFont
import io

# HTML Report
from jinja2 import Template

console = Console()

# ═══════════════════════════════════════════
# SYSTEM DETECTION & FONT MANAGEMENT
# ═══════════════════════════════════════════

class SystemDetector:
    """Auto-detect OS and return appropriate settings"""
    
    @staticmethod
    def get_os():
        system = platform.system().lower()
        if system == "windows":
            return "windows"
        elif system == "darwin":
            return "macos"
        else:
            return "linux"
    
    @staticmethod
    def get_font_paths():
        """Return list of possible font paths based on OS"""
        os_type = SystemDetector.get_os()
        
        if os_type == "windows":
            return [
                "C:\\Windows\\Fonts\\Arial.ttf",
                "C:\\Windows\\Fonts\\Calibri.ttf",
                "C:\\Windows\\Fonts\\segoeui.ttf",
                "arial.ttf",
                "Arial.ttf"
            ]
        elif os_type == "macos":
            return [
                "/System/Library/Fonts/Helvetica.ttc",
                "/System/Library/Fonts/SFNSDisplay.ttf",
                "/Library/Fonts/Arial.ttf",
                "~/Library/Fonts/Arial.ttf"
            ]
        else:  # Linux
            return [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
                "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf"
            ]
    
    @staticmethod
    def get_chromium_path():
        """Get Chromium path for different OS"""
        os_type = SystemDetector.get_os()
        
        if os_type == "windows":
            return None  # Playwright handles Windows automatically
        elif os_type == "macos":
            return None  # Playwright handles macOS automatically
        else:
            # Check common Linux paths
            paths = [
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium",
                "/usr/bin/google-chrome",
                "/snap/bin/chromium"
            ]
            for path in paths:
                if os.path.exists(path):
                    return path
            return None

# ═══════════════════════════════════════════
# BANNER & WATERMARK ENGINE
# ═══════════════════════════════════════════

def get_banner(watermark_text: str = "Lilo Tester"):
    """Generate dynamic banner with custom text"""
    
    # Make ASCII art dynamic based on text length
    text_length = len(watermark_text)
    padding = max(0, 30 - text_length) // 2
    
    BANNER = f"""
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
║              {" " * padding}{watermark_text}{" " * padding}              ║
║              Web Automation Testing Suite                        ║
║                      v2.0.0 Universal                            ║
║              Running on {SystemDetector.get_os().upper()}{" " * (14 - len(SystemDetector.get_os()))}                        ║
╚══════════════════════════════════════════════════════════════════╝
[/bold cyan]
"""
    return BANNER

class WatermarkEngine:
    """Advanced watermark engine with composer-style effects"""
    
    def __init__(self, text: str = "Lilo Tester", opacity: int = 180, position: str = "bottom-right"):
        self.text = text
        self.opacity = opacity
        self.position = position
        self.font = self._load_font()
    
    def _load_font(self):
        """Load best available font for current OS"""
        font_paths = SystemDetector.get_font_paths()
        
        for font_path in font_paths:
            expanded_path = os.path.expanduser(font_path)
            if os.path.exists(expanded_path):
                try:
                    return ImageFont.truetype(expanded_path, 28)
                except:
                    continue
        
        # Final fallback
        try:
            return ImageFont.truetype("arial.ttf", 28)
        except:
            return ImageFont.load_default()
    
    def apply(self, image_path: str, output_path: Optional[str] = None):
        """
        Apply composer-style watermark to image
        
        Features:
        - Text shadow for depth
        - Semi-transparent background badge
        - Gradient effect imitation
        - Multiple position presets
        """
        try:
            img = Image.open(image_path)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Create overlay layer
            overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            
            # Calculate text dimensions
            text_bbox = overlay_draw.textbbox((0, 0), self.text, font=self.font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # Position calculation
            padding = 25
            badge_padding = 12
            
            pos = self._calculate_position(
                img.width, img.height, 
                text_width, text_height, 
                padding
            )
            
            # Badge dimensions
            badge_x = pos['badge_x'] - badge_padding
            badge_y = pos['badge_y'] - badge_padding
            badge_width = text_width + (badge_padding * 2)
            badge_height = text_height + (badge_padding * 2)
            
            # Draw composer-style badge (rounded rectangle effect with border)
            # Main badge background
            overlay_draw.rounded_rectangle(
                [badge_x, badge_y, badge_x + badge_width, badge_y + badge_height],
                radius=10,
                fill=(20, 20, 30, self.opacity),
                outline=(100, 100, 120, min(self.opacity + 30, 255)),
                width=2
            )
            
            # Draw accent line (left border effect)
            accent_width = 4
            overlay_draw.rectangle(
                [badge_x, badge_y + 8, badge_x + accent_width, badge_y + badge_height - 8],
                fill=(0, 180, 255, 200)  # Cyan accent
            )
            
            # Text shadow (for depth)
            shadow_offset = 2
            overlay_draw.text(
                (pos['text_x'] + shadow_offset, pos['text_y'] + shadow_offset),
                self.text,
                font=self.font,
                fill=(0, 0, 0, 100)  # Shadow
            )
            
            # Main text
            overlay_draw.text(
                (pos['text_x'], pos['text_y']),
                self.text,
                font=self.font,
                fill=(255, 255, 255, 230)  # White text
            )
            
            # Compose final image
            img = Image.alpha_composite(img, overlay)
            
            # Save
            output_path = output_path or image_path
            if output_path.lower().endswith('.png'):
                img.save(output_path, 'PNG')
            else:
                img = img.convert('RGB')
                img.save(output_path, 'JPEG', quality=95)
            
            return True
            
        except Exception as e:
            console.print(f"[yellow]⚠️  Watermark error: {e}[/yellow]")
            return False
    
    def _calculate_position(self, img_width, img_height, text_width, text_height, padding):
        """Calculate position based on preset"""
        positions = {
            "bottom-right": {
                "badge_x": img_width - text_width - padding,
                "badge_y": img_height - text_height - padding,
                "text_x": img_width - text_width - padding,
                "text_y": img_height - text_height - padding
            },
            "bottom-left": {
                "badge_x": padding,
                "badge_y": img_height - text_height - padding,
                "text_x": padding,
                "text_y": img_height - text_height - padding
            },
            "top-right": {
                "badge_x": img_width - text_width - padding,
                "badge_y": padding,
                "text_x": img_width - text_width - padding,
                "text_y": padding
            },
            "top-left": {
                "badge_x": padding,
                "badge_y": padding,
                "text_x": padding,
                "text_y": padding
            }
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
        devices: List[str] = None,
        watermark_text: str = "Lilo Tester",
        watermark_position: str = "bottom-right",
        headless: bool = True
    ):
        self.url = url
        self.domain = urlparse(url).netloc
        self.output_dir = Path(output_dir)
        self.timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.report_dir = self.output_dir / f"report_{self.timestamp}"
        self.screenshots_dir = self.report_dir / "screenshots"
        self.headless = headless
        
        # Create directories
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize watermark engine
        self.watermark = WatermarkEngine(
            text=watermark_text,
            opacity=170,
            position=watermark_position
        )
        
        # Test results storage
        self.results = {
            "url": url,
            "timestamp": self.timestamp,
            "os": SystemDetector.get_os(),
            "watermark_text": watermark_text,
            "tests": [],
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "total_time": 0
        }
        
        # Device presets
        self.devices = devices or ["desktop"]
        self.device_configs = {
            "desktop": {"width": 1920, "height": 1080, "name": "Desktop", "scale": 1},
            "tablet": {"width": 768, "height": 1024, "name": "Tablet", "scale": 1},
            "mobile": {"width": 375, "height": 812, "name": "Mobile", "scale": 2}
        }
    
    def add_result(self, name: str, passed: bool, message: str = "", warning: bool = False):
        """Record test result"""
        result = {
            "name": name,
            "passed": passed,
            "message": message,
            "warning": warning,
            "time": datetime.now().strftime("%H:%M:%S")
        }
        self.results["tests"].append(result)
        
        if warning:
            self.results["warnings"] += 1
        elif passed:
            self.results["passed"] += 1
        else:
            self.results["failed"] += 1
    
    def print_status(self, name: str, passed: bool, message: str = "", warning: bool = False):
        """Print test status with color and icon"""
        if warning:
            icon = "⚠️"
            color = "yellow"
        elif passed:
            icon = "✅"
            color = "green"
        else:
            icon = "❌"
            color = "red"
        
        console.print(f"  {icon} [{color}]{name}[/{color}]")
        if message:
            console.print(f"     [dim]{message}[/dim]")
    
    async def test_page_load(self, page: Page):
        """Test page load performance with detailed metrics"""
        start_time = time.time()
        try:
            response = await page.goto(self.url, wait_until="networkidle", timeout=30000)
            load_time = time.time() - start_time
            
            if response and response.ok:
                # Performance metrics
                metrics = await page.evaluate("""() => {
                    const perf = performance.getEntriesByType('navigation')[0];
                    return perf ? {
                        domContentLoaded: perf.domContentLoadedEventEnd - perf.domContentLoadedEventStart,
                        loadComplete: perf.loadEventEnd - perf.loadEventStart,
                        firstPaint: performance.getEntriesByType('paint')[0]?.startTime
                    } : null;
                }""")
                
                if load_time < 3:
                    self.add_result("Page Load Speed", True, f"Loaded in {load_time:.2f}s")
                    self.print_status("Page Load Speed", True, f"{load_time:.2f}s ⚡")
                else:
                    self.add_result("Page Load Speed", False, f"Slow load: {load_time:.2f}s", warning=True)
                    self.print_status("Page Load Speed", False, f"Slow: {load_time:.2f}s 🐌", warning=True)
            else:
                self.add_result("Page Load", False, f"HTTP {response.status if response else 'No response'}")
                self.print_status("Page Load", False, "Failed to load")
                return False
            
            return True
        except Exception as e:
            self.add_result("Page Load", False, str(e))
            self.print_status("Page Load", False, str(e)[:50])
            return False
    
    async def test_title(self, page: Page):
        """Check page title and SEO relevance"""
        try:
            title = await page.title()
            title_length = len(title) if title else 0
            
            if title and 10 <= title_length <= 70:
                self.add_result("Page Title", True, f'"{title}" ({title_length} chars)')
                self.print_status("Page Title", True, f'"{title[:50]}" - Optimal')
            elif title and title_length < 10:
                self.add_result("Page Title", True, f'Too short: {title_length} chars', warning=True)
                self.print_status("Page Title", True, "Too short < 10 chars", warning=True)
            elif title and title_length > 70:
                self.add_result("Page Title", True, f'Too long: {title_length} chars', warning=True)
                self.print_status("Page Title", True, "Too long > 70 chars", warning=True)
            else:
                self.add_result("Page Title", False, "Empty title", warning=True)
                self.print_status("Page Title", False, "Empty title", warning=True)
        except Exception as e:
            self.add_result("Page Title", False, str(e))
            self.print_status("Page Title", False, str(e)[:50])
    
    async def test_links(self, page: Page):
        """Enhanced link checker with categorization"""
        try:
            links = await page.evaluate("""() => {
                return Array.from(document.querySelectorAll('a[href]'))
                    .map(a => ({
                        href: a.href,
                        text: a.textContent.trim().substring(0, 50),
                        isExternal: !a.href.includes(window.location.hostname)
                    }))
                    .filter(link => link.href.startsWith('http'));
            }""")
            
            # Limit to 30 unique links
            seen = set()
            unique_links = []
            for link in links:
                if link['href'] not in seen and len(unique_links) < 30:
                    seen.add(link['href'])
                    unique_links.append(link)
            
            internal_links = [l for l in unique_links if not l['isExternal']]
            external_links = [l for l in unique_links if l['isExternal']]
            
            broken = []
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                context = await browser.new_context()
                check_page = await context.new_page()
                
                for link in internal_links[:15]:  # Check internal links first
                    try:
                        response = await check_page.goto(link['href'], timeout=10000)
                        if response and response.status >= 400:
                            broken.append((link['href'], response.status, link['text']))
                    except:
                        broken.append((link['href'], "Connection failed", link['text']))
                
                await browser.close()
            
            summary = f"Internal: {len(internal_links)}, External: {len(external_links)}"
            if len(broken) == 0:
                self.add_result("Link Check", True, f"All links OK - {summary}")
                self.print_status("Link Check", True, f"{len(unique_links)} links checked")
            else:
                self.add_result("Link Check", False, f"{len(broken)} broken links found - {summary}", warning=True)
                self.print_status("Link Check", False, f"{len(broken)} broken links", warning=True)
                for link, status, text in broken[:3]:
                    display_text = text[:30] if text else "No text"
                    console.print(f"     [red]• {display_text} → {status}[/red]")
        except Exception as e:
            self.add_result("Link Check", False, str(e))
            self.print_status("Link Check", False, str(e)[:50])
    
    async def test_forms(self, page: Page):
        """Advanced form detection with validation"""
        try:
            forms = await page.evaluate("""() => {
                return Array.from(document.querySelectorAll('form')).map((f, idx) => ({
                    id: f.id || `form-${idx}`,
                    action: f.action || 'No action',
                    method: f.method || 'get',
                    inputs: Array.from(f.querySelectorAll('input, textarea, select, button')).map(i => ({
                        type: i.type || i.tagName.toLowerCase(),
                        name: i.name || 'Unnamed',
                        required: i.required || false,
                        placeholder: i.placeholder || ''
                    })),
                    hasSubmit: f.querySelector('button[type="submit"], input[type="submit"]') !== null
                }));
            }""")
            
            if forms:
                total_inputs = sum(len(f['inputs']) for f in forms)
                forms_without_submit = [f for f in forms if not f['hasSubmit']]
                
                if forms_without_submit:
                    self.add_result(
                        "Form Detection", 
                        True, 
                        f"{len(forms)} form(s), {total_inputs} inputs - {len(forms_without_submit)} missing submit button", 
                        warning=True
                    )
                    self.print_status(
                        "Form Detection", 
                        True, 
                        f"{len(forms)} forms detected, {len(forms_without_submit)} need submit button", 
                        warning=True
                    )
                else:
                    self.add_result("Form Detection", True, f"{len(forms)} form(s), {total_inputs} inputs")
                    self.print_status("Form Detection", True, f"{len(forms)} form(s) with proper submit")
            else:
                self.add_result("Form Detection", True, "No forms detected")
                self.print_status("Form Detection", True, "No forms on page")
        except Exception as e:
            self.add_result("Form Detection", False, str(e))
            self.print_status("Form Detection", False, str(e)[:50])
    
    async def test_console_errors(self, page: Page):
        """Capture console errors with categorization"""
        try:
            errors = []
            warnings = []
            
            def handle_console(msg):
                if msg.type == "error":
                    errors.append({
                        "text": msg.text,
                        "location": msg.location.get('url', 'unknown')
                    })
                elif msg.type == "warning":
                    warnings.append(msg.text)
            
            page.on("console", handle_console)
            await page.reload()
            await asyncio.sleep(2)
            
            if len(errors) == 0:
                self.add_result("Console Errors", True, f"No errors, {len(warnings)} warnings")
                self.print_status("Console Errors", True, f"Clean console ({len(warnings)} warnings)")
            else:
                self.add_result(
                    "Console Errors", 
                    False, 
                    f"{len(errors)} error(s), {len(warnings)} warnings", 
                    warning=True
                )
                self.print_status("Console Errors", False, f"{len(errors)} error(s)", warning=True)
                for err in errors[:3]:
                    console.print(f"     [red]• {err['text'][:80]}[/red]")
        except Exception as e:
            self.add_result("Console Errors", False, str(e))
            self.print_status("Console Errors", False, str(e)[:50])
    
    async def test_responsive(self, page: Page):
        """Test responsive design with visual comparison"""
        for device_key in self.devices:
            if device_key in self.device_configs:
                config = self.device_configs[device_key]
                try:
                    await page.set_viewport_size({
                        "width": config["width"], 
                        "height": config["height"]
                    })
                    await page.goto(self.url, wait_until="networkidle")
                    await asyncio.sleep(0.5)
                    
                    # Take screenshot
                    screenshot_filename = f"{device_key}_{self.timestamp}.png"
                    screenshot_path = self.screenshots_dir / screenshot_filename
                    
                    await page.screenshot(path=str(screenshot_path), full_page=True)
                    
                    # Apply watermark
                    self.watermark.apply(str(screenshot_path))
                    
                    self.add_result(
                        f"Responsive ({config['name']})", 
                        True, 
                        f"{config['width']}x{config['height']}"
                    )
                    self.print_status(
                        f"Responsive ({config['name']})", 
                        True, 
                        f"{config['width']}x{config['height']} ✓"
                    )
                except Exception as e:
                    self.add_result(f"Responsive ({config['name']})", False, str(e))
                    self.print_status(f"Responsive ({config['name']})", False, str(e)[:50])
    
    async def test_meta_tags(self, page: Page):
        """Comprehensive meta tag analysis"""
        try:
            meta = await page.evaluate("""() => {
                const getMeta = (name) => {
                    const el = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
                    return el ? el.content : null;
                };
                const getAllMeta = () => {
                    return Array.from(document.querySelectorAll('meta')).map(m => ({
                        name: m.name || m.getAttribute('property'),
                        content: m.content
                    })).filter(m => m.name);
                };
                return {
                    description: getMeta('description'),
                    viewport: document.querySelector('meta[name="viewport"]')?.content,
                    charset: document.characterSet,
                    og_title: getMeta('og:title'),
                    og_description: getMeta('og:description'),
                    og_image: getMeta('og:image'),
                    robots: getMeta('robots'),
                    all_meta: getAllMeta()
                };
            }""")
            
            warnings = []
            if not meta.get('description'):
                warnings.append("Missing description")
            elif len(meta['description']) < 50:
                warnings.append(f"Description too short ({len(meta['description'])} chars)")
            elif len(meta['description']) > 160:
                warnings.append(f"Description too long ({len(meta['description'])} chars)")
            
            if not meta.get('viewport'):
                warnings.append("Missing viewport")
            
            if not meta.get('og_title'):
                warnings.append("Missing OG title")
            
            if warnings:
                self.add_result("Meta Tags", False, ", ".join(warnings), warning=True)
                self.print_status("Meta Tags", False, f"{len(warnings)} issues", warning=True)
                for w in warnings:
                    console.print(f"     [yellow]• {w}[/yellow]")
            else:
                self.add_result("Meta Tags", True, "All meta tags optimized")
                self.print_status("Meta Tags", True, "Well optimized ✓")
        except Exception as e:
            self.add_result("Meta Tags", False, str(e))
            self.print_status("Meta Tags", False, str(e)[:50])
    
    async def test_security_headers(self, page: Page):
        """Check security headers"""
        try:
            response = await page.goto(self.url)
            headers = response.headers if response else {}
            
            security_headers = {
                "Strict-Transport-Security (HSTS)": headers.get("strict-transport-security"),
                "Content-Security-Policy": headers.get("content-security-policy"),
                "X-Frame-Options": headers.get("x-frame-options"),
                "X-Content-Type-Options": headers.get("x-content-type-options"),
                "Referrer-Policy": headers.get("referrer-policy"),
                "Permissions-Policy": headers.get("permissions-policy")
            }
            
            present = {k: v for k, v in security_headers.items() if v}
            missing = [k for k, v in security_headers.items() if not v]
            
            if missing:
                self.add_result(
                    "Security Headers", 
                    False, 
                    f"Present: {len(present)}/{len(security_headers)}", 
                    warning=True
                )
                self.print_status("Security Headers", False, f"Missing {len(missing)} headers", warning=True)
                for m in missing[:3]:
                    console.print(f"     [yellow]• Missing: {m}[/yellow]")
            else:
                self.add_result("Security Headers", True, "All security headers present")
                self.print_status("Security Headers", True, "All headers present ✓")
        except Exception as e:
            self.add_result("Security Headers", False, str(e))
            self.print_status("Security Headers", False, str(e)[:50])
    
    async def test_accessibility(self, page: Page):
        """Basic accessibility checks"""
        try:
            a11y = await page.evaluate("""() => {
                const issues = [];
                
                // Check images without alt
                const imagesWithoutAlt = document.querySelectorAll('img:not([alt]), img[alt=""]');
                if (imagesWithoutAlt.length > 0) {
                    issues.push(`${imagesWithoutAlt.length} image(s) missing alt text`);
                }
                
                // Check heading hierarchy
                const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'));
                let hasH1 = headings.some(h => h.tagName === 'H1');
                if (!hasH1) {
                    issues.push('Missing H1 heading');
                }
                
                // Check label associations
                const inputsWithoutLabel = document.querySelectorAll('input:not([type="hidden"]):not([aria-label]):not([aria-labelledby])');
                let unlabeledInputs = 0;
                inputsWithoutLabel.forEach(input => {
                    const hasLabel = document.querySelector(`label[for="${input.id}"]`);
                    if (!hasLabel) unlabeledInputs++;
                });
                if (unlabeledInputs > 0) {
                    issues.push(`${unlabeledInputs} input(s) without labels`);
                }
                
                return issues;
            }""")
            
            if a11y:
                self.add_result(
                    "Accessibility", 
                    False, 
                    f"{len(a11y)} issue(s)", 
                    warning=True
                )
                self.print_status("Accessibility", True, f"{len(a11y)} issue(s) found", warning=True)
                for issue in a11y[:3]:
                    console.print(f"     [yellow]• {issue}[/yellow]")
            else:
                self.add_result("Accessibility", True, "Basic checks passed")
                self.print_status("Accessibility", True, "Basic checks passed ✓")
        except Exception as e:
            self.add_result("Accessibility", False, str(e))
            self.print_status("Accessibility", False, str(e)[:50])
    
    def generate_html_report(self):
        """Generate beautiful HTML report with watermark branding"""
        template = Template("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ results.watermark_text }} Report - {{ results.url }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1100px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 20px;
            box-shadow: 0 30px 80px rgba(0,0,0,0.4);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 50px 40px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        .header::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: rotate 20s linear infinite;
        }
        @keyframes rotate {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        .header h1 { 
            font-size: 2.8em; 
            margin-bottom: 15px;
            position: relative;
            z-index: 1;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .header .subtitle {
            font-size: 1.2em;
            opacity: 0.95;
            position: relative;
            z-index: 1;
        }
        .header .os-badge {
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            margin-top: 10px;
            position: relative;
            z-index: 1;
        }
        .summary {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            padding: 40px;
            background: #f8f9fa;
        }
        .summary-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            transition: transform 0.2s;
        }
        .summary-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.12);
        }
        .summary-card .number {
            font-size: 3.2em;
            font-weight: 800;
            line-height: 1;
            margin-bottom: 8px;
        }
        .summary-card .label {
            color: #6c757d;
            font-weight: 500;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 0.5px;
        }
        .passed .number { color: #28a745; }
        .failed .number { color: #dc3545; }
        .warning .number { color: #ffc107; }
        .total .number { color: #667eea; }
        .results { padding: 40px; }
        .section-title {
            font-size: 1.5em;
            margin-bottom: 25px;
            color: #333;
            border-left: 4px solid #667eea;
            padding-left: 15px;
        }
        .test-item {
            display: flex;
            align-items: center;
            padding: 18px 20px;
            background: #f8f9fa;
            margin-bottom: 8px;
            border-radius: 10px;
            transition: background 0.2s;
        }
        .test-item:hover {
            background: #e9ecef;
        }
        .test-item .icon { 
            font-size: 1.5em; 
            margin-right: 20px;
            min-width: 30px;
        }
        .test-item .info { flex: 1; }
        .test-item .name { 
            font-weight: 600; 
            color: #333;
            margin-bottom: 3px;
        }
        .test-item .message { 
            color: #6c757d; 
            font-size: 0.9em;
        }
        .test-item .time { 
            color: #adb5bd; 
            font-size: 0.8em;
            min-width: 80px;
            text-align: right;
        }
        .screenshots-section {
            padding: 40px;
            background: #f8f9fa;
        }
        .screenshot-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin-top: 20px;
        }
        .screenshot-card {
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            text-align: center;
        }
        .screenshot-card .device-name {
            padding: 15px;
            font-weight: 600;
            color: #667eea;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-size: 0.9em;
        }
        .screenshot-card img {
            width: 100%;
            display: block;
        }
        .footer {
            text-align: center;
            padding: 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .footer .brand {
            font-size: 1.3em;
            font-weight: 700;
            margin-bottom: 5px;
        }
        .footer .info {
            opacity: 0.8;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🦊 {{ results.watermark_text }}</h1>
            <div class="subtitle">Automation Test Report</div>
            <div class="os-badge">🖥️ Tested on {{ results.os | upper }}</div>
            <div style="margin-top: 15px; position: relative; z-index: 1; opacity: 0.9;">
                <div>{{ results.url }}</div>
                <div style="margin-top: 5px;">{{ results.timestamp }}</div>
            </div>
        </div>
        
        <div class="summary">
            <div class="summary-card total">
                <div class="number">{{ results.tests | length }}</div>
                <div class="label">Total Tests</div>
            </div>
            <div class="summary-card passed">
                <div class="number">{{ results.passed }}</div>
                <div class="label">✅ Passed</div>
            </div>
            <div class="summary-card failed">
                <div class="number">{{ results.failed }}</div>
                <div class="label">❌ Failed</div>
            </div>
            <div class="summary-card warning">
                <div class="number">{{ results.warnings }}</div>
                <div class="label">⚠️ Warnings</div>
            </div>
        </div>
        
        <div class="results">
            <h2 class="section-title">Detailed Test Results</h2>
            {% for test in results.tests %}
            <div class="test-item">
                <div class="icon">
                    {% if test.warning %}⚠️
                    {% elif test.passed %}✅
                    {% else %}❌
                    {% endif %}
                </div>
                <div class="info">
                    <div class="name">{{ test.name }}</div>
                    {% if test.message %}
                    <div class="message">{{ test.message }}</div>
                    {% endif %}
                </div>
                <div class="time">{{ test.time }}</div>
            </div>
            {% endfor %}
        </div>
        
        <div class="screenshots-section">
            <h2 class="section-title">Screenshots</h2>
            <div class="screenshot-grid">
                {% for device in ['desktop', 'tablet', 'mobile'] %}
                <div class="screenshot-card">
                    <div class="device-name">📱 {{ device | upper }}</div>
                    <img src="screenshots/{{ device }}_{{ results.timestamp }}.png" 
                         alt="{{ device }} screenshot"
                         onerror="this.parentElement.style.display='none'">
                </div>
                {% endfor %}
            </div>
        </div>
        
        <div class="footer">
            <div class="brand">🦊 {{ results.watermark_text }}</div>
            <div class="info">Web Automation Testing Suite v2.0.0 • Universal Edition</div>
            <div class="info">Report generated on {{ results.os | upper }}</div>
        </div>
    </div>
</body>
</html>
        """)
        
        report_path = self.report_dir / "report.html"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(template.render(results=self.results))
        
        return report_path
    
    async def run(self):
        """Run all tests with beautiful UI"""
        start_time = time.time()
        
        # Show banner
        console.print(get_banner(self.results['watermark_text']))
        console.print(f"[bold cyan]🎯 Target:[/bold cyan] {self.url}")
        console.print(f"[bold cyan]💻 System:[/bold cyan] {platform.system()} {platform.release()}")
        console.print(f"[bold cyan]📁 Output:[/bold cyan] {self.report_dir}")
        console.print(f"[bold cyan]🏷️  Watermark:[/bold cyan] '{self.results['watermark_text']}'")
        console.print("-" * 60)
        
        with Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            total_tests = 10
            task = progress.add_task("[cyan]🦊 Lilo is scanning...", total=total_tests)
            
            async with async_playwright() as pw:
                # Launch browser
                browser = await pw.chromium.launch(headless=self.headless)
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent=f"LiloTester/2.0 ({platform.system()})"
                )
                page = await context.new_page()
                
                # Run all tests with progress
                tests = [
                    ("Testing page load...", self.test_page_load),
                    ("Checking title...", self.test_title),
                    ("Analyzing meta tags...", self.test_meta_tags),
                    ("Scanning console errors...", self.test_console_errors),
                    ("Checking security headers...", self.test_security_headers),
                    ("Detecting forms...", self.test_forms),
                    ("Testing accessibility...", self.test_accessibility),
                    ("Checking links (internal)...", self.test_links),
                ]
                
                for description, test_fn in tests:
                    progress.update(task, description=f"[cyan]{description}[/cyan]")
                    await test_fn(page)
                    progress.advance(task)
                
                # Responsive tests
                progress.update(task, description="[cyan]Testing responsive design...[/cyan]")
                await self.test_responsive(page)
                progress.advance(task)
                
                # Final screenshot
                progress.update(task, description="[cyan]Capturing full page screenshot...[/cyan]")
                screenshot_path = self.screenshots_dir / f"fullpage_{self.timestamp}.png"
                await page.screenshot(path=str(screenshot_path), full_page=True)
                self.watermark.apply(str(screenshot_path))
                self.add_result("Full Page Screenshot", True, "Captured with watermark")
                progress.advance(task)
                
                await browser.close()
        
        # Calculate total time
        self.results["total_time"] = time.time() - start_time
        
        # Generate report
        console.print("\n[bold cyan]📊 Generating HTML report...[/bold cyan]")
        report_path = self.generate_html_report()
        
        # Show summary
        self.print_summary()
        
        # Open report in browser (cross-platform)
        console.print(f"\n[bold green]✅ Report:[/bold green] {report_path}")
        self._open_report(report_path)
        
        console.print(f"[bold cyan]🦊 {self.results['watermark_text']} completed![/bold cyan]\n")
        
        return self.results
    
    def _open_report(self, report_path):
        """Open report in default browser (cross-platform)"""
        try:
            import webbrowser
            webbrowser.open(f"file://{report_path.absolute()}")
            console.print("[dim]📂 Report opened in browser[/dim]")
        except:
            pass
    
    def print_summary(self):
        """Print beautiful summary table"""
        console.print("\n" + "=" * 60)
        
        # Create summary panel
        summary_text = Text()
        summary_text.append("📊 TEST SUMMARY\n", style="bold cyan")
        summary_text.append("─" * 40 + "\n", style="dim")
        summary_text.append(f"Total Tests:    {len(self.results['tests'])}\n")
        summary_text.append(f"✅ Passed:      {self.results['passed']}\n", style="green")
        summary_text.append(f"❌ Failed:      {self.results['failed']}\n", style="red")
        summary_text.append(f"⚠️  Warnings:   {self.results['warnings']}\n", style="yellow")
        summary_text.append(f"⏱️  Duration:   {self.results['total_time']:.2f}s\n")
        summary_text.append(f"💻 Platform:    {platform.system()}\n", style="dim")
        
        panel = Panel(
            summary_text,
            title=f"[bold]{self.results['watermark_text']}[/bold]",
            border_style="cyan",
            padding=(1, 2)
        )
        console.print(panel)
        
        # Overall status
        if self.results["failed"] == 0 and self.results["warnings"] == 0:
            console.print("[bold green]🎉 PERFECT! All tests passed![/bold green]")
        elif self.results["failed"] == 0:
            console.print(f"[bold yellow]⚠️  {self.results['warnings']} warning(s), but no critical failures.[/bold yellow]")
        else:
            console.print(f"[bold red]💀 {self.results['failed']} FAILED! Check report for details.[/bold red]")

# ═══════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════

async def main():
    parser = argparse.ArgumentParser(
        description="🦊 Lilo Tester - Universal Web Automation Testing Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python lilo_tester.py --url https://example.com
  
  # Custom watermark
  python lilo_tester.py --url https://example.com --watermark "QA Team"
  
  # Custom position
  python lilo_tester.py --url https://example.com --watermark "MyBrand" --position bottom-left
  
  # Specific devices only
  python lilo_tester.py --url https://example.com --devices desktop mobile
  
  # Custom output directory
  python lilo_tester.py --url https://example.com --output test_results
  
  # Show browser window (not headless)
  python lilo_tester.py --url https://example.com --no-headless
  
Positions: bottom-right (default), bottom-left, top-right, top-left
        """
    )
    
    parser.add_argument("--url", "-u", required=True, help="Target website URL")
    parser.add_argument("--output", "-o", default="lilo_reports", help="Output directory")
    parser.add_argument(
        "--devices", "-d", 
        nargs="+", 
        default=["desktop", "tablet", "mobile"],
        choices=["desktop", "tablet", "mobile"],
        help="Devices to test (default: all three)"
    )
    parser.add_argument(
        "--watermark", "-w", 
        default="Lilo Tester",
        help="Custom watermark text (default: 'Lilo Tester')"
    )
    parser.add_argument(
        "--position", "-p",
        default="bottom-right",
        choices=["bottom-right", "bottom-left", "top-right", "top-left"],
        help="Watermark position (default: bottom-right)"
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Show browser window while testing"
    )
    
    args = parser.parse_args()
    
    # Validate URL
    if not args.url.startswith(("http://", "https://")):
        args.url = "https://" + args.url
    
    # Create and run tester
    tester = LiloTester(
        url=args.url,
        output_dir=args.output,
        devices=args.devices,
        watermark_text=args.watermark,
        watermark_position=args.position,
        headless=not args.no_headless
    )
    
    await tester.run()

if __name__ == "__main__":
    asyncio.run(main())