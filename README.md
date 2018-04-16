# AKLEVER - VK Clever automation tool

## Installation
### First way
1. Install dependencies:
```bash
sudo pip install selenium
wget https://github.com/mozilla/geckodriver/releases/download/v0.20.1/geckodriver-v0.20.1-linux64.tar.gz -qO- | sudo tar xvz -C /usr/bin
```
2. Clone repo:
```bash
git clone https://github.com/TaizoGem/AKlever.git && cd AKlever
```
3. Run gui.py:
```bash
python3 gui.py
```
### Second way
1. Clone repo:
```bash
git clone https://github.com/TaizoGem/AKlever.git && cd AKlever
```
2. Get login token [here](https://oauth.vk.com/authorize?client_id=6334949w&display=page&scope=friends&response_type=token&v=5.73)
3. Put your token to `token.ak` file:
```bash
// you can do it any way you want, for example:
echo "your token" > token.ak 
```
4. Run gui.py:
```bash
python3 gui.py
```
## Parts
 - Left list: basic information about your account and next game
 - UPD button: refresh left list
 - Start button: start bot
 - Stop button: stop bot
 - Top right text field - question will appear there
 - 3 buttons with percent sign - answers with possibilities will appear there
