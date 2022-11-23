# Importing built-in libraries
import pytz  # pip install pytz
from datetime import datetime

# Importing third-party libraries
import requests
import pandas as pd  # pip install pandas
import undetected_chromedriver as uc  # pip install undetected_chromedriver
import tda  # pip install tda-api
from tda import auth
from tda.utils import Utils
from tda.orders.generic import OrderBuilder
from tda.orders.common import EquityInstruction, OrderStrategyType, OrderType, Session, Duration, StopPriceLinkType, \
    StopPriceLinkBasis


class TD_Ameritrade_api:
    def __init__(self, credential: dict):
        self.TIMEZONE = "US/Eastern"
        self._chrome_driver_version = 102
        self.client = None
        self.CRED = credential
        self.TOKEN_PATH = "tda_access_token.json"

    def connect(self):
        """
        Connect To TD Ameritrade account
        :return:
        """
        try:
            self.client = auth.client_from_token_file(token_path=self.TOKEN_PATH, api_key=self.CRED['api_key'])
        except FileNotFoundError:
            driver = uc.Chrome()
            self.client = auth.client_from_login_flow(driver, self.CRED['api_key'], self.CRED['redirect_url'],
                                                      self.TOKEN_PATH)

    def is_market_open(self, date: str):
        url = f"https://api.tdameritrade.com/v1/marketdata/hours?apikey={self.CRED['api_key']}&markets=EQUITY&date={date}"
        response = requests.get(url).json()
        try:
            is_market_open = response['equity']['equity']['isOpen']
            return is_market_open
        except Exception as e:
            pass

        try:
            is_market_open = response['equity']['EQ']['isOpen']
            return is_market_open
        except Exception as e:
            print(e)
        # return True

    def get_candle_data(self, symbol: str, timeframe: str, period='1d') -> pd.DataFrame:
        """
        Get realtime candlestick data\n
        symbol		: str 	= symbol of the ticker\n
        timeframe	: str 	= timeframe of the candles\n
        """
        url = f"https://api.tdameritrade.com/v1/marketdata/{symbol}/pricehistory"

        _freq = {
            'm': 'minute',
            'd': 'day',
            'w': 'weekly',
            'M': 'monthly'
        }
        _period = {
            '': None,
            'd': 'day',
            'M': 'month',
            'y': 'year',
            'Y': 'year',
            'ytd': 'ytd'
        }
        params = {}
        params.update({'apikey': self.CRED['api_key']})
        params['needExtendedHoursData'] = False
        kwargs = {
            'period': period[:-1],
            'periodType': _period[period[-1]],
            'frequencyType': _freq[timeframe[-1]],
            'frequency': int(timeframe[:-1]),
        }

        for arg in kwargs:
            parameter = {arg: kwargs.get(arg)}
            params.update(parameter)

        response = requests.get(url, params=params).json()
        df = pd.DataFrame(response['candles'])
        df.index = [datetime.fromtimestamp(x / 1000, tz=pytz.timezone(self.TIMEZONE)) for x in df.datetime]
        return df[['open', 'high', 'low', 'close', 'volume']]


if __name__ == "__main__":
    cred = {
        'api_key': 'Q9SPHIMLEOIIGGTE4QISQAG7OFMXMJZY',
        'redirect_url': 'https://localhost',
        'account_id': 'testing123'
    }
    api = TD_Ameritrade_api(cred)
    # print(api.get_candle_data('MSFT', "15m"))
    # print(api.is_market_open('2022-11-21'))
