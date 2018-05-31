#!/usr/bin/python3
import os
from datetime import datetime, timezone
import json
import logging
import sys
import time
import urllib.request, urllib.parse
import requests
import requests.exceptions
from klever_utils import *
import webbrowser
import configparser


def isInt(str):
    try:
        return int(str)
    except:
        return "no"


class App(object):
    GAME_STATE_PLANNED = "Planned"
    GAME_STATE_STARTED = "Started"
    GAME_STATE_FINISHED = "Finished"
    ACTIONS = ("?", "h", "run", "start", "auth", "custom", "exit", "e", "settings", "config", "q", "c", "vidinfo", "r")
    APP_NAME = "AKlever"  # if you want you can change name of bot here - it will change everywhere
    with open("version") as file:
        VERSION = file.read().split("|")

    logging.basicConfig(format='[%(levelname)s] %(message)s')
    logger = logging.getLogger()

    def __init__(self):
        super().__init__()
        self.token = ""
        self.config = configparser.ConfigParser()
        self.initConfig()
        self.logfile = ""
        self.vid = ""
        self.longPollServer = ""
        if self.config["Config"]["debug_mode"] == "verbose":
            self.logger.setLevel(logging.DEBUG)
        elif self.config["Config"]["debug_mode"] == "basic":
            self.logger.setLevel(logging.INFO)
        elif self.config["Config"]["debug_mode"] not in ("verbose", "disabled", "basic"):
            self.config["Config"]["debug_mode"] = "disabled"
        if self.config["Config"]["updates"] not in ("off", "on"):
            self.config["Config"]["updates"] = "off"
        if self.config["Config"]["answer_ui"] not in ("off", "on"):
            self.config["Config"]["answer_ui"] = "off"
        if self.config["Config"]["updates"] == "on":
            self.checkUpdates()
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
        self.proxies = {"http": "socks5h://" + self.config["Social"]["telegram_proxy"], "https": "socks5h://" + self.config["Social"]["telegram_proxy"]} if self.config["Social"]["telegram_proxy"] else {}

    def checkUpdates(self):
        print("Checking for updates...", end="\r")
        try:
            v = requests.get("https://raw.githubusercontent.com/TaizoGem/AKlever/master/version").text.split("|")
            float(v[0])
        except:
            print("Unable to check for updates. Current version:", self.VERSION[0])
            return
        if float(v[0]) > float(self.VERSION[0]):
            print("New version is available, would you like to auto-update?")
            if input("[Y/n] ") not in ("n", "N", "П", "п"):
                os.system("git pull")
                sys.exit()

    def runCustom(self, q=""):
        if q == "":
            print("Input question in this format:")
            print("questionText:answer1#answer2#answer3")
            q = input("> ")
        try:
            q = q.split(":")
            e = q[1].split("#")
            google = KleverGoogler(q[0], e[0], e[1], e[2], 0, 0, self.config["Config"]["debug_mode"])
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
            print("Configurating "+self.APP_NAME+". Choose option to edit from list below:")
            print("1. Debug mode:", self.config["Config"]["debug_mode"])
            print("2. VK auth token")
            print("3. Updates check:", self.config["Config"]["updates"])
            print("4. Telegram integration")
            print("5. Answer UI:", self.config["Config"]["answer_ui"])
            print("6. Communication method:", self.config["Config"]["api_type"])
            print("0. Save and exit", "[EDITED]" if edited else "")
            a = input("[0-6] > ")
            while isInt(a) not in range(7):
                print("Invalid option")
                a = input("[0-6] > ")
            a = int(a)
            if a == 0:
                self.saveConfig()
                self.__init__()
                return
            elif a == 1:
                while True:
                    print("1.", "[x]" if self.config["Config"]["debug_mode"] == "disabled" else "[ ]", "Disabled - only log critical exceptions")
                    print("2.", "[x]" if self.config["Config"]["debug_mode"] == "basic" else "[ ]", "Basic - log some information")
                    print("3.", "[x]" if self.config["Config"]["debug_mode"] == "verbose" else "[ ]", "Verbose - log basically everything")
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
                    print("Since 0.90 "+self.APP_NAME+" supports Telegram integration")
                    print("You can change:")
                    print("1. Enable:", self.config["Social"]["telegram"])
                    print("2. Bot token:", self.config["Social"]["telegram_token"][:7] + "******" + self.config["Social"]["telegram_token"][38:])
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
                            print("For "+self.APP_NAME+" to work correctly, we need to know to which channel to post")
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
                                self.config["Social"]["telegram_proxy"] = input("Enter you proxy in this format: [login[:password]@]server.tld[:port]\n > ")
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
            elif a == 6:
                while True:
                    print("1. More info")
                    print("2.", "[x]" if self.config["Config"]["api_type"] == "longpoll" else "[ ]", "Longpoll")
                    print("3.", "[x]" if self.config["Config"]["api_type"] == "requests" else "[ ]", "Requests")
                    print("0. Back")
                    c = input("[0-3] > ")
                    while isInt(c) not in range(4):
                        print("Invalid option")
                        c = input("[0-3] > ")
                    c = int(c)
                    if c == 0:
                        break
                    elif c == 1:
                        webbrowser.open("https://github.com/TaizoGem/AKlever/wiki/Communication-types")
                        continue
                    elif c == 2:
                        self.config["Config"]["api_type"] = "longpoll"
                    elif c == 3:
                        self.config["Social"]["api_type"] = "requests"
                    edited = True


    def getTokenInfo(self):
        a = json.loads(requests.get("https://api.vk.com/method/users.get?v=5.73&access_token=" + self.token).text)["response"][0]
        return str(a["id"]) + " > " + a["first_name"] + " " + a["last_name"]

    def initConfig(self):
        if os.path.exists("config.ak"):
            self.logger.debug("config exists")
            self.config.read("config.ak")
            return
        self.logger.debug("creating config")
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
        print("Getting token...", end="\r")
        if self.token and not force:
            return
        try:
            token = self.config["Config"]["token"]
        except KeyError:
            token = ""
        if token and self.validateToken(token) and not force:
            self.logger.debug("valid token found in file: " + token)
        else:
            self.logger.debug("token not found or is invalid, requesting..")
            print("Hi! You are 1 step behind using this bot! Since VK Clever sends questions via VK API, we need access"
                  "\ntoken to be able to get them. It is important to use token with Clever appid.\n"
                  "To get token you just need to click enter, authenticate app in browser (if not already)\n"
                  "and paste url or token here\n -> If you already have a token, just press E before enter" if not force
                  else "E if you already have token")
            while True:
                if input("[PRESS ENTER NO OPEN AUTH PAGE]") not in ("e", "E", "У", "у"):
                    try:
                        webbrowser.open("https://oauth.vk.com/authorize?client_id=6334949&display=page&scope=friends,offline,video&response_type=token&v=5.73")
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
            self.logger.debug("token is valid")
            return True
        except KeyError:
            self.logger.debug("token is invalid")
            return False

    def getStartData(self):
        print("Getting data...", end="\r")
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
            self.vid = str(response["game_info"]["game"]["video_owner_id"]) + "_" + str(response["game_info"]["game"]["video_id"])
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
        print("STATE:  \t\t" + str(self.state))
        # END BASE DATA DISPLAY #

    def showCliHelp(self):
        self.showHelp()
        print("\n"+self.APP_NAME+" can also work in CLI mode! You can see list of available params in list below:",
        "--only=<run|config> - only runs command passed instead of text interface",
        "-h, --help          - shows this help and quits",
        "--token=<token>     - overwrites token for this session (does NOT change token in config file)",
        "--custom=<string>   - processes passed question in syntax q:a1#a2#a2, displays output and quits", sep="\n")

    def parseArgs(self, argv: list):
        for arg in argv:
            if arg in ("--help", "-h"):
                self.showCliHelp()
                sys.exit()
            elif "--logfile" in arg:
                if not "=" in arg or len(arg.split("=")[1]) == 0:
                    logging.basicConfig(filename="log.ak", filemode="a", format='[%(levelname)s] %(message)s')
                    self.logger = logging.getLogger()
                else:
                    logging.basicConfig(filename=arg.split("=")[1], filemode="a", format='[%(levelname)s] %(message)s')
                    self.logger = logging.getLogger()
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
        while True:
            try:
                # example question https://gist.githubusercontent.com/TaizoGem/1aea44b8e5fa05550f50617673809ccb/raw/a93b1b060a595142c8ed13111a5e56f4e1afe6ee/aklever.test.json
                    # base server https://api.vk.com/method/execute.getLastQuestion
                response = json.loads(requests.post("https://api.vk.com/method/execute.getLastQuestion", data={"access_token": self.token, "v": "5.73", "https": 1}).text)["response"]
                if response:
                    print("Received question, thinking...", end="\r")
                    self.logger.debug("got question: " + response["text"])
                    google = KleverGoogler(response["text"], response["answers"][0]['text'], response["answers"][1]['text'],
                                            response["answers"][2]['text'], response["sent_time"], response["number"])
                    try:
                        google.search()
                    except ConnectionResetError as e:
                        print("Exception occurred: errno", e.errno, file=sys.stderr)
                        continue
                    question = google.genQuestion()
                    self.displayQuestion(question, google)
                else:
                    self.logger.debug("No question, waiting..")
                    time.sleep(1)
            except (KeyboardInterrupt, SystemExit):
                self.logger.debug("stopping")
                return
            except requests.exceptions.ConnectionError:
                pass

    def showHelp(self):
        print("This is "+self.APP_NAME+", bot for VK Clever, quiz with money prizes by VK Team\n"
              "Coded by TaizoGem, source is available at:\ngithub.com/TaizoGem/AKlever\n"
              "Current version:", self.VERSION[0], "from", self.VERSION[1],
              "\n\nAvailable commands:\n"
              "?, h        - display this menu\n"
              "run, start  - start working\n"
              "auth        - re-auth in application\n"
              "custom, c   - process a custom question\n"
              "e, exit     - exit from application\n"
              "vidinfo     - information about current video\n"
              "cfg, config - configure application")

    def displayQuestion(self, question: KleverQuestion, googler: KleverGoogler, is_custom: bool=False):
        print("Question " + str(question.id) + ":", question.question)
        print("==============================\n")
        for i in range(3):
            print(("[~]" if i == int(question.best[0])-1 else "[ ]"), "Answer "+str(i+1)+":", str(question.answers[i]))
        print("\n==============================")
        if self.config["Config"]["debug_mode"] in ("basic", "verbose"):
            print("Query for custom question:\n" + str(question))
            print("Optimized question:", question.optimized)
        if self.config["Social"]["telegram_auto"] == "yes":
            message = "Question " + str(question.id) + ": "+  question.question
            message += "==============================\n"
            for i in range(3):
                if i == int(question.best[0])-1:
                    message += "\n`[~]`" + "Answer "+str(i+1)+": " + str(question.answers[i])
                else:
                    message += "\n`[ ]`" + "Answer "+str(i+1)+": " + str(question.answers[i])
            message += "\n\n==============================\n"
            tg = requests.get("https://api.telegram.org/bot"+self.config["Social"]["telegram_token"]+"/sendMessage?chat_id="+self.config["Social"]["telegram_channel"]+"&text="+message+"&parse_mode=markdown", proxies=self.proxies)
        if self.config["Config"]["answer_ui"] == "yes":
            while True:
                print("0. Continue")
                print("1. Re-google")
                num = (0, 1)
                if not googler.ran_reverse:
                    num += (2,)
                    print("2. force do reverse search")
                if self.tg_client and not self.config["Social"]["telegram_auto"] == "yes":
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
                    self.tg_client.send_question(question)
        elif not is_custom:
            time.sleep(10)

    def mainloop(self):
        while True:
            try:
                action = input("[? for help] "+self.APP_NAME+" > ").lower()
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


def main():
    window = App()
    window.parseArgs(sys.argv)
    window.getToken()
    window.getStartData()
    window.mainloop()


if __name__ == '__main__':
    main()
