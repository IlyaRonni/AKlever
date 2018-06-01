"""

    AKLEVER FORK FOR VVPSHOW.RU
    DOESNT SUPPORT SETTINGS, SORRY

"""
import json
import os
import sys
import random
import logging
import time

import requests
import urllib.parse
import re


class VVPAnswer():
    def __init__(self, text, coincidences):
        self.text = text
        self.coincidences = coincidences
        self.probability = 0

    def __str__(self):
        return self.text + " | " + str(self.probability) + "%"

    def setProbability(self, new):
        self.probability = new


class VVPQuestion(object):
    def __init__(self, question, answers: list, sent_time: int, kid: int):
        self.question = question
        self.answers = answers
        self.sent_time = sent_time
        self.id = kid
        self.reverse = " не " in question.lower()

    def __str__(self):
        return self.question + ":" + self.answers[0].text + "#" + self.answers[1].text + "#" + self.answers[2].text + "#" + self.answers[3].text

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
            self.best = VVPAnswer("???", 0)
        else:
            a = min(self.answers[a].coincidences for a in range(4)) if self.reverse else \
                max(self.answers[a].coincidences for a in range(4))
            i = 0
            for answer in self.answers:
                i += 1
                if answer.coincidences == a:
                    self.best = str(i) + ". " + answer.text



class VVPGoogler():
    FILTERED_WORDS = ("сколько", "как много", "вошли в историю как", "какие", "как называется", "чем является",
                      "что из этого", "(у |)как(ой|ого|их) из( этих|)", "какой из героев", "традиционно", "согласно",
                      " - ",
                      "чем занимается", "чья профессия", "в (как|эт)ом году", "состоялся", "из фильма", "что из этого",
                      "какой", "является", "в мире", "и к", "термин(ов|ы|)", "относ(и|я)тся", "в какой",
                      "у как(ого|ой|их)", "согласно", "на каком")
    OPTIMIZE_DICT = {
        "один": "1",          ###############################
        "одна": "1",          ###############################
        "одно": "1",          ####        #######        ####
        "два": "2",           ####        #######        ####
        "двое": "2",          ####        #######        ####
        "две": "2",           ####        #######        ####
        "три": "3",           ###############################
        "трое": "3",          ##############   ##############
        "четыре": "4",        ##############   ##############
        "четверо": "4",       ##############   ##############
        "пять": "5",          ###############################
        "пятеро": "5",        ########               ########
        "шесть": "6",         ########               ########
        "шестеро": "6",       ####    ###############   #####
        "семь": "7",          ####    ###############   #####
        "семеро": "7",        ###############################
        "восемь": "8",        ###############################
        "девять": "9",        #####                     #####
        "десять": "10",       #####                     #####
        "одиннадцать": "11",  #############     #############
        "двенадцать": "12",   #############     #############
        "тринадцать": "13",   #############     #############
        "четырнадцать": "14", #############     #############
        "пятнадцать": "15",   #############     #############
        "шестнадцать": "16",  #############     #############
        "семнадцать": "17",   #############     #############
        "восемнадцать": "18", #############     #############
        "девятнадцать": "19", ###############################
        "двадцать": "20",     ###############################
        "тридцать": "30",     ###############################
        "сорок": "40",        ####         #####         ####
        "пятьдесят": "50",    ####  ############  ###########
        "шестьдесят": "60",   ####  ############  ###########
        "семьдесят": "70",    ####  #####  #####  #####  ####
        "восемьдесят": "80",  ####  ###### #####  ###### ####
        "девяносто": "90",    ####  ###### #####  ###### ####
        "сто": "100",         ####         #####         ####
        "двести": "200",      ###############################
        "триста": "300",      ###############################
        "четыреста": "400",   ###############################
        "пятьсот": "500",     ###############################
        "шестьсот": "600",    ###############################
        "семьсот": "700",     ###############################
        "восемьсот": "800",   ######                   ######
        "девятсот": "900",    ######  if you use this  ######
        "тысача": "1000",     ######    please leave   ######
        " тысячи": "000",     ######  copyright notice ######
        " тысяч": "000",      ######                   ######
        "миллион": "1000000", ######   (c) TaizoGem    ######
        " миллиона": "000000",###############################
        " миллионов": "000000"###############################
    }
    logging.basicConfig(format='[%(levelname)s] %(message)s')
    logger = logging.getLogger()

    def __init__(self, question: str, answer1: str, answer2: str, answer3: str, answer4: str, sent_time: int, num: int, debug_level: str = "disabled"):
        self._question = question
        self.__question = self.optimizeString(question)
        self.answers = []
        self._answers = [answer1, answer2, answer3, answer4]
        self.conn = requests.Session()
        self.sent_time = sent_time
        self.number = num
        self.ran_reverse = False
        if debug_level == "disabled":
            self.logger.setLevel(logging.CRITICAL)
        elif debug_level == "basic":
            self.logger.setLevel(logging.INFO)
        elif debug_level == "verbose":
            self.logger.setLevel(logging.DEBUG)

    def fetch(self, query):
        try:
            return self.conn.get("https://www.google.ru/search?q=" + urllib.parse.quote_plus(query)).text.lower() + \
                   self.conn.get("https://www.yandex.ru/search/?text=" + urllib.parse.quote_plus(query)).text.lower()
        except Exception as e:
            self.logger.error("Exception occurred while trying to search:" + str(e))

    def search(self):
        response = self.fetch(self.__question)
        total = 0
        if " и " in self.__question:
            self.logger.info("found multipart question")
            for answer in self._answers:
                sumd = 0
                for part in answer.split(" и "):
                    sumd += len(re.findall("(:|-|!|.|,|\?|;|\"|'|`| )" + part.lower() + "(:|-|!|.|,|\?|;|\"|'|`| )", response))
                    self.logger.debug("processed " + part + ", found " + str(sumd) + " occs in total")
                self.answers.append(VVPAnswer(answer, sumd))
                total += sumd
        else:
            self.logger.info("usual question, processing..")
            for answer in self._answers:
                for part in answer.split(" "):
                    total += response.count(answer.lower())
                    self.logger.debug("processed " + answer + ", found " + str(total) + " occs in total")
                    self.answers.append(VVPAnswer(answer, len(re.findall("(:|-|!|.|,|\?|;|\"|'|`| )" + answer.lower()
                                                                            + "(:|-|!|.|,|\?|;|\"|'|`| )", response))))
        if self.answers[0].coincidences == self.answers[1].coincidences == self.answers[2].coincidences == self.answers[3].coincidences:
            self.doReverse()



    def doReverse(self):
        self.logger.info("doing reverse search..")
        prev_results = (
            self.answers[0].coincidences,
            self.answers[1].coincidences,
            self.answers[2].coincidences,
            self.answers[3].coincidences
        )
        self.answers = []
        i = 0
        for answer in self._answers:
            rsp = self.fetch(self.optimizeString(answer))
            sumd = 0
            for word in self.getLemmas(self.__question):
                sumd += len(re.findall("(:|-|!|.|,|\?|;|\"|'|`| )" + word.lower() + "(:|-|!|.|,|\?|;|\"|'|`| )", rsp))
                self.logger.debug("processed " + word + ", found " + str(sumd) + " occs in total")
            self.answers.append(VVPAnswer(answer, prev_results[i] + sumd))
            i += 1
        self.ran_reverse = True

    def genQuestion(self):
        a = VVPQuestion(self._question, self.answers, self.sent_time, self.number)
        a.calculate_probability()
        return a

    def optimizeString(self, base):
        base = base.lower()
        base = re.sub("[\'@<!«»?,.]", "", base)
        base = re.sub("("+"|".join(self.FILTERED_WORDS)+")( |)", "", base)
        pattern = re.compile(r'\b(' + '|'.join(self.OPTIMIZE_DICT.keys()) + r')\b')
        base = pattern.sub(lambda x: self.OPTIMIZE_DICT[x.group()], base)
        self.logger.info("optimized string:" + base )
        return base

    def getLemmas(self, base):
        out = []
        for a in requests.get("http://www.solarix.ru/php/lemma-provider.php?query=" + urllib.parse.quote_plus(base)).text.split(" "):
            a = a.replace("\r\n", "")
            if a:
                out.append(a)
        return out

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

HEADERS = {
    #"Sec-WebSocket-Key": "lqKmOMJHDmKj/MPMqA==",
    "Sec-WebSocket-Version": "13",
    "Connection": "Upgrade"
}
logger = logging.getLogger("vvp")

def mainloop():
    print("to start press enter and to stop press ctrl+c")
    input("<press enter>")
    srv = random.choice(SERVERS)
    # srv = "ws://echo.websocket.org"
    logger.debug(srv)
    conn = WebSocket(srv)
    for header, value in HEADERS.items():
        conn.add_header(str.encode(header), str.encode(value))
    corrects = 0
    last_answer = None
    for msg in conn.connect():
        if msg.name == "text":
            a = json.loads(msg.text)
            if a["method"] == "round_question":
                b = a["params"]["answers"]
                googler = VVPGoogler(a["params"]["text"],b[0]["text"],b[1]["text"],b[2]["text"],b[3]["text"], int(time.time()), a["params"]["number"])
                googler.search()
                c = googler.genQuestion()
                last_answer = int(c.best[0])
                print("Question " + str(c.id) + ":", c.question)
                print("==============================\n")
                for i in range(4):
                    print(("[~]" if i + 1 == last_answer else "[ ]"), "Answer " + str(i + 1) + ":", str(c.answers[i]))
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
                print("Bot status:", ("" if last_answer == correct else "in") + "correct,", "%s/%s" % (str(corrects), b["number"]))

        elif msg.name == "disconnected":
            print("disconnected")


if __name__ == '__main__':
    mainloop()