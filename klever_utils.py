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
            total += answer.coincidences # first of all count total, then anything else
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
                      "чем занимается", "чья профессия", "в каком году", "состоялся")

    def __init__(self, question: str, answer1: str, answer2: str, answer3: str, sent_time: int, kid: int):
        self._question = question
        self.__question = self.optimizeString(question)
        self.answers = []
        self._answers = [answer1, answer2, answer3]
        self.conn = googler.GoogleConnection("google.ru")
        self.sent_time = sent_time
        self.id = kid



    def search(self):
        response = self.conn.fetch_page("https://www.google.ru/search?q=" + urllib.parse.quote_plus(self.__question)).lower()
        if "и" in self.__question:
            for answer in self._answers:
                sum = 0
                for part in answer.split(" и "):
                    sum += len(re.findall("(:|-|!|.|,|\?|;|\"|'|`| )" + part.lower() + "(:|-|!|.|,|\?|;|\"|'|`| )", response))
                    # sum += response.count(part.lower())
                self.answers.append(KleverAnswer(answer, sum))
                if sum == 0:
                    pass
                    # TODO реверсивный поиск
        else:
            for answer in self._answers:
                self.answers.append(KleverAnswer(answer, response.count(answer.lower())))

    def genQuestion(self):
        a = KleverQuestion(self._question, self.answers, self.sent_time, self.id)
        a.calculate_probability()
        return a

    def optimizeString(self, base):
        base = base.lower() # TODO замена слов на более понятные поисковику
        base = re.sub("[\'@<!«»?,.]", "", base)
        base = re.sub("("+"|".join(self.FILTERED_WORDS)+")( |)", "", base)
        return base
