import sys
import threading

from PyQt5 import QtWidgets, QtCore
import design
from datetime import datetime, timezone
import json
import logging
import sys
import time
import urllib.request, urllib.parse
import requests
from klever_utils import *
try:
    from selenium import webdriver, common
except ImportError:
    pass
import platform

if platform.system() in ("Linux", "Darwin"):
    import subprocess

    res = subprocess.run(["xdpyinfo"], stdout=subprocess.PIPE).stdout.decode('utf-8').split("dimensions:    ")[1].split(
        " pixels")[0].split('x')
elif platform.system() == "Windows":
    print("Untested OS, be careful!")
    from win32api import GetSystemMetrics

    res = (GetSystemMetrics(0), GetSystemMetrics(1))
else:
    print("Unsupported OS, exiting", file=sys.stderr)
    exit(1)

logging.basicConfig(format='[%(levelname)s] %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

class App(QtWidgets.QMainWindow, design.Ui_AKlever):
    GAME_STATE_PLANNED = "Planned"
    GAME_STATE_STARTED = "Started"
    GAME_STATE_FINISHED = "Finished"

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.token = ""
        self.game_start = 0
        self.prize = 0
        self.balance = 0
        self.lives = 0
        self.rating = 0
        self.state = 0
        self.current_answer = ""
        self.buf = ""
        self.t = KleverThread(self)
        self.updateButton.clicked.connect(self.getStartData)
        self.startBtn.clicked.connect(self.startGame)
        self.progressBar.hide()
        self.stopBtn.clicked.connect(self.threadEnd)
        self.t.showQuestion.connect(self.displayQuestion)
        self.runCustomButton.clicked.connect(self.runCustom)

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
        except Exception:
            print("malformed input, cancelling")

    def getToken(self):
        try:
            open("token.ak", "r").close()
            logger.debug("token file found")
        except FileNotFoundError:
            open("token.ak", "a").close()
            logger.debug("token file created")
        f = open("token.ak", "r")
        token = f.read()
        if token:
            logger.debug("token found in file: " + token)
        else:
            logger.debug("token not found, requesting..")
            try:
                browser = webdriver.Firefox()
            except common.exceptions.WebDriverException:
                print(
                    "Oops, it seems geckodriver is not installed.. https://github.com/mozilla/geckodriver/releases. \nOr get token by yourself and put it to token.ak file: https://oauth.vk.com/authorize?client_id=6334949w&display=page&scope=friends&response_type=token&v=5.73",
                    file=sys.stderr)
                exit(1)
            browser.get(
                "https://oauth.vk.com/authorize?client_id=6334949w&display=page&scope=friends&response_type=token&v=5.73")
            browser.set_window_size(600, 700)
            browser.set_window_position(int(res[0]) / 2 - 300, int(res[1]) / 2 - 350)
            while "#access_token" not in browser.current_url: pass
            logger.debug("logged in, got access token")
            token = browser.current_url.split("#access_token=")[1].split('&')[0]
            browser.close()
            f.close()
            f = open("token.ak", "w")
            f.write(token)
        f.close()
        self.token = token

    def validateToken(self):
        out = json.loads(
            urllib.request.urlopen("https://api.vk.com/method/users.get?v=5.73&access_token=" + self.token).read())
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
        self.startData.clear()
        self.startData.addItem("======={ YOUR STATS }=======")
        self.startData.addItem("BALANCE (RUB):  " + str(self.balance))
        self.startData.addItem("EXTRA LIVES:  " + str(self.lives))
        self.startData.addItem("RATING (%):  " + str(self.rating))
        self.startData.addItem("======={ GAME  INFO }=======")
        self.startData.addItem(
            "NEXT GAME:   " + datetime.utcfromtimestamp(self.game_start).replace(tzinfo=timezone.utc).astimezone(
                tz=None).strftime("%H:%M"))
        self.startData.addItem("PRIZE:  " + str(self.prize))
        self.startData.addItem("STATE:  " + str(self.state))
        # END BASE DATA DISPLAY #
        if self.state == self.GAME_STATE_STARTED:
            self.startBtn.setEnabled(True)

    def startGame(self):
        self.t = KleverThread(self)
        self.t.start()
        self.startBtn.setEnabled(False)
        self.stopBtn.setEnabled(True)

    def threadEnd(self):
        self.t.terminate()
        self.stopBtn.setEnabled(False)
        self.startBtn.setEnabled(True)
        logger.debug('stopped thread')

    #@QtCore.pyqtSlot(KleverQuestion, name="displayQuestion")
    def displayQuestion(self, question: KleverQuestion):
        logger.debug('displaying', question.question)
        self.question.setPlainText(question.question)
        self.answer1.setText(question.answer1.text)
        self.answer2.setText(question.answer2.text)
        self.answer3.setText(question.answer3.text)
        self.probab1.setText(str(question.answer1.probability) + "%")
        self.probab2.setText(str(question.answer2.probability) + "%")
        self.probab3.setText(str(question.answer3.probability) + "%")
        self.answer1.setEnabled(True)
        self.answer2.setEnabled(True)
        self.answer3.setEnabled(True)
        print("Question:", question.question)
        print("Answer 1:", question.answer1.text)
        print("Answer 2:", question.answer2.text)
        print("Answer 3:", question.answer3.text)
        # self.progressBar.setMaximum(10)
        # i = 0
        # while i < 10:
        #     self.progressBar.setValue(question.sent_time + 10 - round(time.time()))
        #     i += 1
        #     time.sleep(1)


class KleverThread(QtCore.QThread):
    showQuestion = QtCore.pyqtSignal(object)

    def __init__(self, parent):
        super(KleverThread, self).__init__(parent)
        self.token = parent.token

    def run(self):
        while True: # https://api.vk.com/method/execute.getLastQuestion
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
                time.sleep(0.01)
                self.showQuestion.emit(question)
                print("Question:", question.question)
                print("Answer 1:", question.answer1.text)
                print("Answer 2:", question.answer2.text)
                print("Answer 3:", question.answer3.text)
                time.sleep(10)
            else:
                logger.debug("No question, waiting..")
                time.sleep(1)


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = App()
    window.getToken()
    window.validateToken()
    window.getStartData()
    window.setFixedSize(854, 306)
    window.show()
    app.exec_()



if __name__ == '__main__':
    main()