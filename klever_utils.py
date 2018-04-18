import googler
import urllib.parse
import re


class KleverAnswer():
    def __init__(self, text, coincidences):
        self.text = text
        self.coincidences = coincidences
        self.probability = 0

    def setProbability(self, new):
        self.probability = new


class KleverQuestion(object):
    def __init__(self, question, answer1: KleverAnswer, answer2: KleverAnswer, answer3: KleverAnswer, sent_time: int, kid: int):
        self.question = question
        self.answers = (answer1, answer2, answer3)
        self.sent_time = sent_time
        self.id = kid
        self.reverse = False
        if "НЕ" in question:
            self.reverse = True

    def calculate_probability(self):
        total = 0
        for answer in self.answers:
            total += answer.coincidences # first of all count total, then anything else
        for answer in self.answers:
            if total == 0:
                answer.setProbability(0)
            else:
                answer.setProbability(round(answer.coincidences / total * 100, 1))
        if total == 0:
            self.question += " | NOT FOUND!"

class KleverGoogler():
    def __init__(self, question: str, answer1: str, answer2: str, answer3: str, sent_time: int, kid: int):
        self._question = question
        self._answer1 = answer1
        self._answer2 = answer2
        self._answer3 = answer3
        self.conn = googler.GoogleConnection("google.ru")
        self.sent_time = sent_time
        self.id = kid



    def search(self):
        response = self.conn.fetch_page("https://www.google.ru/search?q=" + urllib.parse.quote_plus(re.sub("[\'@<!«»?]", "", self._question).lower())).lower()
        self.answer1 = KleverAnswer(self._answer1, response.count(self._answer1.lower()))
        self.answer2 = KleverAnswer(self._answer2, response.count(self._answer2.lower()))
        self.answer3 = KleverAnswer(self._answer3, response.count(self._answer3.lower()))

    def genQuestion(self):
        a = KleverQuestion(self._question, self.answer1, self.answer2, self.answer3, self.sent_time, self.id)
        a.calculate_probability()
        return a
