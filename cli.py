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
logging.basicConfig(format='[%(levelname)s] %(message)s')
logger = logging.getLogger()


class App(object):
    GAME_STATE_PLANNED = "Planned"
    GAME_STATE_STARTED = "Started"
    GAME_STATE_FINISHED = "Finished"
    ACTIONS = ("?", "h", "run", "start", "auth", "custom", "exit", "e", "settings", "config", "q")
    _VERSION = (0.78, "18.04.18")

    def __init__(self):
        super().__init__()
        self.token = ""
        self.config = configparser.ConfigParser()
        self.initConfig()
        if self.config["Config"]["debug_mode"] == "true":
            logger.setLevel(logging.DEBUG)
        elif self.config["Config"]["debug_mode"] not in ("true", "false"):
            self.config["Config"]["debug_mode"] = "false"
        self.game_start = 0
        self.prize = 0
        self.balance = 0
        self.lives = 0
        self.rating = 0
        self.state = 0
        self.current_answer = ""
        self.buf = ""

    def runCustom(self):
        print("Input question in this format:")
        print("questionText:answer1#answer2#answer3")
        q = input("> ")
        try:
            q = q.split(":")
            e = q[1].split("#")
            google = KleverGoogler(q[0], e[0], e[1], e[2], 0, 0)
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
            logger.debug("config exists")
            self.config.read("config.ak")
            return
        logger.debug("creating config")
        self.config.add_section("Config")
        self.config["Config"]["debug_mode"] = "false"
        self.saveConfig()
        self.config.read("config.ak")

    def getToken(self):
        try:
            token = self.config["Config"]["token"]
        except KeyError:
            token = ""
        if token:
            logger.debug("token found in file: " + token)
        elif not token or not self.validateToken(token):
            logger.debug("token not found, requesting..")
            auth = False
            print("Hi! You are 1 step behind using this bot! Since VK Clever sends questions via VK API, we need access"
                  "\ntoken to be able to get them. It is important to use token with Clever appid.\n"
                  "To get token you just need to click enter, authenticate app in browser (if not already)\n"
                  "and paste url or token here")
            while True:
                input("[PRESS ENTER TO OPEN AUTH PAGE]")
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
                elif self.validateToken(token):
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

    def startGame(self):
        print("To stop press Ctrl-C")
        while True: # https://api.vk.com/method/execute.getLastQuestion
            try:
                response = json.loads(requests.post("https://api.vk.com/method/execute.getLastQuestion", data={"access_token": self.token, "v": "5.73", "https": 1}).text)["response"]
                if response:
                    logger.debug("got question: " + response["text"])
                    google = KleverGoogler(response["text"], response["answers"][0]['text'], response["answers"][1]['text'],
                                            response["answers"][2]['text'], response["sent_time"], response["id"])
                    try:
                        google.search()
                    except ConnectionResetError as e:
                        print("Exception occured: errno", e.errno, file=sys.stderr)
                        continue
                    question = google.genQuestion()
                    self.displayQuestion(question)
                    time.sleep(10)
                else:
                    logger.debug("No question, waiting..")
                    time.sleep(1)
            except (KeyboardInterrupt, SystemExit):
                logger.debug("stopping")
                return

    def showHelp(self):
        print("This is AKlever, bot for VK Clever, quiz with money prizes by VK Team\n"
              "Coded by TaizoGem, source is available at:\ngithub.com/TaizoGem/AKlever\n"
              "Current version:", self._VERSION[0], "from", self._VERSION[1],
              "\n\nAvailable commands:\n"
              "?, h             - display this menu\n"
              "run, start       - start working\n"
              "auth             - re-auth in application\n"
              "custom           - process a custom question\n"
              "e, exit          - exit from application\n"
              "settings, config - configure application")

    def displayQuestion(self, question: KleverQuestion):
        print("Question:", question.question)
        print("==============================")
        print("\nAnswer 1:", question.answers[0].text, "|", str(question.answers[0].probability) + "%")
        print("Answer 2:", question.answers[1].text, "|", str(question.answers[1].probability) + "%")
        print("Answer 3:", question.answers[2].text, "|", str(question.answers[2].probability) + "%")
        print("\n==============================")
        if self.config["Config"]["debug_mode"] == "true":
            a = question.question[:-13] if "NOT FOUND" in question.question else question.question
            print("Query for custom question:\n" + a + ":" + question.answers[0].text + "#" +
                  question.answers[1].text + "#" + question.answers[2].text)
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
                elif action == "custom":
                    self.runCustom()

            except (KeyboardInterrupt, EOFError):
                if self.config["Config"]["debug_mode"] == "false":
                    print("\nTo exit execute command 'q'")
                else:
                    print("\nFinishing..")
                    sys.exit()


def main():
    window = App()
    window.getToken()
    window.getStartData()
    window.mainloop()


if __name__ == '__main__':
    main()
