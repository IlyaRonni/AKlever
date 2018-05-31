# AKLEVER - Trivia automation tool

## Installation
1. Clone repo:
```bash
git clone https://github.com/TaizoGem/AKlever.git && cd AKlever
```
2. Run cli.py:
```bash
python cli.py
```

## Usage
| Command            | Description                                       |
|--------------------|---------------------------------------------------|
| `q, e, exit`       | Exits from app                                    |
| `custom, c`        | Runs qustom query, mostly used for debug and fun  |
| `config`           | Opens settings interface                          |
| `?, h`             | Opens help (similar to this table)                |
| `auth`             | Re-obtain token, used if some errors present      |
| `run, start`       | Start bot                                         |
| `vidinfo`          | Gets video information from VK api                |

## Console
| Options            | Description                                       |
|--------------------|---------------------------------------------------|
| `--only=<command>` | Only runs command passed instead of text interface|
| `-h, --help`       | Shows help and quits                              |
| `--token=<token>`  | Overwrites token for this session                 |
| `--custom=<string>`| Processes passed question in syntax q:a1#a2#a2    |
