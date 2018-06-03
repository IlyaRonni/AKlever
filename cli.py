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

IS_EXE = getattr(sys, 'frozen', False)
APP_NAME = "AKlever"  # if you want you can change name of bot here - it will change everywhere
VERSION = 0.95
logging.basicConfig(format='[%(levelname)s] %(message)s')
logger = logging.getLogger(APP_NAME)
config = configparser.ConfigParser()
def saveConfig():
    with open("config.ak", "w") as config_file:
        config.write(config_file)
if os.path.exists("config.ak"):
    logger.debug("config exists")
    config.read("config.ak")
else:
    logger.debug("creating config")
    config.add_section("Config")
    config.add_section("Social")
    config["Social"]["telegram"] = "off"
    config["Social"]["telegram_token"] = ""
    config["Social"]["telegram_channel"] = ""
    config["Social"]["telegram_proxy"] = ""
    config["Social"]["telegram_auto"] = ""
    config["Config"]["debug_mode"] = "disabled"
    config["Config"]["updates"] = "on"
    config["Config"]["answer_ui"] = "off"
    saveConfig()
config.read("config.ak")
proxies = {"http": "socks5h://" + config["Social"]["telegram_proxy"],"https": "socks5h://" + config["Social"]["telegram_proxy"]} if config["Social"]["telegram_proxy"] else {}
vk_token = ""
try:
    if config["Config"]["lang"] == "russian":
        from strings_ru import *
    else:
        from strings_en import *
except KeyError:
    config["Config"]["lang"] = "english"
    saveConfig()
    from strings_en import *
try:
    from lomond import WebSocket
    WS_INSTALLED = True
except ImportError:
    print(WEBSOCKET_NOT_INSTALLED, file=sys.stderr)
    WS_INSTALLED = False


def send_to_telegram(message):
    try:
        requests.post(
            "https://api.telegram.org/bot" + config["Social"]["telegram_token"] + "/sendMessage",
            json=dict(chat_id="@" + config["Social"]["telegram_channel"],
                      text=message,
                      parse_mode="markdown"), proxies=proxies)
    except requests.exceptions.InvalidSchema:
        print(SOCKS_NOT_INSTALLED_FAIL)


def runCustom(q=""):
    if q == "":
        print(CUSTOM_QUESTION_INFO)
        print(CUSTOM_QUESTION_FORMAT)
        q = input("> ")
    try:
        q = q.split(":")
        e = q[1].split("#")
        google = KleverGoogler(q[0], e, 0, 0)
        google.search()
        g = google.genQuestion()
        CleverBot.displayQuestion(CleverBot(), g, google, True)
    except IndexError as e:
        print(MALFORMED_INPUT)


def isInt(str):
    try:
        return int(str)
    except:
        return "no"


def getTokenInfo(token):
        a = requests.get("https://api.vk.com/method/users.get?v=5.73&access_token=" + token).json()["response"][0]
        try:
            return str(a["id"]) + " > " + a["first_name"] + " " + a["last_name"]
        except KeyError:
            return NO_ACCOUNT


def checkUpdates():
    print(CHECKING_FOR_UPDATES, end="\r")
    try:
        v = requests.get("https://raw.githubusercontent.com/TaizoGem/AKlever/master/version").text
        v = float(v)
    except:
        print(CHECKING_FOR_UPDATES_FAILED % VERSION)
        return
    if v > float(VERSION):
        print(NEW_VERSION_AVAILABLE)
        if input(Yn_PROMPT) not in n_ARRAY:
            if IS_EXE:
                newversion = requests.get(
                    "https://github.com/TaizoGem/AKlever/releases/download/v"+str(v)+"/aklever.exe")
                logger.debug("status code is " + str(newversion.status_code))
                if newversion.status_code == 200:
                    import string
                    oldname = sys.executable.split("\\")[-1]
                    filename = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6)) + ".exe"
                    with open(filename, "wb") as f:
                        f.write(newversion.content)  # \/\/\/\/\/\/\/ waiting 3 seconds before copying
                    os.system(
                        "start \"updating aklever\" cmd /c \"ping 127.0.0.1 -n 3 > nul & move " + filename + " " + oldname + " & start " + oldname + "\"")
                    exit()
                else:
                    print(EXE_NOT_YET_COMPILED)
            else:
                newversion = requests.get(
                    "https://raw.githubusercontent.com/TaizoGem/AKlever/master/cli.py")
                if newversion.status_code == 200:
                    import string
                    filename = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6)) + ".py"
                    with open(filename, "wb") as f:
                        f.write(newversion.content)
                    os.system(
                        "start \"updating aklever\" cmd /c \"ping 127.0.0.1 -n 3 > nul & move " + filename + " " + __file__ + " & python " + __file__ + "\"")
                else:
                    print(UPDATE_FAILED % newversion.status_code)


def validateToken(token=None):
        if not token:
            token = vk_token
        out = requests.get("https://api.vk.com/method/users.get?v=5.73&access_token=" + token).json()
        try:
            out["response"]
            logger.debug("token is valid")
            return True
        except KeyError:
            logger.debug("token is invalid")
            return False


def getToken(force=False):
    global vk_token
    print(GETTING_TOKEN, end="\r")
    if vk_token and not force:
        return
    try:
        token = config["Config"]["token"]
    except KeyError:
        token = ""
    if token and validateToken(token) and not force:
        logger.debug("valid token found in file: " + token)
        vk_token = token
        return
    else:
        logger.debug("token not found or is invalid, requesting..")
        print("Hi! You are 1 step behind using this bot! Since VK Clever sends questions via VK API, we need access"
              "\ntoken to be able to get them. It is important to use token with Clever appid.\n"
              "To get token you just need to click enter, authenticate app in browser (if not already)\n"
              "and paste url or token here\n -> If you already have a token, just press E before enter" if not force
              else "E if you already have token")
        while True:
            if input("[PRESS ENTER TO OPEN AUTH PAGE]") not in ("e", "E", "У", "у"):
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
                if not validateToken(token):
                    print("Invalid token, please try again")
                    continue
                else:
                    break
            elif validateToken(a):
                token = a
                break
            else:
                print("Invalid token, please try again")
                continue
    vk_token = token
    config["Config"]["token"] = token
    saveConfig()


def configurate():
        edited = False
        while True:
            print(CONFIGURATION_INTRO % APP_NAME)
            print("1. %s:" % DEBUG_MODE, config["Config"]["debug_mode"])
            print("2. %s" % VK_AUTH_TOKEN)
            print("3. %s:" % CHECK_FOR_UPDATES, config["Config"]["updates"])
            print("4. %s" % TELEGRAM_INTEGRATION)
            print("5. %s:" % ANSWER_UI, config["Config"]["answer_ui"])
            print("6. %s: %s" % (LANGUAGE, CURRENT_LANG))
            print("0. %s" % SAVE_AND_EXIT, EDITED if edited else "")
            a = input("[0-6] > ")
            while isInt(a) not in range(7):
                a = input("[0-6] > ")
            a = int(a)
            if a == 0:
                saveConfig()
                return
            elif a == 1:
                while True:
                    print("1.", "[x]" if config["Config"]["debug_mode"] == "disabled" else "[ ]",
                          DEBUG_DISABLED)
                    print("2.", "[x]" if config["Config"]["debug_mode"] == "basic" else "[ ]",
                          DEBUG_BASIC)
                    print("3.", "[x]" if config["Config"]["debug_mode"] == "verbose" else "[ ]",
                          DEBUG_VERBOSE)
                    print("\n0.", BACK)
                    b = input("[0-3] > ")
                    while isInt(b) not in range(4):
                        b = input("[0-3] > ")
                    b = int(b)
                    if b == 0:
                        break
                    elif b == 1:
                        config["Config"]["debug_mode"] = "disabled"
                    elif b == 2:
                        config["Config"]["debug_mode"] = "basic"
                    elif b == 3:
                        config["Config"]["debug_mode"] = "verbose"
                    edited = True
            elif a == 2:
                while True:
                    print(VK_AUTH_INFO)
                    print("%s:" % CURRENT_TOKEN, vk_token[:6] + "******" + vk_token[75:])
                    print("%s:" % CURRENT_ACCOUNT, getTokenInfo(vk_token))
                    print("1.", CHANGE_TOKEN)
                    print("0.", BACK)
                    b = input("[0-1] > ")
                    while isInt(b) not in range(2):
                        b = input("[0-1] > ")
                    b = int(b)
                    if b == 0:
                        break
                    elif b == 1:
                        getToken(True)
            elif a == 3:
                while True:
                    print(UPDATES_INFO)
                    print("1.", "[x]" if config["Config"]["updates"] == "on" else "[ ]", ENABLE)
                    print("2.", "[x]" if config["Config"]["updates"] == "off" else "[ ]", DISABLE)
                    print("0.", BACK)
                    b = input("[0-2] > ")
                    while isInt(b) not in range(3):
                        b = input("[0-2] > ")
                    b = int(b)
                    if b == 0:
                        break
                    elif b == 1:
                        config["Config"]["updates"] = "on"
                    elif b == 2:
                        config["Config"]["updates"] = "off"
                    edited = True
            elif a == 4:
                while True:
                    print(TELEGRAM_INTEGRATION_INFO % APP_NAME)
                    print("1. %s:" % ENABLE, config["Social"]["telegram"])
                    print("2. %s:" % TELEGRAM_BOT_TOKEN,
                          config["Social"]["telegram_token"][:7] + "******" + config["Social"][
                                                                                       "telegram_token"][38:])
                    print("3. %s: @" + config["Social"]["telegram_channel"] % TELEGRAM_CHANNEL)
                    print("4. %s: " + config["Social"]["telegram_proxy"] % PROXY)
                    print("5. %s:" % TELEGRAM_AUTO_SEND, config["Social"]["telegram_auto"])
                    print("0.", BACK)
                    b = input("[0-5] > ")
                    while isInt(b) not in range(6):
                        b = input("[0-5] > ")
                    b = int(b)
                    if b == 0:
                        break
                    elif b == 1:
                        while True:
                            print(TELEGRAM_ENABLE_DISABLE)
                            print("1.", "[x]" if config["Social"]["telegram"] == "on" else "[ ]", ENABLE)
                            print("2.", "[x]" if config["Social"]["telegram"] == "off" else "[ ]", DISABLE)
                            print("0.", BACK)
                            c = input("[0-2] > ")
                            while isInt(b) not in range(3):
                                c = input("[0-2] > ")
                            c = int(c)
                            if c == 0:
                                break
                            elif c == 1:
                                config["Social"]["telegram"] = "on"
                            elif c == 2:
                                config["Social"]["telegram"] = "off"
                            edited = True
                    elif b == 2:
                        while True:
                            print(TELEGRAM_BOT_TOKEN_INFO)
                            print("1.", CHANGE_TOKEN)
                            print("0.", BACK)
                            c = input("[0-1] > ")
                            while isInt(c) not in range(2):
                                c = input("[0-1] > ")
                            c = int(c)
                            if c == 0:
                                break
                            elif c == 1:
                                config["Social"]["telegram"] = input(ENTER_YOUR_TOKEN + "\n > ")
                            edited = True
                    elif b == 3:
                        while True:
                            print(TELEGRAM_CHANNEL_INFO % APP_NAME)
                            print("1.", CHANGE_CHANNEL)
                            print("0.", BACK)
                            c = input("[0-1] > ")
                            while isInt(c) not in range(2):
                                c = input("[0-1] > ")
                            c = int(c)
                            if c == 0:
                                break
                            elif c == 1:
                                config["Social"]["telegram_channel"] = input(ENTER_YOUR_CHANNEL + "\n > @")
                            edited = True
                    elif b == 4:
                        while True:
                            print(TELEGRAM_PROXY_INFO)
                            print("1.", SET_PROXY)
                            print("0.", BACK)
                            c = input("[0-1] > ")
                            while isInt(c) not in range(2):
                                c = input("[0-1] > ")
                            c = int(c)
                            if c == 0:
                                break
                            elif c == 1:
                                config["Social"]["telegram_proxy"] = input(
                                    ENTER_YOUR_PROXY + "\n > ")
                            edited = True
                    elif b == 5:
                        while True:
                            print(TELEGRAM_AUTO_SEND_INFO)
                            print("1.", "[x]" if config["Social"]["telegram_auto"] == "on" else "[ ]", ENABLE)
                            print("2.", "[x]" if config["Social"]["telegram_auto"] == "off" else "[ ]", DISABLE)
                            print("0.", BACK)
                            c = input("[0-2] > ")
                            while isInt(c) not in range(3):
                                c = input("[0-2] > ")
                            c = int(c)
                            if c == 0:
                                break
                            elif c == 1:
                                config["Social"]["telegram_auto"] = "on"
                            elif c == 2:
                                config["Social"]["telegram_auto"] = "off"
                            edited = True
            elif a == 5:
                while True:
                    print(ANSWER_UI_INFO)
                    print("1.", "[x]" if config["Social"]["answer_ui"] == "on" else "[ ]", ENABLE)
                    print("2.", "[x]" if config["Social"]["answer_ui"] == "off" else "[ ]", DISABLE)
                    print("0.", BACK)
                    c = input("[0-2] > ")
                    while isInt(c) not in range(3):
                        c = input("[0-2] > ")
                    c = int(c)
                    if c == 0:
                        break
                    elif c == 1:
                        config["Social"]["answer_ui"] = "on"
                    elif c == 2:
                        config["Social"]["answer_ui"] = "off"
                    edited = True
            elif a == 6:
                while True:
                    print(LANGUAGE_INFO % APP_NAME)
                    print("1.", "[x]" if config["Config"]["lang"] == "english" else "[ ]",
                          "English")
                    print("2.", "[x]" if config["Config"]["lang"] == "russian" else "[ ]",
                          "Russian")
                    print("0.", BACK)
                    b = input("[0-2] > ")
                    while isInt(b) not in range(3):
                        b = input("[0-2] > ")
                    if b == '0':
                        break
                    elif b == '1':
                        config["Config"]["lang"] = "english"
                    elif b == '2':
                        config["Config"]["lang"] = "russian"
                    edited = True


class KleverAnswer:
    def __init__(self, text, coincidences):
        self.text = text
        self.coincidences = coincidences
        self.probability = 0

    def __str__(self):
        return self.text + " | " + str(self.probability) + "%"

    def setProbability(self, new):
        self.probability = new


class KleverQuestion:
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


class KleverGoogler:
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
        self.ran_reverse = False

    def fetch(self, query, newquery=""):
        try:
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
            logger.error("  Exception occurred while trying to search:" + str(e))
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

    def doReverse(self, prev_results=[0 for a in range(25)]):
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
        self.logfile = ""
        self.vid = ""
        self.longPollServer = ""
        self.game_start = 0
        self.prize = 0
        self.balance = 0
        self.lives = 0
        self.coins = 0
        self.rating = 0
        self.state = 0
        self.current_answer = ""
        self.buf = ""

    def getStartData(self):
        print(GETTING_DATA, end="\r")
        response = requests.post("https://api.vk.com/method/execute.getStartData",
                                            data={"build_ver": 3078, "need_leaderboard": 0, "func_v": -1,
                                                  "access_token": vk_token, "v": "5.73", "lang": "ru",
                                                  "https": 1}).json()
        try:
            response = response["response"]
        except KeyError:
            print("Error occurred:")
            print(response)
            return
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
            try:
                a = requests.post("https://api.vk.com/method/video.getLongPollServer", data={
                    "video_id": response["game_info"]["game"]["video_id"],
                    "owner_id": response["game_info"]["game"]["video_owner_id"],
                    "access_token": vk_token,
                    "v": 5.73,
                    "lang": "ru",
                    "https": 1
                }).json()
                self.longPollServer = a["response"]["url"]
            except KeyError:
                print("Exception occurred:\n", a)
                self.longPollServer = ""
        elif a == "finished":
            self.state = self.GAME_STATE_FINISHED
        print(YOUR_STATS)
        print(BALANCE + str(self.balance))
        print(EXTRA_LIVES + str(self.lives))
        print(COINS + str(self.coins))
        print(RATING + str(self.rating))
        print(GAME_INFO)
        print(NEXT_GAME, datetime.utcfromtimestamp(self.game_start).replace(tzinfo=timezone.utc).astimezone(
            tz=None).strftime("%H:%M") if self.state != self.GAME_STATE_STARTED else NOW, sep="")
        print(PRIZE + str(self.prize))
        print(STATE + str(self.state))

    def showCliHelp(self):
        self.showHelp()
        print("\n%s can also work in CLI mode! You can see list of available params in list below:" % APP_NAME,
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
                if not validateToken(arg.split("=")[1]):
                    print("Token is invalid!     ")
                    sys.exit()
                self.token = arg.split("=")[1]
            elif "--custom" in arg:
                try:
                    query = arg.split("=")[1]
                    runCustom(query)
                    sys.exit()
                except Exception:
                    runCustom()
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
                        configurate()

    def startGame(self):
        print(TO_STOP_PRESS)
        self.corrects = 0
        while True:
            try:
                # example question https://gist.githubusercontent.com/TaizoGem/1aea44b8e5fa05550f50617673809ccb/raw/a93b1b060a595142c8ed13111a5e56f4e1afe6ee/aklever.test.json
                # base server https://api.vk.com/method/execute.getLastQuestion
                response = json.loads(requests.post("https://api.vk.com/method/execute.getLastQuestion",
                                                    data={"access_token": vk_token, "v": "5.73", "https": 1}).text)["response"]
                if response:
                    print(RECEIVED_QUESTION, end="\r")
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
                                                data={"access_token": vk_token, "v": "5.73", "lang": "ru",
                                                      "https": 1}).json()
                        try:
                            answrsp = answrsp["response"]["question"]
                        except KeyError:
                            print("Exception occurred:\n", answrsp)
                            break
                        try:
                            correct = answrsp["right_answer_id"]
                            self.displayQuestion(question, google, False, correct)
                            if int(question.best[0]) - 1 == correct:
                                self.corrects += 1
                            break
                        except KeyError:
                            time.sleep(2)
                else:
                    logger.debug(NO_QUESTION)
                    time.sleep(1)
            except (KeyboardInterrupt, SystemExit):
                return
            except requests.exceptions.ConnectionError:
                pass

    def showHelp(self):
        print(BOT_INFO % (APP_NAME, VERSION),
              BOT_COMMANDS)

    def displayQuestion(self, question: KleverQuestion, googler: KleverGoogler, is_custom: bool = False, correct=-1):
        message = QUESTION % (str(question.id), question.question)
        message += "\n==============================\n"
        for i in range(len(question.answers)):
            sign = "`[ ]`"
            if i == int(question.best[0]) - 1:
                sign = "`[~]`"
            if i == correct:
                sign = "`[x]`"
            message += "\n" + sign + " "+ANSWER+" " + str(i + 1) + ": " + str(question.answers[i])
        message += "\n\n==============================\n"
        if correct != -1:
            message += BOT_STATUS + (CORRECT if int(question.best[0]) - 1 == correct else INCORRECT) + ", " + \
                str(self.corrects) + "/12"
        print(message)
        if config["Config"]["debug_mode"] in ("basic", "verbose"):
            logger.info("Query for custom question:\n" + str(question))
            logger.info("Optimized question:" + question.optimized)
        if (config["Config"]["answer_ui"] == "on" and config["Social"]["telegram_auto"] == "on"
                or config["Social"]["telegram"] == "on") and not is_custom:
            send_to_telegram(message)
        if config["Config"]["answer_ui"] == "on" or is_custom:
            while True:
                print("0.", ANSWER_UI_CONTINUE)
                print("1.", ANSWER_UI_REGOOGLE)
                num = (0, 1)
                if not googler.ran_reverse:
                    num += (2,)
                    print("2.", ANSWER_UI_FORCE_REVERSE)
                if not config["Social"]["telegram_auto"] == "yes":
                    num += (3,)
                    print("3." + ANSWER_UI_SEND_TELEGRAM + " @" + config["Social"]["telegram_channel"])
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
                    send_to_telegram(message)
        elif not is_custom:
            time.sleep(10)

    def mainloop(self):
        while True:
            try:
                action = input(CLI_PROMPT % APP_NAME).lower()
                if action not in self.ACTIONS:
                    print(INVALID_ACTION)
                    continue
                if action in ("?", "h",):
                    self.showHelp()
                elif action in ("run", "start"):
                    self.startGame()
                elif action in ("e", "exit", "q"):
                    sys.exit()
                elif action in ("custom", "c"):
                    runCustom()
                elif action in ("cfg", "config"):
                    configurate()
                elif action == "vidinfo":
                    if self.state == self.GAME_STATE_STARTED:
                        print(CURRENT_VIDEO)
                        print("https://vk.com/video" + self.vid)
                        print("Longpoll:")
                        print(self.longPollServer)
                    else:
                        print(GAME_IS_NOT_RUNNING_NOW)
                elif action == "r":
                    self.__init__()
                    self.getStartData()

            except (KeyboardInterrupt, EOFError):
                exit()


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
        input("<press enter>")
        print(TO_STOP_PRESS)
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

                    message = QUESTION % (str(c.id), c.question)
                    message += "\n==============================\n"
                    for i in range(4):
                        message += ("[~]" if i + 1 == last_answer else "[ ]") + "Answer " + str(i + 1) + ":" + str(c.answers[i])
                    message += "\n\n==============================\n"
                    print(message)
                    if config["Config"]["debug_mode"] in ("basic", "verbose"):
                        logger.info("Query for custom question:\n" + str(c))
                        logger.info("Optimized question:" + c.optimized)
                    if config["Config"]["answer_ui"] == "on" and config["Social"]["telegram_auto"] == "on" \
                            or config["Social"]["telegram"] == "on":
                        send_to_telegram(message)
                elif a["method"] == "round_result":
                    b = a["params"]
                    c = a["params"]["answers"]
                    message = ANSWER_FOR_QUESTION % (b["number"], b["text"])
                    message += "\n==============================\n"
                    correct = -1
                    for q in c:
                        d = False
                        if q["correct"]:
                            d = True
                            correct = q["number"]
                        message += ("`[x]`" if d else "`[ ]`") + ANSWER + " %s: %s" % (q["number"], q["text"]) + "\n"
                    message += "\n=============================="
                    if last_answer == correct:
                        corrects += 1
                    message += BOT_STATUS + (CORRECT if last_answer == correct else INCORRECT) + ", " + \
                               str(corrects) + "/" + str(b["number"])

            elif msg.name == "disconnected":
                print("disconnected")


def main():
    if config["Config"]["debug_mode"] == "verbose":
        logger.setLevel(logging.DEBUG)
    elif config["Config"]["debug_mode"] == "basic":
        logger.setLevel(logging.INFO)
    elif config["Config"]["debug_mode"] not in ("verbose", "disabled", "basic"):
        config["Config"]["debug_mode"] = "disabled"
    if config["Config"]["updates"] not in ("off", "on"):
        config["Config"]["updates"] = "off"
    if config["Config"]["answer_ui"] not in ("off", "on"):
        config["Config"]["answer_ui"] = "off"
    if config["Config"]["updates"] == "on":
        checkUpdates()
    if config["Social"]["telegram"] not in ("off", "on"):
        config["Social"]["telegram"] = "off"
    if config["Social"]["telegram_auto"] not in ("off", "on"):
        config["Social"]["telegram_auto"] = "off"
    print(BOT_INFO % (APP_NAME, VERSION))
    print()
    try:
        while True:
            print(WHAT_BOT)
            print("1.", CONFIG)
            print("2.", CUSTOM_QUESTION)
            print("3.", VK_CLEVER_NAME)
            print("4.", VVP_NAME)
            print("0.", EXIT)
            a = input("[0-4] > ")
            while isInt(a) not in range(5):
                a = input("[0-4] > ")
            if a == '0':
                exit()
            elif a == '1':
                configurate()
            elif a == '2':
                runCustom()
            elif a == '3':
                getToken()
                clever = CleverBot()
                clever.parseArgs(sys.argv)
                clever.getStartData()
                clever.mainloop()
            elif a == '4' and WS_INSTALLED:
                VVP = VVPBot()
                VVP.mainloop()
    except SystemExit:
        pass


if __name__ == '__main__':
    main()
