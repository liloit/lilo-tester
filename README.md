# 🦊 Lilo Tester v5.0.0

<p align="center">

**Deep DAST & Advanced Web Security Scanner**

*Authenticate • Crawl • Fuzz • Exploit • Analyze • Report*

</p>

<p align="center">

![Python](https://img.shields.io/badge/python-3.10+-blue)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![Browser](https://img.shields.io/badge/browser-Playwright%20Chromium-purple)
![License](https://img.shields.io/badge/license-MIT-green)
![Version](https://img.shields.io/badge/version-5.0.0-orange)

</p>

<p align="center">

🕵️ Recon → 🔬 Analysis → 💥 Exploitation → 📊 Reporting

</p>

---

# 📑 Table of Contents

* [Overview](#-overview)
* [What's New in v5.0.0](#-whats-new-in-v500)
* [Features](#-features)
* [Quick Start](#-quick-start)
* [Installation](#-installation)
* [Usage Guide](#-usage-guide)
* [CLI Reference](#-cli-reference)
* [Security Modules](#-security-modules)
* [DevSecOps / CI-CD](#-devsecops--cicd)
* [Output Structure](#-output-structure)
* [Report Formats](#-report-formats)
* [Troubleshooting](#-troubleshooting)
* [FAQ](#-faq)
* [License](#-license)

---

# 🚀 Overview

Lilo Tester is a full-stack Dynamic Application Security Testing (DAST) tool built for browser-rendered web applications. It runs entirely locally — no API keys, no cloud, no data sent externally.

It combines:

* Authenticated deep crawling with Shadow DOM traversal
* **Hybrid Engine** — Playwright for recon, `aiohttp` for high-speed fuzzing
* **Auth-Synchronized Fuzzing** — Playwright cookies auto-synced into `aiohttp` session
* Context-aware payload injection (XSS & SQLi) against all crawled pages
* External wordlist streaming (SecLists compatible, no RAM blowout)
* Out-of-Band (OOB) blind vulnerability detection via Interactsh
* Multi-Role IDOR/BOLA engine with dual session replay
* DOM-Based Taint Analysis via persistent JS injection
* Business Logic & Mass Assignment fuzzer (opt-in)
* Advanced Performance Analytics (Core Web Vitals, resource waterfall)
* Multi-format reporting: HTML, Markdown, PDF, **SARIF**
* **DevSecOps-ready** — exits with code `1` on Critical/High findings for CI/CD pipelines

into a single command.

Supports virtually any modern stack:

```text
Laravel • Filament • Nova • Livewire • Inertia

React • Next.js • Remix • Vue • Nuxt • Quasar

WordPress • Django • Rails • FastAPI

SPA • Static HTML • ERP • CRM
```

> No configuration files.
>
> One command.
>
> Full report.

---

# ✨ What's New in v5.0.0

| Feature | Description |
| --- | --- |
| ⚡ Hybrid Engine | Playwright handles recon; `aiohttp` handles fuzzing — 100× faster |
| 🔐 Auth Sync | Playwright cookies auto-injected into `aiohttp.ClientSession` — fuzzing runs fully authenticated |
| 📄 External Wordlists | `--xss-wordlist` & `--sqli-wordlist` — streams payloads line-by-line, no RAM blowout |
| 🌐 Proxy Support | `--proxy http://127.0.0.1:8080` — routes both Playwright & aiohttp through Burp/Caido/ZAP |
| 🪖 Custom Headers | `--header "Authorization: Bearer xxx"` — bypass WAF or inject manual tokens |
| 🚦 Rate Limiting | `--rate-limit N` — caps fuzzing requests/sec via asyncio.Semaphore |
| 📋 SARIF Export | `--sarif` — generates `report.sarif` compatible with GitHub Actions & GitLab CI |
| 🚨 CI/CD Exit Code | Exits with code `1` if Critical or High vulnerabilities are found |
| 🧬 DOM Taint Analysis | Tracks JS variable flows from sources (`location.search`) to sinks (`eval`, `innerHTML`) |
| 📡 OOB Testing | Interactsh integration with local fallback server for blind SSRF, RCE, XSS detection |
| 🔀 IDOR/BOLA Engine | Dual session replay with Cookie & Bearer Token injection |
| ⚗️ Mass Assignment | Business logic fuzzer (behind `--enable-mass-assign` opt-in flag) |
| 🕵️ Time-Based SQLi | Baseline-aware SLEEP() detection to eliminate network-lag false positives |
| 🗂️ Endpoint Fuzzing | Hidden path discovery (`/backup`, `/.git`, `/api/v1/users`, etc.) |
| 🪪 JWT Analysis | Detects insecure JWTs, weak algorithms, and sensitive browser storage items |
| 📄 PDF Export | Auto PDF generation via Playwright Chromium (headless) |
| 🛡️ WAF Awareness | Passive + active WAF/CDN detection with confirmation prompt |
| 🔬 Tech Fingerprinting | Detects framework, CMS, CDN, and WAF from headers and DOM |
| 🌐 Subdomain Enum | Passive subdomain enumeration via crt.sh and HackerTarget |

---

# ⚡ Features

## 🕵️ Phase 1 — Intelligence Gathering

| Feature | Description |
| --- | --- |
| Tech Stack Fingerprinting | Detects framework, CMS, CDN, server from headers & DOM |
| WAF/CDN Detection | Passive detection (headers) + active probe |
| Subdomain Enumeration | crt.sh + HackerTarget; optional Level 2 (`--deep-enum`) |
| Hidden Parameter Discovery | Differential response analysis across 70+ parameters |
| Context-Aware Payload Mapping | Selects optimal XSS/SQLi payload per injection context |

---

## 🔬 Phase 2 — Vulnerability Analysis

| Test | Coverage |
| --- | --- |
| 🔒 Security Headers | 8 critical headers (CSP, HSTS, X-Frame-Options, etc.) |
| 🎯 XSS | Reflected (aiohttp reflection check → Playwright execution confirm) |
| 💉 SQLi | Error-based, Time-based (baseline-aware), OOB |
| 🔑 CSRF | Missing token detection |
| 📁 Sensitive Files | 30+ paths (`/.git`, `/phpinfo.php`, `/backup`, etc.) |
| 🍪 Cookies | Secure, HttpOnly, SameSite flags |
| 🌐 CORS | Reflection & wildcard issues |
| 🖥️ Clickjacking | Frame protection headers |
| 🔐 SSL/TLS | HTTPS enforcement validation |
| 📝 Forms | Autocomplete, secure attributes |
| 🔓 Info Disclosure | API keys, secrets, stack traces |
| 📂 Directory Listing | Open directory detection |
| 🪪 JWT/Storage | Insecure JWT algorithms, sensitive data in localStorage |
| 🧬 DOM Taint | Source-to-sink taint flow tracking in JavaScript |
| 🏗️ Mass Assignment | Parameter injection on POST/PUT endpoints (opt-in) |

> **Note:** XSS and SQLi fuzzing now run via `aiohttp` (high-speed, low-memory) across **all crawled pages**, not just the homepage.

---

## 💥 Phase 3 — Exploitation

| Feature | Description |
| --- | --- |
| ⏱️ Time-Based Verification | Baseline response time measurement; confirms Blind SQLi/CMDi |
| 📡 OOB Callback Testing | Interactsh URL injection for Blind XSS, SSRF, OOB SQLi |
| 🔀 IDOR/BOLA Engine | Dual session, intercepts and swaps auth tokens (Cookie & Bearer) |
| 🗂️ Endpoint Fuzzing | GET-based wordlist against hidden paths; records 200/403 hits |

---

## 📊 Phase 4 — Reporting

| Feature | Description |
| --- | --- |
| 📋 Auto PoC Generation | Copy-paste `curl` commands for every confirmed finding |
| 📈 CVSS Scoring | Static mapping per vulnerability category (0.0–10.0) |
| 💡 Context-Driven Remediation | Fix advice tailored to detected stack (Laravel, React, PHP, etc.) |
| 🌐 HTML Report | Interactive, collapsible, tabbed report with screenshots |
| 📄 Markdown Report | Clean `.md` file for GitHub issues or Notion |
| 📑 PDF Report | Auto-generated via Playwright Chromium |
| 🗃️ JSON Report | Machine-readable full result set |
| 📋 SARIF Report | Industry-standard format for GitHub Advanced Security / GitLab SAST |

---

## ⚡ Performance Analytics

| Feature | Description |
| --- | --- |
| Performance Score | 0–100 grading (A–F) |
| Core Web Vitals | TTFB, FCP, LCP, CLS |
| Resource Analysis | JS, CSS, Fonts, Images breakdown |
| Slowest Assets | Top 15 slowest resources |
| Largest Assets | Top 15 heaviest resources |
| Third-Party Impact | External domain request analysis |
| DOM Complexity | Node count & nesting depth |
| Recommendations | Actionable optimization hints |

---

## 🧪 Micro-Interaction Testing

| Test | Validation |
| --- | --- |
| 🔍 Search Input | Query execution & response |
| 📊 Filter Dropdown | Option switching |
| 📄 Pagination | Next/page navigation |
| ↕️ Sort Buttons | Sortable column clicks |
| 📑 Tab Navigation | Tab switching |
| 🪟 Modal Buttons | Open / Close cycle |
| 📋 Dropdown Menus | Toggle behavior |
| 🎵 Accordion | Expand / Collapse |
| 📝 Form Validation | Empty submission handling |
| 📅 Datepicker | Input testing |
| ☑️ Checkbox & Radio | State changes |
| 🔽 Select Dropdown | Option selection |
| ✏️ Rich Text Editor | Editor interaction |
| 📎 File Upload | Upload element detection |
| 📊 Data Tables | Row & column inspection |

---

# ⚡ Quick Start

**Clone and install:**

```bash
git clone https://github.com/yourusername/lilo-tester.git
cd lilo-tester
pip install -r requirements.txt
python -m playwright install chromium
pip install -e .
```

**Run:**

```bash
# Full authenticated scan
liloit -u https://example.com

# Fast public scan (no login)
liloit -u https://example.com -m quick

# Security-only scan
liloit -u https://example.com -m security

# With IDOR testing
liloit -u https://example.com --enable-idor --idor-user victim:password123

# With custom XSS wordlist + proxy (Burp Suite)
liloit -u https://example.com --xss-wordlist payloads.txt --proxy http://127.0.0.1:8080

# Generate SARIF for CI/CD
liloit -u https://staging.example.com --headless --no-open --sarif
```

---

# 📦 Installation

<details>

<summary>🪟 Windows</summary>

```powershell
git clone https://github.com/yourusername/lilo-tester.git
cd lilo-tester
pip install -r requirements.txt
python -m playwright install chromium
pip install -e .
liloit -u https://example.com
```

</details>

<details>

<summary>🍎 macOS</summary>

```bash
brew install python@3.12
git clone https://github.com/yourusername/lilo-tester.git
cd lilo-tester
pip3 install -r requirements.txt
python3 -m playwright install chromium
pip3 install -e .
liloit -u https://example.com
```

</details>

<details>

<summary>🐧 Linux</summary>

```bash
sudo apt update && sudo apt install python3 python3-pip -y
git clone https://github.com/yourusername/lilo-tester.git
cd lilo-tester
pip install -r requirements.txt
python3 -m playwright install chromium
python3 -m playwright install-deps chromium
pip install -e .
liloit -u https://example.com
```

</details>

---

# 🧠 Usage Guide

## Scan Modes

| Mode | Auth | Crawl | Security | Performance | Best For |
| --- | --- | --- | --- | --- | --- |
| `dashboard` | ✅ | 50 pages | ✅ | ✅ | ERP, CRM, Admin panels |
| `public` | ❌ | 10 pages | ✅ | ✅ | Public-facing websites |
| `performance` | ❌ | Limited | ❌ | Full | Performance optimization |
| `security` | ❌ | ❌ | Full | ❌ | Security-only testing |
| `quick` | ❌ | ❌ | ❌ | Basic | Health checks, CI/CD |

**Examples:**

```bash
liloit -u https://erp.company.com                         # Full dashboard scan
liloit -u https://blog.example.com --mode public          # Public site scan
liloit -u https://shop.example.com --mode performance     # Performance only
liloit -u https://example.com --mode security             # Security only
liloit -u https://example.com --mode quick --headless     # CI/CD health check
```

---

# ⚙️ CLI Reference

| Flag | Short | Default | Description |
| --- | --- | --- | --- |
| `--url` | `-u` | *(required)* | Target URL to test |
| `--mode` | `-m` | `dashboard` | Scan mode: `dashboard`, `public`, `performance`, `security`, `quick` |
| `--login-url` | `-l` | auto | Custom login URL |
| `--output` | `-o` | `lilo_reports` | Report output directory |
| `--max-pages` | | `50` | Maximum pages to crawl |
| `--headless` | | off | Run browser without GUI |
| `--no-login` | | off | Skip authentication |
| `--no-security` | | off | Skip vulnerability analysis |
| `--no-open` | | off | Don't auto-open report |
| `--enable-idor` | | off | Enable IDOR/BOLA engine |
| `--idor-user` | | — | Victim credentials: `user:password` |
| `--oob-server` | | public | Custom Interactsh server URL |
| `--deep-enum` | | off | Enable Level 2 subdomain enumeration |
| `--ignore-waf` | | off | Force scanning even if WAF detected |
| `--enable-mass-assign` | | off | ⚠️ Enable destructive Mass Assignment tester |
| `--xss-wordlist` | | built-in | Path to custom XSS payload file (streamed, RAM-safe) |
| `--sqli-wordlist` | | built-in | Path to custom SQLi payload file (streamed, RAM-safe) |
| `--proxy` | | — | Upstream proxy (e.g., `http://127.0.0.1:8080`) |
| `--header` | | — | Custom request header (repeatable, e.g., `Authorization: Bearer xxx`) |
| `--rate-limit` | | `0` (off) | Max fuzzing requests per second |
| `--sarif` | | off | Export SARIF report for GitHub/GitLab integration |

**Full examples:**

```bash
# Standard full scan with custom login URL
liloit -u https://app.company.com --login-url /admin/login

# IDOR testing with victim credentials
liloit -u https://api.example.com --enable-idor --idor-user victim:pass123

# WAF-protected target with forced scan
liloit -u https://waf-protected.com --ignore-waf --mode security

# Headless CI/CD check with SARIF output
liloit -u https://staging.example.com --headless --no-open --sarif

# Deep subdomain + security scan
liloit -u https://example.com --deep-enum --mode security

# Business logic testing (CAUTION: destructive)
liloit -u https://example.com --enable-mass-assign

# Custom SecLists wordlist + proxy (Burp Suite)
liloit -u https://example.com \
  --xss-wordlist ~/SecLists/Fuzzing/XSS/xss-payload-list.txt \
  --sqli-wordlist ~/SecLists/Fuzzing/SQLi/sqli-payloads.txt \
  --proxy http://127.0.0.1:8080 \
  --rate-limit 20

# Custom Authorization header
liloit -u https://api.example.com \
  --header "Authorization: Bearer eyJhbGci..." \
  --mode security
```

---

# 🛡️ Security Modules

## IDOR/BOLA Engine

Requires two accounts: an attacker (you) and a victim.

```bash
liloit -u https://app.example.com \
  --enable-idor \
  --idor-user victim_user:victim_pass
```

The engine:
1. Logs in as victim → captures session cookies & Bearer tokens
2. Logs in as attacker → replays victim's requests
3. Detects cross-session data access (IDOR)
4. Supports Cookie-based and Authorization header-based APIs

---

## Hybrid Fuzzing Engine

The scanner uses a **two-phase approach** for XSS and SQLi:

1. **Phase 1 (Recon)** — Playwright crawls the app, logs in, collects all URLs and CSRF tokens.
2. **Phase 2 (Fuzzing)** — `aiohttp` (with cookies synced from Playwright) sends thousands of requests per second against every discovered URL.

This means:
- Fuzzing runs **fully authenticated** (no 401/403 false negatives)
- Memory stays flat — wordlists are **streamed line-by-line**, never loaded entirely into RAM
- A 2 GB wordlist works fine

```bash
# Stream a 2 GB wordlist safely
liloit -u https://example.com \
  --xss-wordlist /path/to/huge-xss-list.txt \
  --rate-limit 50
```

---

## OOB (Out-of-Band) Testing

Detects blind vulnerabilities that don't produce visible errors.

```bash
# Use public Interactsh (default)
liloit -u https://example.com

# Use self-hosted Interactsh server
liloit -u https://example.com --oob-server https://your-interactsh.server
```

Detects:
* Blind XSS (in contact forms, comments)
* SSRF (Server-Side Request Forgery)
* OOB SQLi
* Blind Command Injection

Falls back to a local `aiohttp` server if Interactsh is unavailable.

---

## DOM Taint Analysis

Tracks JavaScript variable flows from user-controlled sources to dangerous sinks:

| Sources | Sinks |
| --- | --- |
| `window.location.search` | `eval()` |
| `window.location.hash` | `innerHTML` |
| `document.URL` | `document.write()` |
| `document.referrer` | `setTimeout()` |

Injected persistently via `page.add_init_script()` on every page load.

---

## Time-Based SQLi

Uses a baseline response time measurement to eliminate false positives caused by network lag:

1. Sends baseline request → records average response time
2. Injects `SLEEP(6)` / `WAITFOR DELAY` payload
3. Confirms only if response time ≥ (baseline + 4.5s)

---

## Mass Assignment Tester

> ⚠️ **Destructive flag. Requires explicit opt-in.**

```bash
liloit -u https://example.com --enable-mass-assign
```

Tests POST/PUT endpoints for unauthorized field injection (`role`, `is_admin`, `balance`, etc.). May create or modify records — use only on test environments.

---

## Proxy Support

Route all traffic through Burp Suite, Caido, or OWASP ZAP:

```bash
liloit -u https://example.com --proxy http://127.0.0.1:8080
```

Both Playwright (browser) and `aiohttp` (fuzzer) are routed through the proxy simultaneously.

---

# 🚀 DevSecOps / CI-CD

Lilo Tester is designed to integrate into automated pipelines.

## Exit Codes

| Code | Meaning |
| --- | --- |
| `0` | Scan complete, no Critical/High findings |
| `1` | Critical or High vulnerabilities detected |

## GitHub Actions Example

```yaml
- name: Run Lilo Tester
  run: |
    pip install -e .
    python -m playwright install chromium
    liloit -u ${{ secrets.STAGING_URL }} \
      --headless \
      --no-open \
      --sarif \
      --mode security

- name: Upload SARIF
  uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: lilo_reports/report_*/report.sarif
```

## GitLab CI Example

```yaml
security-scan:
  script:
    - pip install -e .
    - python -m playwright install chromium
    - liloit -u $STAGING_URL --headless --no-open --sarif --mode security
  artifacts:
    reports:
      sast: lilo_reports/report_*/report.sarif
```

---

# 🔐 Authentication

Auto-discovery works by:

* Password field detection
* Login link discovery
* Common path enumeration (`/login`, `/admin`, `/wp-admin`, etc.)

```bash
# Auto-detect login
liloit -u https://app.company.com

# Custom login URL
liloit -u https://app.company.com --login-url /admin/login

# Skip login (public pages only)
liloit -u https://app.company.com --no-login
```

| Login Type | Description |
| --- | --- |
| Username + Password | Standard form authentication |
| Password Only | Admin panels with single field |
| Direct Access | Already authenticated sessions |

---

# 💾 Credential Manager

Credentials stored locally at:

```text
~/.lilo_tester/credentials.json
```

Features:
* Multiple saved accounts with labels
* Interactive account selection on prompt
* Auto-detection of previously stored credentials

---

# 📂 Output Structure

```text
lilo_reports/
└── report_YYYY-MM-DD_HH-MM-SS/
    ├── report.html        ← Interactive HTML report
    ├── report.md          ← Markdown report
    ├── report.pdf         ← PDF report (auto-generated)
    ├── report.json        ← Full machine-readable results
    ├── report.sarif       ← SARIF (with --sarif flag)
    └── screenshots/
        ├── pages/         ← Page captures (up to 20 pages)
        ├── security/      ← Screenshots of security findings
        └── errors/        ← Error screenshots

~/.lilo_tester/
└── credentials.json       ← Saved login credentials
```

---

# 📊 Report Formats

### HTML Report (Tabbed, Interactive)

| Tab | Content |
| --- | --- |
| Performance | Score, Web Vitals, resource breakdown |
| Security | Findings by severity with CVSS scores & PoC commands |
| IDOR | BOLA/IDOR confirmed findings |
| Deep API | Hidden API endpoints from JS bundles |
| Screenshots | Full-page page captures |
| Exploration | Discovered pages, components, APIs |
| Micro Tests | Interaction test results |
| Errors | Console errors and exceptions |

### Markdown Report

Clean `.md` suitable for GitHub Issues, Notion, or Confluence.

### PDF Report

Auto-generated from the HTML report via Playwright Chromium.

### JSON Report

Complete machine-readable output containing:
* All findings with evidence
* Performance metrics
* Discovered endpoints and pages
* Stack traces and error logs

### SARIF Report

Industry-standard Static Analysis Results Interchange Format. Compatible with:
* GitHub Advanced Security (Code Scanning)
* GitLab SAST
* VS Code SARIF Viewer extension

---

# 🔧 Troubleshooting

### `liloit` command not found

```bash
pip install -e .
```

### Playwright not installed

```bash
python -m playwright install chromium
```

Linux only:

```bash
python -m playwright install-deps chromium
```

### Login fails

```bash
# Specify exact login URL
liloit -u https://app.com --login-url /login

# Skip login for public pages
liloit -u https://app.com --no-login
```

### Scan blocked by WAF

```bash
# Force scan (risk of IP ban)
liloit -u https://app.com --ignore-waf
```

### Memory or timeout issues

```bash
# Reduce crawl scope
liloit -u https://example.com --max-pages 10 --mode quick
```

### Slow fuzzing / rate limiting

```bash
# Limit to 20 requests per second
liloit -u https://example.com --rate-limit 20
```

### Reset saved credentials

```bash
rm ~/.lilo_tester/credentials.json
```

---

# ❓ FAQ

### Does it modify production data?

**No** — by default, Safe Mode is always active:

* Blocks POST, PUT, PATCH, DELETE requests
* Only GET requests pass through during crawling

The `--enable-mass-assign` flag disables this for business logic tests. **Use only on test/staging environments.**

---

### Does it send data externally?

**No** — Lilo Tester runs fully locally. The only external calls are:

* To the target URL being tested
* Subdomain enumeration via crt.sh / HackerTarget (passive, read-only)
* Interactsh OOB server (public by default; self-hosted option available)

---

### CI/CD Support?

Yes — Lilo Tester returns **exit code 1** if Critical or High vulnerabilities are found:

```bash
liloit -u https://staging.example.com \
  --headless \
  --no-open \
  --sarif \
  --mode security
# exits 1 if critical/high found → pipeline fails automatically
```

---

### Supported Applications?

Anything browser-rendered:

* Laravel, Filament, Nova, Livewire, Inertia
* React, Next.js, Remix, Vue, Nuxt, Quasar
* WordPress, Django, Rails, FastAPI
* ERP, CRM, Admin Panels

---

### Can I use my own payload lists?

Yes — both XSS and SQLi support external wordlists that are **streamed line-by-line** (RAM-safe, SecLists compatible):

```bash
liloit -u https://example.com \
  --xss-wordlist ~/SecLists/Fuzzing/XSS/xss-payload-list.txt \
  --sqli-wordlist ~/SecLists/Fuzzing/SQLi/sqli-payloads.txt
```

---

### Where are credentials stored?

Locally at `~/.lilo_tester/credentials.json`. Never transmitted. For production environments use:

* Environment variables
* Vault / Secrets Manager

---

# 🪪 License

MIT License

Copyright (c) 2024–2026 Lilo Tester

---

<p align="center">

**🦊 lilo · TESTER v5.0.0**

*Recon • Analyze • Exploit • Report*

<sub>Made with ❤️ for security researchers and developers who want things to just work.</sub>

</p>
