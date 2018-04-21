#!/usr/bin/python3
import os
from datetime import datetime, timezone
import json
import logging
import sys
import time
import urllib.request, urllib.parse
import requests
from klever_utils import *
import platform
import webbrowser
import configparser



class App(object):
    GAME_STATE_PLANNED = "Planned"
    GAME_STATE_STARTED = "Started"
    GAME_STATE_FINISHED = "Finished"
    ACTIONS = ("?", "h", "run", "start", "auth", "custom", "exit", "e", "settings", "config", "q", "c")
    _VERSION = (0.80, "21.04.18")
    logging.basicConfig(format='[%(levelname)s] %(message)s')
    logger = logging.getLogger()
    def __init__(self):
        super().__init__()
        self.token = ""
        self.config = configparser.ConfigParser()
        self.initConfig()
        self.logfile = ""
        if self.config["Config"]["debug_mode"] == "verbose":
            self.logger.setLevel(logging.DEBUG)
        elif self.config["Config"]["debug_mode"] == "basic":
            self.logger.setLevel(logging.INFO)
        elif self.config["Config"]["debug_mode"] not in ("verbose", "disabled", "basic"):
            self.config["Config"]["debug_mode"] = "disabled"
        self.game_start = 0
        self.prize = 0
        self.balance = 0
        self.lives = 0
        self.rating = 0
        self.state = 0
        self.current_answer = ""
        self.buf = ""

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
            self.displayQuestion(g)
        except (KeyError, IndexError):
            print("malformed input, cancelling")

    def saveConfig(self):
        with open("config.ak", "w") as config_file:
            self.config.write(config_file)

    def initConfig(self):
        if os.path.exists("config.ak"):
            self.logger.debug("config exists")
            self.config.read("config.ak")
            return
        self.logger.debug("creating config")
        self.config.add_section("Config")
        self.config["Config"]["debug_mode"] = "disabled"
        self.saveConfig()
        self.config.read("config.ak")

    def getToken(self):
        if self.token:
            return
        try:
            token = self.config["Config"]["token"]
        except KeyError:
            token = ""
        if token and self.validateToken(token):
            self.logger.debug("valid token found in file: " + token)
        else:
            self.logger.debug("token not found or is invalid, requesting..")
            print("Hi! You are 1 step behind using this bot! Since VK Clever sends questions via VK API, we need access"
                  "\ntoken to be able to get them. It is important to use token with Clever appid.\n"
                  "To get token you just need to click enter, authenticate app in browser (if not already)\n"
                  "and paste url or token here\n -> If you already have a token, just press E before enter")
            while True:
                if input("[PRESS ENTER NO OPEN AUTH PAGE]") not in ("e", "E", "У", "у"):
                    try:
                        webbrowser.open("https://oauth.vk.com/authorize?client_id=6334949w&display=page&scope=friends&response_type=token&v=5.73")
                    except Exception:
                        print("failed to open browser, open it by yourself, please:\n"
                              "https://oauth.vk.com/authorize?client_id=6334949w&display=page&scope=friends&response_type=token&v=5.73")
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
        response = json.loads(requests.post("https://api.vk.com/method/execute.getStartData",
                                            data={"build_ver": 3078, "need_leaderboard": 0, "func_v": 2,
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
        a = response["game_info"]["game"]["status"]
        if a == "planned":
            self.state = self.GAME_STATE_PLANNED
        elif a == "started":
            self.state = self.GAME_STATE_STARTED
        elif a == "finished":
            self.state = self.GAME_STATE_FINISHED
        # BASE DATA DISPLAY #
        print("======={ YOUR STATS }=======")
        print("BALANCE (RUB):  " + str(self.balance))
        print("EXTRA LIVES:  \t" + str(self.lives))
        print("RATING (%):  \t" + str(self.rating))
        print("======={ GAME  INFO }=======")
        print("NEXT GAME:     ", datetime.utcfromtimestamp(self.game_start).replace(tzinfo=timezone.utc).astimezone(
                tz=None).strftime("%H:%M") if self.state != self.GAME_STATE_STARTED else "NOW!")
        print("PRIZE:  \t\t" + str(self.prize))
        print("STATE:  \t\t" + str(self.state))
        # END BASE DATA DISPLAY #

    def showCliHelp(self):
        self.showHelp()
        print("""\nAKlever can also work in CLI mode! You can see list of available params in list below:
        --only=<run|config> - only runs command passed instead of text interface
        -h, --help          - shows this help and quits
        --token=<token>     - overwrites token for this session (does NOT change token in config file)
        --custom=<string>   - processes passed question in syntax q:a1#a2#a2, displays output and quits
        """)

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
                        # TODO


    def startGame(self):
        print("To stop press Ctrl-C")
        while True: # https://api.vk.com/method/execute.getLastQuestion
            try:
                response = json.loads(requests.post("https://api.vk.com/method/execute.getLastQuestion", data={"access_token": self.token, "v": "5.73", "https": 1}).text)["response"]
                if response:
                    self.logger.debug("got question: " + response["text"])
                    google = KleverGoogler(response["text"], response["answers"][0]['text'], response["answers"][1]['text'],
                                            response["answers"][2]['text'], response["sent_time"], response["number"])
                    try:
                        google.search()
                    except ConnectionResetError as e:
                        print("Exception occured: errno", e.errno, file=sys.stderr)
                        continue
                    question = google.genQuestion()
                    self.displayQuestion(question)
                    time.sleep(10)
                else:
                    self.logger.debug("No question, waiting..")
                    time.sleep(1)
            except (KeyboardInterrupt, SystemExit):
                self.logger.debug("stopping")
                return

    def showHelp(self):
        print("This is AKlever, bot for VK Clever, quiz with money prizes by VK Team\n"
              "Coded by TaizoGem, source is available at:\ngithub.com/TaizoGem/AKlever\n"
              "Current version:", self._VERSION[0], "from", self._VERSION[1],
              "\n\nAvailable commands:\n"
              "?, h             - display this menu\n"
              "run, start       - start working\n"
              "auth             - re-auth in application\n"
              "custom, c        - process a custom question\n"
              "e, exit          - exit from application\n"
              "settings, config - configure application")

    def displayQuestion(self, question: KleverQuestion):
        print("Question " + str(question.id) + ":", question.question)
        print("==============================\n")
        print("Answer 1:", str(question.answers[0]))
        print("Answer 2:", str(question.answers[1]))
        print("Answer 3:", str(question.answers[2]))
        print("\n==============================")
        if self.config["Config"]["debug_mode"] in ("basic", "verbose"):
            print("Query for custom question:\n" + str(question))
        print()

    def mainloop(self):
        while True:
            try:
                action = input("[? for help] AKlever > ").lower()
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
