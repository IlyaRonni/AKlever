import logging

import requests

import googler
import urllib.parse
import re


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
    def __init__(self, question, answers: list, sent_time: int, kid: int):
        self.question = question
        self.answers = answers
        self.sent_time = sent_time
        self.id = kid
        self.reverse = " НЕ" in question or "НЕ " in question or " НЕ " in question

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


class KleverGoogler():
    FILTERED_WORDS = ("сколько", "как много", "вошли в историю как", "какие", "как называется", "чем является",
                      "что из этого", "какой из( этих|)", "какой из героев", "традиционно", "согласно", " - ",
                      "чем занимается", "чья профессия", "в каком году", "состоялся", "из фильма", "что из этого")
    OPTIMIZE_DICT = {
        "какого животного": "кого",
        "": ""
    }
    logging.basicConfig(format='[%(levelname)s] %(message)s')
    logger = logging.getLogger()

    def __init__(self, question: str, answer1: str, answer2: str, answer3: str, sent_time: int, num: int, debug_level: str = "disabled"):
        self._question = question
        self.__question = self.optimizeString(question)
        self.answers = []
        self._answers = [answer1, answer2, answer3]
        self.conn = googler.GoogleConnection("google.ru")
        self.sent_time = sent_time
        self.number = num
        if debug_level == "disabled":
            self.logger.setLevel(logging.CRITICAL)
        elif debug_level == "basic":
            self.logger.setLevel(logging.INFO)
        elif debug_level == "verbose":
            self.logger.setLevel(logging.DEBUG)

    def fetch(self, query):
        return self.conn.fetch_page("https://www.google.ru/search?q=" + urllib.parse.quote_plus(query)).lower()

    def search(self):
        response = self.fetch(self.__question)
        total = 0
        if " и " in self.__question:
            self.logger.info("found multipart answer")
            for answer in self._answers:
                sumd = 0
                for part in answer.split(" и "):
                    sumd += len(re.findall("(:|-|!|.|,|\?|;|\"|'|`| )" + part.lower() + "(:|-|!|.|,|\?|;|\"|'|`| )", response))
                    self.logger.debug("processed " + part + ", found " + str(sumd) + " occs in total")
                self.answers.append(KleverAnswer(answer, sumd))
                total += sumd
        else:
            self.logger.info("usual question, processing..")
            for answer in self._answers:
                total += response.count(answer.lower())
                self.logger.debug("processed " + answer + ", found " + str(total) + " occs in total")
                self.answers.append(KleverAnswer(answer, len(re.findall("(:|-|!|.|,|\?|;|\"|'|`| )" + answer.lower()
                                                                        + "(:|-|!|.|,|\?|;|\"|'|`| )", response))))
        if total == 0:
            # reverse search
            self.logger.info("not found anything, trying reverse search..")
            self.answers = []
            for answer in self._answers:
                rsp = self.fetch(self.optimizeString(answer))
                sumd = 0
                for word in self.getLemmas(self.__question):
                    sumd += len(re.findall("(:|-|!|.|,|\?|;|\"|'|`| )" + word.lower() + "(:|-|!|.|,|\?|;|\"|'|`| )", rsp))
                    self.logger.debug("processed " + word + ", found " + str(sumd) + " occs in total")
                self.answers.append(KleverAnswer(answer, sumd))

    def genQuestion(self):
        a = KleverQuestion(self._question, self.answers, self.sent_time, self.number)
        a.calculate_probability()
        return a

    def optimizeString(self, base):
        base = base.lower()
        base = re.sub("[\'@<!«»?,.]", "", base)
        base = re.sub("("+"|".join(self.FILTERED_WORDS)+")( |)", "", base)
        pattern = re.compile(r'\b(' + '|'.join(self.OPTIMIZE_DICT.keys()) + r')\b')
        base = pattern.sub(lambda x: self.OPTIMIZE_DICT[x.group()], base)
        return base

    def getLemmas(self, base):
        out = []
        for a in requests.get("http://www.solarix.ru/php/lemma-provider.php?query=" + urllib.parse.quote_plus(base)).text.split(" "):
            a = a.replace("\r\n", "")
            if a:
                out.append(a)
        return out
