# 🦊 Lilo Tester v4.5.1

<p align="center">

**Advanced Web Automation & Security Testing Suite**

*Authenticated Exploration • Micro-Interaction Testing • Performance Analytics • Security Audit*

</p>

<p align="center">

![Python](https://img.shields.io/badge/python-3.8+-blue)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![Browser](https://img.shields.io/badge/browser-Playwright%20Chromium-purple)
![License](https://img.shields.io/badge/license-MIT-green)
![Version](https://img.shields.io/badge/version-4.5.1-orange)

</p>

<p align="center">

🔐 Authenticate → 🗺️ Explore → 🧪 Test → 🛡️ Audit → ⚡ Analyze → 📄 Report

</p>

---

# 📑 Table of Contents

* [Overview](#-overview)
* [Features](#-features)
* [Quick Start](#-quick-start)
* [Installation](#-installation)
* [Usage Guide](#-usage-guide)
* [Authentication](#-authentication)
* [Credential Manager](#-credential-manager)
* [Performance Testing](#-performance-testing)
* [Security Audit](#-security-audit)
* [Micro-Interaction Testing](#-micro-interaction-testing)
* [CLI Reference](#-cli-reference)
* [Output Structure](#-output-structure)
* [Report Details](#-report-details)
* [Troubleshooting](#-troubleshooting)
* [FAQ](#-faq)
* [License](#-license)

---

# 🚀 Overview

Lilo Tester is a comprehensive CLI toolkit designed for browser-rendered applications.

It combines:

* Authenticated dashboard exploration
* Micro-interaction testing
* Advanced performance analytics
* Security auditing
* Screenshot capture
* Rich HTML reporting

into a single command.

Supports virtually any modern stack:

```text
Laravel • Filament • Nova • Livewire • Inertia

React • Next.js • Remix

Vue • Nuxt • Quasar

WordPress • Django • Rails

SPA • Static HTML
```

> No configuration.
>
> One command.
>
> Full report.

---

# ⚡ Features

## 🔐 Authentication & Exploration

| Feature             | Description                                       |
| ------------------- | ------------------------------------------------- |
| Flexible Login      | Username + Password, Password-only, Direct Access |
| Auto Detect Login   | Finds login pages automatically                   |
| Custom Login URL    | Specify exact login path                          |
| Dashboard Explorer  | Discovers menus and internal pages                |
| Session Persistence | Reuse browser sessions                            |
| Safe Mode           | Blocks POST / PUT / DELETE                        |

---

## 🧪 Micro-Interaction Testing

| Test          | Validation               |
| ------------- | ------------------------ |
| 🔍 Search     | Query execution          |
| 📊 Filters    | Option switching         |
| 📄 Pagination | Next/page navigation     |
| ↕️ Sort       | Sortable columns         |
| 📑 Tabs       | Tab switching            |
| 🪟 Modal      | Open / Close             |
| 📋 Dropdown   | Toggle menus             |
| 🎵 Accordion  | Expand / Collapse        |
| 📝 Forms      | Validation               |
| 📅 Datepicker | Input testing            |
| ☑️ Checkbox   | State changes            |
| 🔽 Select     | Option selection         |
| ✏️ Editor     | Rich text interaction    |
| 📎 Upload     | Upload element detection |
| 📊 Tables     | Rows & columns           |

---

## ⚡ Performance Analytics

| Feature              | Description            |
| -------------------- | ---------------------- |
| Performance Score    | 0–100 grading          |
| Core Web Vitals      | TTFB, FCP, LCP, CLS    |
| Resource Analysis    | JS, CSS, Fonts, Images |
| Slowest Assets       | Top 15                 |
| Largest Assets       | Top 15                 |
| Third Party Analysis | External domains       |
| DOM Complexity       | Node count & depth     |
| Recommendations      | Optimization hints     |

---

## 🛡 Security Audit

| Test              | Coverage             |
| ----------------- | -------------------- |
| Headers           | 8 security headers   |
| XSS               | Reflected & DOM      |
| SQLi              | Error based          |
| CSRF              | Missing token checks |
| Sensitive Files   | 30+ paths            |
| Cookies           | Secure flags         |
| CORS              | Reflection issues    |
| Clickjacking      | Frame protection     |
| SSL               | HTTPS validation     |
| Forms             | Secure attributes    |
| Disclosure        | Secrets detection    |
| Directory Listing | Common directories   |

---

## 📸 Reporting

| Feature           | Description        |
| ----------------- | ------------------ |
| Screenshots       | Full page captures |
| Security Evidence | Critical findings  |
| Error Screenshots | Debugging          |
| HTML Report       | Interactive        |
| JSON Report       | Machine readable   |
| Security Score    | 0–100              |

---

# ⚡ Quick Start

Clone repository

```bash
git clone https://github.com/yourusername/lilo-tester.git

cd lilo-tester
```

Install dependencies

```bash
pip install -r requirements.txt

python -m playwright install chromium
```

Run scanner

```bash
python lilo_tester.py -u https://example.com
```

Install globally

```bash
pip install -e .

liloit -u https://example.com
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
sudo apt update

sudo apt install python3 python3-pip -y

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

| Mode        | Auth | Exploration | Security | Performance | Best For         |
| ----------- | ---- | ----------- | -------- | ----------- | ---------------- |
| dashboard   | ✅    | 50 Pages    | ✅        | ✅           | ERP / CRM        |
| public      | ❌    | 10 Pages    | ✅        | ✅           | Websites         |
| performance | ❌    | Limited     | ❌        | Full        | Optimization     |
| security    | ❌    | ❌           | Full     | ❌           | Security Testing |
| quick       | ❌    | ❌           | ❌        | Basic       | Health Checks    |

Examples

```bash
liloit -u https://erp.company.com

liloit -u https://blog.example.com --no-login

liloit -u https://shop.example.com --mode performance

liloit -u https://example.com --mode security

liloit -u https://example.com --mode quick
```

---

# 🔐 Authentication

Auto discovery works by:

* password field detection
* login link discovery
* common path enumeration

Examples

```bash
liloit -u https://app.company.com
```

Custom login

```bash
liloit -u https://app.company.com \
--login-url /admin/login
```

Localhost

```bash
liloit -u http://127.0.0.1:8000 \
--login-url /login
```

Supported login types

| Type                | Description             |
| ------------------- | ----------------------- |
| Username + Password | Standard authentication |
| Password Only       | Admin panels            |
| Direct Access       | Already authenticated   |

---

# 💾 Credential Manager

Stored at

```text
~/.lilo_tester/credentials.json
```

Supports:

* multiple accounts
* labels
* interactive selection
* auto detection

---

# ⚡ Performance Testing

```bash
liloit -u https://example.com --mode performance
```

Includes

* Performance Score
* Web Vitals
* Resource Analysis
* Largest Assets
* Slowest Assets
* Third Party Impact
* Recommendations

---

# 🛡 Security Audit

Run security scan

```bash
liloit -u https://example.com --mode security
```

Findings include

* severity
* evidence
* affected URL
* screenshot
* remediation advice

---

# 🧪 Micro-Interaction Testing

Executed automatically in:

* dashboard mode
* public mode

Includes over **15 interaction tests**.

```bash
liloit -u https://erp.company.com
```

---

# ⚙ CLI Reference

| Flag          | Description           |
| ------------- | --------------------- |
| -u            | URL                   |
| -m            | Mode                  |
| -l            | Login URL             |
| -o            | Output Folder         |
| --headless    | Headless browser      |
| --max-pages   | Exploration limit     |
| --no-login    | Disable auth          |
| --no-security | Disable security      |
| --no-open     | Prevent report launch |

Examples

```bash
liloit -u https://erp.company.com

liloit -u https://erp.company.com --login-url /admin/login

liloit -u https://example.com --mode security

liloit -u https://example.com --mode performance

liloit -u https://example.com --mode quick
```

---

# 📂 Output Structure

```text
lilo_reports/

├── report_YYYY-MM-DD/

│ ├── report.html

│ ├── report.json

│ ├── screenshots/

│ │ ├── pages/

│ │ ├── security/

│ │ └── errors/

│ └── error_screenshots/

├── sessions/

│ └── auth_session.json

└── screenshots/

~/.lilo_tester/

└── credentials.json
```

---

# 📊 Report Details

### HTML Report

* Performance
* Security
* Screenshots
* Exploration
* Micro Tests
* Errors

### JSON Report

Contains

* test results
* metrics
* findings
* APIs
* stack traces
* navigation graph

---

# 🔧 Troubleshooting

### Command not found

```bash
pip install -e .
```

### Playwright missing

```bash
python -m playwright install chromium
```

Linux

```bash
python -m playwright install-deps chromium
```

### Login issues

```bash
liloit -u https://app.com \
--login-url /login
```

### Performance issues

```bash
liloit -u https://example.com --max-pages 10
```

### Reset credentials

```bash
rm ~/.lilo_tester/credentials.json
```

---

# ❓ FAQ

### Does it modify data?

No.

Safe Mode blocks:

* POST
* PUT
* PATCH
* DELETE

Only GET requests are allowed.

---

### CI/CD Support?

Yes.

```bash
liloit -u https://staging.example.com \
--headless \
--no-open \
--mode quick
```

---

### Supported Applications?

Anything browser rendered.

* Laravel
* Filament
* React
* Next.js
* Vue
* Nuxt
* WordPress
* Django
* ERP
* CRM
* Admin Panels

---

### Credential Safety?

Credentials are stored locally.

For production environments consider:

* Vault
* Secrets Manager
* Environment Variables

---

# 🪪 License

MIT License

Copyright (c) 2024–2026 Lilo Tester

---

<p align="center">

**🦊 Lilo Tester v4.5.1**

*Authenticate • Explore • Test • Audit • Analyze • Report*

<sub>Made with ❤️ for developers who want things to just work.</sub>

</p>
