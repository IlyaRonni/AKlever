# AKLEVER - VK Clever automation tool

## Installation
1. Install dependencies:
```bash
wget https://github.com/mozilla/geckodriver/releases/download/v0.20.1/geckodriver-v0.20.1-linux64.tar.gz -qO- | sudo tar xvz -C /usr/bin
```
2. Clone repo:
```bash
git clone https://github.com/TaizoGem/AKlever.git && cd AKlever
```
3. Run cli.py:
```bash
python3 cli.py
```

## Usage
| Command            | Description                                      |
|--------------------|--------------------------------------------------|
| `q, e, exit`       | Exits from app                                   |
| `custom`           | Runs qustom query, mostly used for debug and fun |
| `settings, config` | Opens settings interface ___TODO___              |
| `?, h`             | Opens help (similar to this table)               |
| `auth`             | Re-obtain token, used if some errors present     |
| `run, start`       | Start bot                                        |