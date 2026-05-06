# 🦊 Lilo Tester

<p align="center">
  <strong>Web Automation Testing Suite</strong><br>
  <em>Fast. Minimal. Straight to the point.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-blue" />
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey" />
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

Lilo Tester is a lightweight CLI tool that scans any website and generates a **complete diagnostic report** in seconds.

No setup complexity.
No config files.
No unnecessary noise.

Just run it.

---

## ⚡ What You Get

* ⚡ **Performance insights**
* 🔍 **SEO & meta validation**
* 🔗 **Broken links detection**
* 🐞 **Console error tracking**
* 🛡 **Security headers audit**
* ♿ **Accessibility checks**
* 📱 **Responsive testing**
* 📸 **Multi-device screenshots**

---

## ⚡ Quick Start

```bash
git clone https://github.com/yourusername/lilo-tester.git
cd lilo-tester
pip install -r requirements.txt
playwright install chromium
python lilo_tester.py --url https://example.com
```

---

## 🧠 Usage

```bash
python lilo_tester.py -u https://target.com
```

### Advanced

```bash
python lilo_tester.py -u https://target.com -d desktop mobile
python lilo_tester.py -u https://target.com --no-headless
```

---

## ⚙️ CLI Options

| Flag            | Description               |
| --------------- | ------------------------- |
| `-u, --url`     | Target website (required) |
| `-d, --devices` | desktop / tablet / mobile |
| `-o, --output`  | Output folder             |
| `--no-headless` | Show browser              |

---

## 📦 Installation

<details>
<summary>🪟 Windows</summary>

```bash
# install python from python.org (check "Add to PATH")

git clone https://github.com/yourusername/lilo-tester.git
cd lilo-tester
pip install -r requirements.txt
playwright install chromium

python lilo_tester.py --url https://example.com
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
playwright install chromium

python3 lilo_tester.py --url https://example.com
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

playwright install chromium
playwright install-deps chromium

python3 lilo_tester.py --url https://example.com
```

</details>

---

## 📂 Output

```bash
lilo_reports/
└── report_xxx/
    ├── report.html
    └── screenshots/
```

Open `report.html` in your browser.

---

## 🧪 Why Lilo Tester?

Most testing tools are:

* Overcomplicated
* Noisy
* Slow

Lilo Tester is:

> **Focused. Fast. Practical.**

---

## 🪪 License

MIT License
