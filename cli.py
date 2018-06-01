#!/usr/bin/python3
import os
import random
import re
from datetime import datetime, timezone
import json
import sys
import time
import urllib.request, urllib.parse
import requests.exceptions
import logging
import webbrowser
import configparser

try:
    from lomond import WebSocket

    WS_INSTALLED = True
except ImportError:
    print("WebSocket module is not installed. VVP, HQ and CS won't be available.", file=sys.stderr)
    WS_INSTALLED = False
IS_EXE = __file__[:-4] == ".exe"
APP_NAME = "AKlever"  # if you want you can change name of bot here - it will change everywhere
VERSION = 0.94
logging.basicConfig(format='[%(levelname)s] %(message)s')
logger = logging.getLogger(APP_NAME)


def isInt(str):
    try:
        return int(str)
    except:
        return "no"


def checkUpdates():
    print("Checking for updates...", end="\r")
    try:
        v = requests.get("https://raw.githubusercontent.com/TaizoGem/AKlever/master/version").text
        float(v)
    except:
        print("Unable to check for updates. Current version:", VERSION)
        return
    if float(v) > float(VERSION):
        print("New version is available, would you like to auto-update?")
        if input("[Y/n] ") not in ("n", "N", "П", "п"):
            if IS_EXE:
                newversion = requests.get(
                    "https://github.com/TaizoGem/AKlever/releases/download/v" + v + "/aklever.exe")
                if newversion.status_code == 200:
                    import string
                    filename = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6)) + ".exe"
                    with open(filename, "wb") as f:
                        f.write(newversion.content)  # \/\/\/\/\/\/\/ waiting 3 seconds before copying
                    os.system(
                        "start \"updating aklever\" cmd /c \"ping 127.0.0.1 -n 3 & move " + filename + " " + __file__ + " & start " + __file__ + "\"")
                else:
                    print("It seems that you are using .exe version of bot, and latest version is not yet compiled.\n"
                          "Can't proceed.")
            else:
                newversion = requests.get(
                    "https://raw.githubusercontent.com/TaizoGem/AKlever/master/cli.py")
                if newversion.status_code == 200:
                    import string
                    filename = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6)) + ".py"
                    with open(filename, "wb") as f:
                        f.write(newversion.content)
                    os.system(
                        "start \"updating aklever\" cmd /c \"ping 127.0.0.1 -n 3 & move " + filename + " " + __file__ + " & python " + __file__ + "\"")
                else:
                    print("Oops, something went wrong. Can't proceed. Error code", newversion.status_code)


class KleverAnswer():
    def __init__(self, text, coincidences):
        self.text = text
        self.coincidences = coincidences
        self.probability = 0

    def __str__(self):
        return self.text + " | " + str(self.probability) + "%"

    def setProbability(self, new):
        self.probability = new


class KleverQuestion(object):
    def __init__(self, question, answers: list, sent_time: int, kid: int, optimized: str):
        self.question = question
        self.answers = answers
        self.sent_time = sent_time
        self.id = kid
        self.reverse = " не " in question.lower() or " ни " in question.lower()
        self.optimized = optimized

    def __str__(self):
        return self.question + ":" + self.answers[0].text + "#" + self.answers[1].text + "#" + self.answers[2].text

    def calculate_probability(self):
        total = 0
        for answer in self.answers:
            total += answer.coincidences  # first of all count total, then anything else
        for answer in self.answers:
            if total == 0:
                answer.setProbability(0)
            else:
                answer.setProbability(round(answer.coincidences / total * 100, 1))
        if total == 0:
            self.question += " | NOT FOUND!"
            self.best = "0. ???"
        else:
            a = min(self.answers[a].coincidences for a in range(3)) if self.reverse else \
                max(self.answers[a].coincidences for a in range(3))
            i = 0
            for answer in self.answers:
                i += 1
                if answer.coincidences == a:
                    self.best = str(i) + ". " + answer.text


class KleverGoogler():
    FILTERED_WORDS = ("сколько", "как много", "вошли в историю как", "какие", "как называется", "чем является",
                      "что из этого", "(у |)как(ой|ого|их) из( этих|)", "какой из героев", "традиционно", "согласно",
                      " - ",
                      "чем занимается", "чья профессия", "состоялся", "из фильма", "что из этого",
                      "какой", "является", "в мире", "и к", "термин(ов|ы|)", "относ(и|я)тся", "в какой",
                      "у как(ого|ой|их)", "согласно", "на каком", "состоялся", "по численности", " не ", " ни ")
    OPTIMIZE_DICT = {
        "в каком году": "когда",
        "какого животного": "кого",  ###############################
        "один": "1",  ###############################
        "одна": "1",  ###############################
        "одно": "1",  ####        #######        ####
        "два": "2",  ####        #######        ####
        "двое": "2",  ####        #######        ####
        "две": "2",  ####        #######        ####
        "три": "3",  ###############################
        "трое": "3",  ##############   ##############
        "четыре": "4",  ##############   ##############
        "четверо": "4",  ##############   ##############
        "пять": "5",  ###############################
        "пятеро": "5",  ########               ########
        "шесть": "6",  ########               ########
        "шестеро": "6",  ####    ###############   #####
        "семь": "7",  ####    ###############   #####
        "семеро": "7",  ###############################
        "восемь": "8",  ###############################
        "девять": "9",  #####                     #####
        "десять": "10",  #####                     #####
        "одиннадцать": "11",  #############     #############
        "двенадцать": "12",  #############     #############
        "тринадцать": "13",  #############     #############
        "четырнадцать": "14",  #############     #############
        "пятнадцать": "15",  #############     #############
        "шестнадцать": "16",  #############     #############
        "семнадцать": "17",  #############     #############
        "восемнадцать": "18",  #############     #############
        "девятнадцать": "19",  ###############################
        "двадцать": "20",  ###############################
        "тридцать": "30",  ###############################
        "сорок": "40",  ####         #####         ####
        "пятьдесят": "50",  ####  ############  ###########
        "шестьдесят": "60",  ####  ############  ###########
        "семьдесят": "70",  ####  #####  #####  #####  ####
        "восемьдесят": "80",  ####  ###### #####  ###### ####
        "девяносто": "90",  ####  ###### #####  ###### ####
        "сто": "100",  ####         #####         ####
        "двести": "200",  ###############################
        "триста": "300",  ###############################
        "четыреста": "400",  ###############################
        "пятьсот": "500",  ###############################
        "шестьсот": "600",  ###############################
        "семьсот": "700",  ###############################
        "восемьсот": "800",  ######                   ######
        "девятсот": "900",  ######  if you use this  ######
        "тысача": "1000",  ######    please leave   ######
        " тысячи": "000",  ######  copyright notice ######
        " тысяч": "000",  ######                   ######
        "миллион": "1000000",  ######   (c) TaizoGem    ######
        " миллиона": "000000",  ###############################
        " миллионов": "000000"  ###############################
    }

    def __init__(self, question: str, answers, sent_time: int, num: int):
        self._question = question
        self.__question = self.optimizeString(question)
        self.answers = []
        self.__answers = [self.optimizeString(a) for a in answers]
        self.newquestion = self.__question + '("' + '" | "'.join(answers) + '")'
        self.conn = requests.Session()
        self.sent_time = sent_time
        self.number = num

    def fetch(self, query, newquery=""):
        try:
            print("Performing search for", query, end="\r")
            google = self.conn.get("https://www.google.ru/search?q=" + urllib.parse.quote_plus(query)).text.lower()
            yandex = self.conn.get("https://www.yandex.ru/search/?text=" + urllib.parse.quote_plus(query)).text.lower()
            newyandex = self.conn.get("https://www.yandex.ru/search/?text=" + urllib.parse.quote_plus(
                newquery)).text.lower() if newquery else ""
            ddg = self.conn.get("https://duckduckgo.com/?q=" + urllib.parse.quote_plus(query) + "&format=json").json()
            out = ""
            try:
                smth = self.conn.get(ddg["AbstractURL"]).text.lower()
                out += smth
            except:
                pass
            out += ddg["Abstract"]
            if not "Our systems have detected unusual traffic from your computer network" in google \
                    and not "support.google.com/websearch/answer/86640" in google:
                out += google
            if not "{\"captchaSound\"" in yandex:
                out += yandex
            if not "{\"captchaSound\"" in newyandex:
                out += newyandex
            return out
        except Exception as e:
            logger.error("Exception occurred while trying to search:" + str(e))
            return ""

    def search(self):
        response = self.fetch(self.__question, self.newquestion)
        if all(" и " in s for s in self.__answers):  # если И есть в каждом ответе...
            print("Found multipart question", end="\r")
            for answer in self.__answers:
                current_count = 0
                for part in answer.split(" и "):
                    current_count += len(
                        re.findall("(:|-|!|.|,|\?|;|\"|'|`| )" + part.lower() + "(:|-|!|.|,|\?|;|\"|'|`| )", response))
                    logger.debug("processed " + part + ", found " + str(current_count) + " occs in total")
                self.answers.append(KleverAnswer(answer, current_count))
        else:
            logger.info("usual question, processing..")
            for answer in self.__answers:
                current_count = 0
                for part in answer.split(" "):
                    current_count += len(
                        re.findall("(:|-|!|.|,|\?|;|\"|'|`| )" + part.lower() + "(:|-|!|.|,|\?|;|\"|'|`| )", response))
                    logger.debug("processed " + part + ", found " + str(current_count) + " occs in total")
                self.answers.append(KleverAnswer(answer, current_count))
        a = [b.coincidences for b in self.answers]
        if a[1:] == a[:-1]:
            self.doReverse(a)
        del a

    def doReverse(self, prev_results=(0, 0, 0)):
        logger.info("doing reverse search..")
        self.answers = []
        i = 0
        for answer in self.__answers:
            rsp = self.fetch(self.optimizeString(answer))
            sumd = 0
            for word in self.getLemmas(self.__question):
                sumd += len(re.findall("(:|-|!|.|,|\?|;|\"|'|`| )" + word.lower() + "(:|-|!|.|,|\?|;|\"|'|`| )", rsp))
                logger.debug("processed " + word + ", found " + str(sumd) + " occs in total")
            self.answers.append(KleverAnswer(answer, prev_results[i] + sumd))
            i += 1
        self.ran_reverse = True

    def genQuestion(self):
        a = KleverQuestion(self._question, self.answers, self.sent_time, self.number, self.__question)
        a.calculate_probability()
        return a

    def optimizeString(self, base):
        base = base.lower()
        base = re.sub("[\'@<!«»?,.]", "", base)
        base = re.sub("(" + "|".join(self.FILTERED_WORDS) + ")( |)", "", base)
        pattern = re.compile(r'\b(' + '|'.join(self.OPTIMIZE_DICT.keys()) + r')\b')
        base = pattern.sub(lambda x: self.OPTIMIZE_DICT[x.group()], base)
        logger.info("optimized string:" + base)
        return base

    def getLemmas(self, base):
        out = []
        for a in requests.get(
                "http://www.solarix.ru/php/lemma-provider.php?query=" + urllib.parse.quote_plus(base)).text.split(" "):
            a = a.replace("\r\n", "")
            if a:
                out.append(a)
        return out


class CleverBot(object):
    GAME_STATE_PLANNED = "Planned"
    GAME_STATE_STARTED = "Started"
    GAME_STATE_FINISHED = "Finished"
    ACTIONS = (
        "?", "h", "run", "start", "auth", "custom", "exit", "e", "settings", "config", "q", "c", "vidinfo", "r", "vvp")

    def __init__(self):
        super().__init__()
        self.corrects = 0
        self.token = ""
        self.config = configparser.ConfigParser()
        self.initConfig()
        self.logfile = ""
        self.vid = ""
        self.longPollServer = ""
        if self.config["Config"]["debug_mode"] == "verbose":
            logger.setLevel(logging.DEBUG)
        elif self.config["Config"]["debug_mode"] == "basic":
            logger.setLevel(logging.INFO)
        elif self.config["Config"]["debug_mode"] not in ("verbose", "disabled", "basic"):
            self.config["Config"]["debug_mode"] = "disabled"
        if self.config["Config"]["updates"] not in ("off", "on"):
            self.config["Config"]["updates"] = "off"
        if self.config["Config"]["answer_ui"] not in ("off", "on"):
            self.config["Config"]["answer_ui"] = "off"
        if self.config["Config"]["updates"] == "on":
            checkUpdates()
        if self.config["Social"]["telegram"] not in ("off", "on"):
            self.config["Social"]["telegram"] = "off"
        if self.config["Social"]["telegram_auto"] not in ("off", "on"):
            self.config["Social"]["telegram_auto"] = "off"
        self.game_start = 0
        self.prize = 0
        self.balance = 0
        self.lives = 0
        self.coins = 0
        self.rating = 0
        self.state = 0
        self.current_answer = ""
        self.buf = ""
        self.proxies = {"http": "socks5h://" + self.config["Social"]["telegram_proxy"],
                        "https": "socks5h://" + self.config["Social"]["telegram_proxy"]} if self.config["Social"][
            "telegram_proxy"] else {}
        self.getToken()
        self.getStartData()

    def runCustom(self, q=""):
        if q == "":
            print("Input question in this format:")
            print("questionText:answer1#answer2#answer3")
            q = input("> ")
        try:
            q = q.split(":")
            e = q[1].split("#")
            google = KleverGoogler(q[0], e, 0, 0)
            google.search()
            g = google.genQuestion()
            self.displayQuestion(g, google, True)
        except (KeyError, IndexError):
            print("malformed input, cancelling")

    def saveConfig(self):
        with open("config.ak", "w") as config_file:
            self.config.write(config_file)

    def configurate(self):
        edited = False
        while True:
            print("Configurating " + APP_NAME + ". Choose option to edit from list below:")
            print("1. Debug mode:", self.config["Config"]["debug_mode"])
            print("2. VK auth token")
            print("3. Updates check:", self.config["Config"]["updates"])
            print("4. Telegram integration")
            print("5. Answer UI:", self.config["Config"]["answer_ui"])
            print("0. Save and exit", "[EDITED]" if edited else "")
            a = input("[0-5] > ")
            while isInt(a) not in range(7):
                print("Invalid option")
                a = input("[0-5] > ")
            a = int(a)
            if a == 0:
                self.saveConfig()
                self.__init__()
                return
            elif a == 1:
                while True:
                    print("1.", "[x]" if self.config["Config"]["debug_mode"] == "disabled" else "[ ]",
                          "Disabled - only log critical exceptions")
                    print("2.", "[x]" if self.config["Config"]["debug_mode"] == "basic" else "[ ]",
                          "Basic - log some information")
                    print("3.", "[x]" if self.config["Config"]["debug_mode"] == "verbose" else "[ ]",
                          "Verbose - log basically everything")
                    print("\n0. Back")
                    b = input("[0-3] > ")
                    while isInt(b) not in range(4):
                        print("Invalid option")
                        b = input("[0-3] > ")
                    b = int(b)
                    if b == 0:
                        break
                    elif b == 1:
                        self.config["Config"]["debug_mode"] = "disabled"
                    elif b == 2:
                        self.config["Config"]["debug_mode"] = "basic"
                    elif b == 3:
                        self.config["Config"]["debug_mode"] = "verbose"
                    edited = True
            elif a == 2:
                while True:
                    print("Current auth token:", self.token[:6] + "******" + self.token[75:])
                    print("Current account:", self.getTokenInfo())
                    print("1. Edit token")
                    print("0. Back")
                    b = input("[0-1] > ")
                    while isInt(b) not in range(2):
                        print("Invalid option")
                        b = input("[0-1] > ")
                    b = int(b)
                    if b == 0:
                        break
                    elif b == 1:
                        self.getToken(True)
            elif a == 3:
                while True:
                    print("It is not recommended to disable update check")
                    print("1.", "[x]" if self.config["Config"]["updates"] == "on" else "[ ]", "Enable")
                    print("2.", "[x]" if self.config["Config"]["updates"] == "off" else "[ ]", "Disable")
                    print("0. Back")
                    b = input("[0-2] > ")
                    while isInt(b) not in range(3):
                        print("Invalid option")
                        b = input("[0-2] > ")
                    b = int(b)
                    if b == 0:
                        break
                    elif b == 1:
                        self.config["Config"]["updates"] = "on"
                    elif b == 2:
                        self.config["Config"]["updates"] = "off"
                    edited = True
            elif a == 4:
                while True:
                    print("Since 0.90 " + APP_NAME + " supports Telegram integration")
                    print("You can change:")
                    print("1. Enable:", self.config["Social"]["telegram"])
                    print("2. Bot token:",
                          self.config["Social"]["telegram_token"][:7] + "******" + self.config["Social"][
                                                                                       "telegram_token"][38:])
                    print("3. Channel to post: @" + self.config["Social"]["telegram_channel"])
                    print("4. Proxy: " + self.config["Social"]["telegram_proxy"])
                    print("5. Auto send to channel:", self.config["Social"]["telegram_auto"])
                    print("0. Back")
                    b = input("[0-5] > ")
                    while isInt(b) not in range(6):
                        print("Invalid input")
                        b = input("[0-5] > ")
                    b = int(b)
                    if b == 0:
                        break
                    elif b == 1:
                        while True:
                            print("Enable or disable Telegram integration")
                            print("1.", "[x]" if self.config["Social"]["telegram"] == "on" else "[ ]", "Enable")
                            print("2.", "[x]" if self.config["Social"]["telegram"] == "off" else "[ ]", "Disable")
                            print("0. Back")
                            c = input("[0-2] > ")
                            while isInt(b) not in range(3):
                                print("Invalid option")
                                c = input("[0-2] > ")
                            c = int(c)
                            if c == 0:
                                break
                            elif c == 1:
                                self.config["Social"]["telegram"] = "on"
                            elif c == 2:
                                self.config["Social"]["telegram"] = "off"
                            edited = True
                    elif b == 2:
                        while True:
                            print("To use Telegram integration you need a Bot token.")
                            print("To get it message @BotFather and register a bot")
                            print("1. Edit token")
                            print("0. Back")
                            c = input("[0-1] > ")
                            while isInt(c) not in range(2):
                                print("Invalid option")
                                c = input("[0-1] > ")
                            c = int(c)
                            if c == 0:
                                break
                            elif c == 1:
                                self.config["Social"]["telegram"] = input("Enter your token\n > ")
                            edited = True
                    elif b == 3:
                        while True:
                            print(
                                "For " + APP_NAME + " to work correctly, we need to know to which channel to post")
                            print("Your bot must be admin in this channel with rights to post messages")
                            print("1. Change channel")
                            print("0. Back")
                            c = input("[0-1] > ")
                            while isInt(c) not in range(2):
                                print("Invalid option")
                                c = input("[0-1] > ")
                            c = int(c)
                            if c == 0:
                                break
                            elif c == 1:
                                self.config["Social"]["telegram_channel"] = input("Enter your channel\n > @")
                            edited = True
                    elif b == 4:
                        while True:
                            print("In several countries, some providers (try to) block Telegram API server, so")
                            print("you may need a SOCKS5 proxy to connect")
                            print("1. Set proxy")
                            print("0. Back")
                            c = input("[0-1] > ")
                            while isInt(c) not in range(2):
                                print("Invalid option")
                                c = input("[0-1] > ")
                            c = int(c)
                            if c == 0:
                                break
                            elif c == 1:
                                self.config["Social"]["telegram_proxy"] = input(
                                    "Enter you proxy in this format: [login[:password]@]server.tld[:port]\n > ")
                            edited = True
                    elif b == 5:
                        while True:
                            print("Enable or disable auto answer sending")
                            print("1.", "[x]" if self.config["Social"]["telegram_auto"] == "on" else "[ ]", "Enable")
                            print("2.", "[x]" if self.config["Social"]["telegram_auto"] == "off" else "[ ]", "Disable")
                            print("0. Back")
                            c = input("[0-2] > ")
                            while isInt(c) not in range(3):
                                print("Invalid option")
                                c = input("[0-2] > ")
                            c = int(c)
                            if c == 0:
                                break
                            elif c == 1:
                                self.config["Social"]["telegram_auto"] = "on"
                            elif c == 2:
                                self.config["Social"]["telegram_auto"] = "off"
                            edited = True
            elif a == 5:
                while True:
                    print("Enable or disable answer UI")
                    print("1.", "[x]" if self.config["Social"]["answer_ui"] == "on" else "[ ]", "Enable")
                    print("2.", "[x]" if self.config["Social"]["answer_ui"] == "off" else "[ ]", "Disable")
                    print("0. Back")
                    c = input("[0-2] > ")
                    while isInt(c) not in range(3):
                        print("Invalid option")
                        c = input("[0-2] > ")
                    c = int(c)
                    if c == 0:
                        break
                    elif c == 1:
                        self.config["Social"]["answer_ui"] = "on"
                    elif c == 2:
                        self.config["Social"]["answer_ui"] = "off"
                    edited = True

    def getTokenInfo(self):
        a = json.loads(requests.get("https://api.vk.com/method/users.get?v=5.73&access_token=" + self.token).text)[
            "response"][0]
        return str(a["id"]) + " > " + a["first_name"] + " " + a["last_name"]

    def initConfig(self):
        if os.path.exists("config.ak"):
            logger.debug("config exists")
            self.config.read("config.ak")
            return
        logger.debug("creating config")
        self.config.add_section("Config")
        self.config.add_section("Social")
        self.config["Social"]["telegram"] = "off"
        self.config["Social"]["telegram_token"] = ""
        self.config["Social"]["telegram_channel"] = ""
        self.config["Social"]["telegram_proxy"] = ""
        self.config["Social"]["telegram_auto"] = ""
        self.config["Config"]["debug_mode"] = "disabled"
        self.config["Config"]["updates"] = "on"
        self.config["Config"]["answer_ui"] = "off"
        self.saveConfig()
        self.config.read("config.ak")

    def getToken(self, force=False):
        print("Getting token...    ", end="\r")
        if self.token and not force:
            return
        try:
            token = self.config["Config"]["token"]
        except KeyError:
            token = ""
        if token and self.validateToken(token) and not force:
            logger.debug("valid token found in file: " + token)
        else:
            logger.debug("token not found or is invalid, requesting..")
            print("Hi! You are 1 step behind using this bot! Since VK Clever sends questions via VK API, we need access"
                  "\ntoken to be able to get them. It is important to use token with Clever appid.\n"
                  "To get token you just need to click enter, authenticate app in browser (if not already)\n"
                  "and paste url or token here\n -> If you already have a token, just press E before enter" if not force
                  else "E if you already have token")
            while True:
                if input("[PRESS ENTER NO OPEN AUTH PAGE]") not in ("e", "E", "У", "у"):
                    try:
                        webbrowser.open(
                            "https://oauth.vk.com/authorize?client_id=6334949&display=page&scope=friends,offline,video&response_type=token&v=5.73")
                    except Exception:
                        print("failed to open browser, open it by yourself, please:\n"
                              "https://oauth.vk.com/authorize?client_id=6334949&display=page&scope=friends,offline,video&response_type=token&v=5.73")
                    time.sleep(3)
                print("Token or url:")
                a = input("> ")
                if "access_token" in a:
                    try:
                        token = a.split("#access_token=")[1].split('&')[0]
                    except Exception:
                        print("Malformed url given, please try again")
                        continue
                    if not self.validateToken(token):
                        print("Invalid token, please try again")
                        continue
                    else:
                        break
                elif self.validateToken(a):
                    token = a
                    break
                else:
                    print("Invalid token, please try again")
                    continue
        self.token = token
        self.config["Config"]["token"] = self.token
        self.saveConfig()

    def validateToken(self, token=None):
        if not token:
            token = self.token
        out = json.loads(
            urllib.request.urlopen("https://api.vk.com/method/users.get?v=5.73&access_token=" + token).read())
        try:
            out["response"]
            logger.debug("token is valid")
            return True
        except KeyError:
            logger.debug("token is invalid")
            return False

    def getStartData(self):
        print("Getting data...       ", end="\r")
        response = json.loads(requests.post("https://api.vk.com/method/execute.getStartData",
                                            data={"build_ver": 3078, "need_leaderboard": 0, "func_v": -1,
                                                  "access_token": self.token, "v": "5.73", "lang": "ru",
                                                  "https": 1}).text)["response"]
        try:
            self.game_start = response["game_info"]["game"]["start_time"]
        except:
            self.game_start = 0
        self.balance = response["game_info"]["user"]["balance"]
        self.lives = response["game_info"]["user"]["extra_lives"]
        self.rating = response["game_info"]["rating_percent"]
        self.prize = response["game_info"]["game"]["prize"]
        self.coins = response["game_info"]["user"]["coins"]
        a = response["game_info"]["game"]["status"]
        if a == "planned":
            self.state = self.GAME_STATE_PLANNED
        elif a == "started":
            self.state = self.GAME_STATE_STARTED
            self.vid = str(response["game_info"]["game"]["video_owner_id"]) + "_" + str(
                response["game_info"]["game"]["video_id"])
            self.longPollServer = requests.post("https://api.vk.com/method/video.getLongPollServer", data={
                "video_id": response["game_info"]["game"]["video_id"],
                "owner_id": response["game_info"]["game"]["video_owner_id"],
                "access_token": self.token,
                "v": 5.73,
                "lang": "ru",
                "https": 1
            }).json()["response"]["url"]
        elif a == "finished":
            self.state = self.GAME_STATE_FINISHED
        # BASE DATA DISPLAY #
        print("======={ YOUR STATS }=======")
        print("BALANCE (RUB):  " + str(self.balance))
        print("EXTRA LIVES:  \t" + str(self.lives))
        print("CLEVERS:  \t" + str(self.coins))
        print("RATING (%):  \t" + str(self.rating))
        print("======={ GAME  INFO }=======")
        print("NEXT GAME:     ", datetime.utcfromtimestamp(self.game_start).replace(tzinfo=timezone.utc).astimezone(
            tz=None).strftime("%H:%M") if self.state != self.GAME_STATE_STARTED else "NOW!")
        print("PRIZE (RUB):  \t" + str(self.prize))
        print("STATE:  \t" + str(self.state))
        # END BASE DATA DISPLAY #

    def showCliHelp(self):
        self.showHelp()
        print("\n" + APP_NAME + " can also work in CLI mode! You can see list of available params in list below:",
              "--only=<run|config> - only runs command passed instead of text interface",
              "-h, --help          - shows this help and quits",
              "--token=<token>     - overwrites token for this session (does NOT change token in config file)",
              "--custom=<string>   - processes passed question in syntax q:a1#a2#a2, displays output and quits",
              sep="\n")

    def parseArgs(self, argv: list):
        for arg in argv:
            if arg in ("--help", "-h"):
                self.showCliHelp()
                sys.exit()
            elif "--logfile" in arg:
                if not "=" in arg or len(arg.split("=")[1]) == 0:
                    global logger
                    logging.basicConfig(filename="log.ak", filemode="a", format='[%(levelname)s] %(message)s')
                    logger = logging.getLogger(APP_NAME)
                else:
                    logging.basicConfig(filename=arg.split("=")[1], filemode="a", format='[%(levelname)s] %(message)s')
                    logger = logging.getLogger(APP_NAME)
            elif "--token" in arg:
                if not "=" in arg:
                    print("Token is not specified!")
                    sys.exit(1)
                print("Validating token..\r", end="")
                if not self.validateToken(arg.split("=")[1]):
                    print("Token is invalid!     ")
                    sys.exit()
                self.token = arg.split("=")[1]
            elif "--custom" in arg:
                try:
                    query = arg.split("=")[1]
                    self.runCustom(query)
                    sys.exit()
                except Exception:
                    self.runCustom()
                    sys.exit()
            elif "--only" in arg:
                if not "=" in arg or arg.split("=")[1] not in ("run", "config"):
                    print("Action must be specified:\n $ python cli.py --only=run")
                    sys.exit(1)
                else:
                    if arg.split("=")[1] == "run":
                        self.startGame()
                        sys.exit()
                    else:
                        pass
                        self.configurate()

    def startGame(self):
        print("To stop press Ctrl-C")
        self.corrects = 0
        while True:
            try:
                # example question https://gist.githubusercontent.com/TaizoGem/1aea44b8e5fa05550f50617673809ccb/raw/a93b1b060a595142c8ed13111a5e56f4e1afe6ee/aklever.test.json
                # base server https://api.vk.com/method/execute.getLastQuestion
                response = json.loads(requests.post("https://api.vk.com/method/execute.getLastQuestion",
                                                    data={"access_token": self.token, "v": "5.73", "https": 1}).text)[
                    "response"]
                if response:
                    print("Received question, thinking...", end="\r")
                    logger.debug("got question: " + response["text"])
                    google = KleverGoogler(response["text"], [response["answers"][i]['text'] for i in range(3)],
                                           response["sent_time"], response["number"])
                    try:
                        google.search()
                    except ConnectionResetError as e:
                        print("Exception occurred: errno", e.errno, file=sys.stderr)
                        continue
                    question = google.genQuestion()
                    self.displayQuestion(question, google)
                    while True:
                        answrsp = requests.post("https://api.vk.com/method/streamQuiz.getCurrentStatus",
                                                data={"access_token": self.token, "v": "5.73", "lang": "ru",
                                                      "https": 1}).json()["response"]["question"]
                        try:
                            correct = answrsp["right_answer_id"]
                            self.displayQuestion(question, google, False, correct)
                            if int(question.best[0]) - 1 == correct:
                                self.corrects += 1
                            break
                        except KeyError:
                            time.sleep(2)
                else:
                    logger.debug("No question, waiting..")
                    time.sleep(1)
            except (KeyboardInterrupt, SystemExit):
                logger.debug("stopping")
                return
            except requests.exceptions.ConnectionError:
                pass

    def showHelp(self):
        print("This is " + APP_NAME + ", bot for VK Clever, quiz with money prizes by VK Team\n"
                                      "Coded by TaizoGem, source is available at:\ngithub.com/TaizoGem/AKlever\n"
                                      "Current version:", VERSION,
              "\n\nAvailable commands:\n"
              "?, h        - display this menu\n"
              "run, start  - start working\n"
              "auth        - re-auth in application\n"
              "custom, c   - process a custom question\n"
              "e, exit     - exit from application\n"
              "vidinfo     - information about current video\n"
              "config      - configure application")

    def displayQuestion(self, question: KleverQuestion, googler: KleverGoogler, is_custom: bool = False, correct=-1):
        print("Question " + str(question.id) + ":", question.question)
        print("==============================\n")
        for i in range(3):
            sign = "[ ]"
            if i == int(question.best[0]) - 1:
                sign = "[~]"
            if i == correct:
                sign = "[x]"
            print(sign, "Answer " + str(i + 1) + ":",
                  str(question.answers[i]))
        if correct != -1:
            print("Bot status: " + ("" if int(question.best[0]) - 1 == correct else "in") + "correct, " + \
                str(self.corrects) + "/12")
        if self.config["Config"]["debug_mode"] in ("basic", "verbose"):
            print("Query for custom question:\n" + str(question))
            print("Optimized question:", question.optimized)
        if self.config["Social"]["telegram_auto"] == "on":
            message = "Question " + str(question.id) + ": " + question.question
            message += "\n==============================\n"
            for i in range(3):
                sign = "`[ ]`"
                if i == int(question.best[0]) - 1:
                    sign = "`[~]`"
                if i == correct:
                    sign = "`[x]`"
                message += "\n" + sign + " Answer " + str(i + 1) + ": " + str(question.answers[i])
            message += "\n\n==============================\n"
            message += "Bot status: " + ("" if int(question.best[0]) - 1 == correct else "in") + "correct, " + \
                       str(self.corrects) + "/12"
            try:
                requests.post(
                    "https://api.telegram.org/bot" + self.config["Social"]["telegram_token"] + "/sendMessage",
                    json=dict(chat_id="@" + self.config["Social"]["telegram_channel"],
                              text=message,
                              parse_mode="markdown"), proxies=self.proxies)
            except requests.exceptions.InvalidSchema:
                print("Unable to send message to channel because socks support is not installed")
        if self.config["Config"]["answer_ui"] == "yes":
            while True:
                print("0. Continue")
                print("1. Re-google")
                num = (0, 1)
                if not googler.ran_reverse:
                    num += (2,)
                    print("2. force do reverse search")
                if not self.config["Social"]["telegram_auto"] == "yes":
                    num += (3,)
                    print("3. Send to @" + self.config["Social"]["telegram_channel"])
                a = input(" > ")
                while isInt(a) not in num:
                    a = input(" > ")
                a = int(a)
                if a == 0:
                    print()
                    return
                elif a == 1:
                    googler.search()
                    self.displayQuestion(googler.genQuestion(), googler)
                    print()
                    return
                elif a == 2:
                    googler.doReverse()
                    self.displayQuestion(googler.genQuestion(), googler)
                    print()
                    return
                elif a == 3:
                    message = "Question " + str(question.id) + ": " + question.question
                    message += "\n==============================\n"
                    for i in range(3):
                        sign = "`[ ]`"
                        if i == int(question.best[0]) - 1:
                            sign = "`[~]`"
                        if i == correct:
                            sign = "`[x]`"
                        message += "\n" + sign + " Answer " + str(i + 1) + ": " + str(question.answers[i])
                    message += "\n\n==============================\n"
                    message += "Bot status: " + ("" if int(question.best[0]) - 1 == correct else "in") + "correct, " + \
                               str(self.corrects) + "/12"
                    try:
                        requests.post(
                            "https://api.telegram.org/bot" + self.config["Social"]["telegram_token"] + "/sendMessage",
                            json=dict(chat_id="@" + self.config["Social"]["telegram_channel"],
                                      text=message,
                                      parse_mode="markdown"), proxies=self.proxies)
                    except requests.exceptions.InvalidSchema:
                        print("Unable to send message to channel because socks support is not installed")
        elif not is_custom:
            time.sleep(10)

    def mainloop(self):
        while True:
            try:
                action = input("[? for help] " + APP_NAME + " > ").lower()
                if action not in self.ACTIONS:
                    print("Invalid action, enter ? or h for help")
                    continue
                if action in ("?", "h",):
                    self.showHelp()
                elif action in ("run", "start"):
                    self.startGame()
                elif action in ("e", "exit", "q"):
                    sys.exit()
                elif action in ("custom", "c"):
                    self.runCustom()
                elif action in ("cfg", "config"):
                    self.configurate()
                elif action == "vidinfo":
                    if self.state == self.GAME_STATE_STARTED:
                        print("Current video:")
                        print("https://vk.com/video" + self.vid)
                        print("Longpoll server:")
                        print(self.longPollServer)
                    else:
                        print("Game is not running now, nothing to display!")
                elif action == "r":
                    self.__init__()
                    self.getStartData()

            except (KeyboardInterrupt, EOFError):
                if self.config["Config"]["debug_mode"] == "disabled":
                    print("\nTo exit execute command 'q'")
                else:
                    print("\nFinishing..")
                    sys.exit()


class VVPBot:
    SERVERS = (
        "ws://ws-tosno1.trivia.incrdbl.me:8888/socket",
        "ws://ws-tosno2.trivia.incrdbl.me:8888/socket",
        "ws://ws-tosno3.trivia.incrdbl.me:8888/socket",
        "ws://ws-tosno4.trivia.incrdbl.me:8888/socket",
        "ws://ws-tosno5.trivia.incrdbl.me:8888/socket",
        "ws://ws-tosno6.trivia.incrdbl.me:8888/socket",
        "ws://ws-luga1.trivia.incrdbl.me:8888/socket",
        "ws://ws-luga2.trivia.incrdbl.me:8888/socket",
        "ws://ws-luga3.trivia.incrdbl.me:8888/socket",
        "ws://ws-luga4.trivia.incrdbl.me:8888/socket",
        "ws://ws-luga5.trivia.incrdbl.me:8888/socket",
        "ws://ws-luga6.trivia.incrdbl.me:8888/socket"
    )

    def mainloop(self):
        print("to start press enter and to stop press ctrl+c")
        input("<press enter>")
        srv = random.choice(self.SERVERS)
        logger.debug(srv)
        conn = WebSocket(srv)
        corrects = 0
        last_answer = None
        for msg in conn.connect():
            if msg.name == "text":
                a = json.loads(msg.text)
                if a["method"] == "round_question":
                    b = a["params"]["answers"]
                    googler = KleverGoogler(a["params"]["text"], [b[i]["text"] for i in range(4)],
                                            int(time.time()), a["params"]["number"])
                    googler.search()
                    c = googler.genQuestion()
                    last_answer = int(c.best[0])
                    msg = ""
                    msg += "Question " + str(c.id) + ": " + c.question
                    msg += "\n==============================\n\n"
                    for i in range(4):
                        print(("[~]" if i + 1 == last_answer else "[ ]"), "Answer " + str(i + 1) + ":",
                              str(c.answers[i]))
                    print("\n==============================")
                elif a["method"] == "round_result":
                    b = a["params"]
                    c = a["params"]["answers"]
                    print("Answer for question %s: %s" % (b["number"], b["text"]))
                    print("==============================\n")
                    correct = -1
                    for q in c:
                        d = False
                        if q["correct"]:
                            d = True
                            correct = q["number"]
                        print(("[x]" if d else "[ ]"), "Answer %s: %s" % (q["number"], q["text"]))
                    print("\n==============================")
                    if last_answer == correct:
                        corrects += 1
                    print("Bot status:", ("" if last_answer == correct else "in") + "correct,",
                          "%s/%s" % (str(corrects), b["number"]))

            elif msg.name == "disconnected":
                print("disconnected")


def main():
    print("What bot would you like to start?")
    print("1. VK Clever")
    print("2. VVP")
    a = input("[1-2] > ")
    while isInt(a) not in range(3):
        a = input("[1-2] > ")
    if a == '1':
        clever = CleverBot()
        clever.parseArgs(sys.argv)
        clever.mainloop()
    elif a == '2' and WS_INSTALLED:
        VVP = VVPBot()
        VVP.mainloop()


if __name__ == '__main__':
    main()
