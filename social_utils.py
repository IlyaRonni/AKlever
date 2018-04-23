"""

SOCIAL INTEGRATION FOR AKLEVER
BY TAIZOGEM

"""
import json
import logging

import klever_utils
import cli


class TGClient:
    def __init__(self, token, channel_name, proxy="apihot:apihot@proxy.apihot.ru:7777"):
        self.token = token
        self.channel_name = channel_name
        self.proxies = {"http": "socks5h://" + proxy, "https": "socks5h://" + proxy} if proxy else {}
        self.session = klever_utils.requests.Session()

    def validate_token(self, token):
        if "error happened" in self.doRequest("getMe"):
            return False
        return True

    def send_question(self, question: klever_utils.KleverQuestion):
        message = "Вопрос " + str(question.id) + ": " + question.question
        message += "\n==============================\n\nОтвет 1: "
        message += str(question.answers[0])
        message += "\nОтвет 2: " + str(question.answers[1])
        message += "\nОтвет 3: " + str(question.answers[2])
        message += "\n\n==============================\n"+cli.App.APP_NAME+" v" + cli.App.VERSION[0]
        self.doRequest("sendMessage", chat_id='@' + self.channel_name, text=message)

    def doRequest(self, method: str, **args):
        try:
            out = json.loads(self.session.post("https://api.telegram.org/bot"+self.token+"/"+method, data=json.dumps(dict(args)), proxies=self.proxies, headers={'Content-type': 'application/json'}).text)
        except Exception as e:
            logging.getLogger().error("Internal error happened:", e)
            return
        if not out["ok"]:
            logging.getLogger().error("External error happened:", out["description"])
        else:
            logging.getLogger().info("Made request " + method)
            return out["result"]
