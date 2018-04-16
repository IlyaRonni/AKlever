import googler
import urllib.parse


class KleverAnswer():
    def __init__(self, text, coincidences):
        self.text = text
        self.coincidences = coincidences
        self.probability = 0

    def setProbability(self, new):
        self.probability = new

class KleverQuestion():

    def __init__(self, question, answer1: KleverAnswer, answer2: KleverAnswer, answer3: KleverAnswer, sent_time: int, id: int):
        self.question = question
        self.answer1 = answer1
        self.answer2 = answer2
        self.answer3 = answer3
        self.sent_time = sent_time
        self.id = id

    def calculate_probability(self):
        total = self.answer1.coincidences + self.answer2.coincidences + self.answer2.coincidences
        try:
            self.answer1.setProbability(round(self.answer1.coincidences / total * 100, 1))
            self.answer2.setProbability(round(self.answer2.coincidences / total * 100, 1))
            self.answer3.setProbability(round(self.answer3.coincidences / total * 100, 1))
        except ZeroDivisionError:
            self.answer1.setProbability(0)
            self.answer2.setProbability(0)
            self.answer3.setProbability(0)
            self.question += " | NOT FOUND!"


class KleverGoogler():
    def __init__(self, question: str, answer1: str, answer2: str, answer3: str, sent_time: int, id: int):
        self._question = question
        self._answer1 = answer1
        self._answer2 = answer2
        self._answer3 = answer3
        self.conn = googler.GoogleConnection("google.ru")
        self.sent_time = sent_time
        self.id = id



    def search(self):
        response = self.conn.fetch_page("https://google.ru/search?q=" + urllib.parse.quote_plus(self._question))
        self.answer1 = KleverAnswer(self._answer1, response.count(self._answer1))
        self.answer2 = KleverAnswer(self._answer2, response.count(self._answer2))
        self.answer3 = KleverAnswer(self._answer3, response.count(self._answer3))

    def genQuestion(self):
        a = KleverQuestion(self._question, self.answer1, self.answer2, self.answer3, self.sent_time, self.id)
        a.calculate_probability()
        return a

