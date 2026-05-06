# 🦊 Lilo Tester

<p align="center">
  <strong>Web Automation Testing Suite</strong><br>
  <em>Fast. Minimal. Straight to the point.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-blue" />
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey" />
  <img src="https://img.shields.io/badge/browser-Playwright%20Chromium-purple" />
  <img src="https://img.shields.io/badge/license-MIT-green" />
</p>

---

<p align="center">
  <img src="docs/lilotester.gif" alt="Lilo Tester Demo" width="900"/>
</p>

<p align="center">
  <em>Scan → Analyze → Report. Fully automated.</em>
</p>

---

## 🚀 Overview

**Lilo Tester** is a lightweight CLI tool that scans any browser-rendered website and generates a complete diagnostic report.

It works with websites built using Laravel, React, Next.js, Vue, WordPress, Django, plain HTML, or any other stack — as long as the website can be opened in a browser.

No complex setup.  
No config files.  
No unnecessary noise.  

Just run it.

---

## ⚡ What You Get

- ⚡ **Page load performance**
- 🔍 **SEO & meta validation**
- 🔗 **Broken internal link detection**
- 🐞 **Console error tracking**
- 🌐 **Network error detection**
- 🛡 **Security headers audit**
- ♿ **Basic accessibility checks**
- 🧪 **Safe form testing**
- 📱 **Responsive testing**
- 📸 **Multi-device screenshots**
- 📄 **HTML + JSON report**

---

## 🎯 Scan Modes

Lilo Tester supports two scan modes:

| Mode | Description |
| ---- | ----------- |
| `quick` | Fast scan for the main page |
| `full` | Deeper scan across internal pages |

If you run Lilo Tester without choosing a mode, it will ask you:

```bash
liloit -u example.com
```

---

## ⚡ Quick Start

```bash
git clone https://github.com/yourusername/lilo-tester.git
cd lilo-tester

pip install -r requirements.txt
python -m playwright install chromium

python lilo_tester.py -u https://example.com
```

---

## 🦊 Use as `liloit`

Install it locally as a CLI command:

```bash
pip install -e .
```

Then run:

```bash
liloit -u example.com
```

---

## 🧠 Usage

### Quick Scan

```bash
liloit -u example.com --mode quick
```

### Full Scan

```bash
liloit -u example.com --mode full
```

### Full Scan with limits

```bash
liloit -u example.com --mode full --max-pages 30 --depth 2
```

### Test specific devices

```bash
liloit -u example.com -d desktop mobile
```

### Show browser while testing

```bash
liloit -u example.com --no-headless
```

### Run without opening report automatically

```bash
liloit -u example.com --no-open-report
```

### Disable safe form test

```bash
liloit -u example.com --no-form-test
```

---

## ⚙️ CLI Options

| Flag | Description |
| ---- | ----------- |
| `-u, --url` | Target website URL |
| `--mode` | Scan mode: `quick` or `full` |
| `--full-scan` | Shortcut for full scan |
| `--max-pages` | Maximum pages for full scan |
| `--depth` | Internal crawl depth |
| `-d, --devices` | Devices to test: desktop, tablet, mobile |
| `-o, --output` | Output folder |
| `--no-headless` | Show browser window while testing |
| `--no-form-test` | Disable safe dummy form validation |
| `--no-open-report` | Do not open report automatically |

---

## 🧪 Safe Form Testing

Lilo Tester can safely test forms by filling fields with dummy data and checking validation rules.

It is designed to avoid real submissions, so it will not intentionally create bookings, orders, messages, or accounts.

It checks:

- required fields
- invalid inputs
- missing labels
- broken form validation
- fields that fail after dummy fill
- forms without submit buttons

Disable it anytime:

```bash
liloit -u example.com --no-form-test
```

---

## 📦 Installation

<details>
<summary>🪟 Windows</summary>

Install Python from [python.org](https://www.python.org/downloads/).

During installation, make sure to enable:

```text
Add Python to PATH
```

Then run:

```bash
git clone https://github.com/yourusername/lilo-tester.git
cd lilo-tester

pip install -r requirements.txt
python -m playwright install chromium

pip install -e .
liloit -u example.com
```

If `python` is not recognized, use:

```bash
py -m pip install -r requirements.txt
py -m playwright install chromium
py lilo_tester.py -u example.com
```

</details>

---

<details>
<summary>🍎 macOS</summary>

```bash
brew install python@3.12

git clone https://github.com/yourusername/lilo-tester.git
cd lilo-tester

pip3 install -r requirements.txt
python3 -m playwright install chromium

pip3 install -e .
liloit -u example.com
```

Fallback:

```bash
python3 lilo_tester.py -u example.com
```

</details>

---

<details>
<summary>🐧 Linux</summary>

```bash
sudo apt update
sudo apt install python3 python3-pip

git clone https://github.com/yourusername/lilo-tester.git
cd lilo-tester

pip install -r requirements.txt
python3 -m playwright install chromium
python3 -m playwright install-deps chromium

pip install -e .
liloit -u example.com
```

Fallback:

```bash
python3 lilo_tester.py -u example.com
```

</details>

---

## 📂 Output

Every scan generates a timestamped report folder:

```bash
lilo_reports/
└── report_YYYY-MM-DD_HH-MM-SS/
    ├── report.html
    ├── report.json
    └── screenshots/
        ├── desktop_YYYY-MM-DD_HH-MM-SS.png
        ├── tablet_YYYY-MM-DD_HH-MM-SS.png
        ├── mobile_YYYY-MM-DD_HH-MM-SS.png
        └── fullpage_YYYY-MM-DD_HH-MM-SS.png
```

Open:

```bash
report.html
```

in your browser.

---

## 📊 Report Details

The HTML report includes collapsible details for issues such as:

- broken internal links
- source page of broken links
- HTTP status codes
- console errors
- network failures
- missing SEO tags
- security header warnings
- accessibility issues
- form validation problems
- screenshot capture results

---

## 🛠 Troubleshooting

### `liloit` command not found

Run:

```bash
pip install -e .
```

Then try again:

```bash
liloit -u example.com
```

Fallback:

```bash
python lilo_tester.py -u example.com
```

---

### Playwright browser missing

```bash
python -m playwright install chromium
```

On Linux:

```bash
python -m playwright install-deps chromium
```

---

### Website gets stuck or loads forever

Try quick mode first:

```bash
liloit -u example.com --mode quick
```

Or show the browser:

```bash
liloit -u example.com --mode quick --no-headless
```

---

### Screenshots are missing

Run:

```bash
liloit -u example.com --mode quick --no-headless
```

Then check:

```bash
lilo_reports/
```

If needed, use the direct Python fallback:

```bash
python lilo_tester.py -u example.com --mode quick --no-headless
```

---

### Full scan is too slow

Limit the scan:

```bash
liloit -u example.com --mode full --max-pages 10 --depth 1
```

---

### Python 3.14 issues

If some packages fail on Python 3.14, use Python 3.12.

Recommended:

```bash
python --version
```

Best stable target:

```text
Python 3.12
```

---

## 🧪 Why Lilo Tester?

Most testing tools are:

- Overcomplicated
- Noisy
- Slow
- Too much setup

Lilo Tester is:

> **Focused. Fast. Practical.**

Made for quick website diagnostics without the usual setup pain.

---

## 🪪 License

MIT License