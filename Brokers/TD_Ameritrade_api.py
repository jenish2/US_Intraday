import tda
from tda import auth


class TD_Ameritrade_api:
    def __init__(self, cred: dict):
        self.CRED = cred
        self.TDA_TOKEN_PATH = "tda_access_token.json"

    def connect(self):
        try:
            self.client =True
        except FileNotFoundError:
            print("not")
