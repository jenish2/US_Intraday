# Importing built-in libraries
import os, json, pytz, time
import datetime as dt
from datetime import datetime
from threading import Thread
from copy import deepcopy

# Importing third-party libraries
import pandas as pd  # pip install pandas
from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from ibapi.common import OrderId, ListOfContractDescription, BarData, TickerId, TickAttrib, SetOfFloat, SetOfString, \
    ListOfHistoricalTickBidAsk, ListOfHistoricalTick, ListOfHistoricalTickLast
from ibapi.order import Order
from ibapi.account_summary_tags import AccountSummaryTags
from ibapi.ticktype import TickTypeEnum
from ibapi.contract import Contract, ContractDetails
from ibapi.commission_report import CommissionReport
from ibapi.execution import Execution, ExecutionFilter


class InteractiveBrokerAPI(EWrapper, EClient):
    _sec_type = {
        "stock": "STK",
        "stocks": "STK",
        "option": "OPT",
        "options": "OPT",
        "futureContract": "FUT",
        "futureContractOption": "FOP",
        "futureContractOptions": "FOP",
        "Stocks": "STK",
        "Options": "OPT",
        "FutureContract": "FUT",
        "FutureContractOptions": "FOP",
    }

    def __init__(self, credentials: dict):
        EClient.__init__(self, self)

        self._candle_data = []
        self.CREDS = credentials
        self.TIMEZONE = "US/Eastern"

    # IB override methods
    def error(self, reqId, errorCode, errorString):
        print("ERROR", reqId, errorCode, errorString)
        ...

    def tickPrice(self, reqId, tickType, price, attrib):
        print("Tick price", reqId, TickTypeEnum.to_str(tickType), price)

    def tickSize(self, reqId: TickerId, tickType, size: int):
        print(reqId, TickTypeEnum.to_str(tickType), size)

    def connect(self) -> None:
        """
        Connect the system with Interactive brokers TWS desktop app\n
        """
        super().connect(self.CREDS['host'], self.CREDS['port'], self.CREDS.get('client_id') or 1)
        Thread(target=self.run, daemon=True).start()

        time.sleep(1)

    ## Historical data
    def historicalData(self, reqId: int, bar: BarData):
        _ = {
            "datetime": bar.date,
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "volume": bar.volume
        }
        self._candle_data.append(_)

        # print(bar.date, bar.open, bar.high, bar.low, bar.close,)

    def historicalDataEnd(self, reqId: int, start: str, end: str):
        # print(reqId, start, end)
        ...

    def get_candle_data(self, contract: str, symbol: str, timeframe: str, period: str = '2d', exchange: str = ...,
                        **options) -> pd.DataFrame:
        """
        Get candle data from the api\n
        """

        _tf = {
            's': "sec",
            'm': "min"
        }

        self._candle_data = []

        c = Contract()
        c.symbol = symbol
        c.secType = self._sec_type[contract]
        c.exchange = exchange
        c.currency = "USD"

        _timeframe = timeframe[:-1] + ' ' + _tf[timeframe[-1]] + ('s' if timeframe[:-1] != '1' else '')

        _period = ' '.join([i.upper() for i in period])
        self.reqHistoricalData(9, c, '', _period, _timeframe, 'MIDPOINT', 0, 2, False, [])
        time.sleep(options.get('sleep') or 4)
        df = pd.DataFrame(self._candle_data)
        # print(df)
        df.index = [datetime.fromtimestamp(int(x), tz=pytz.timezone(self.TIMEZONE)) for x in df.datetime]
        self._candle_data = []
        return df[['open', 'high', 'low', 'close', 'volume']]


if __name__ == "__main__":
    creds = {
        "account": "IB",
        "host": "127.0.0.1",
        "port": 7497,
        "client_id": 1
    }

    api = InteractiveBrokerAPI(credentials=creds)
    api.connect()

    # NOTE Get candle data
    contract = "stock"
    symbol = "AAPL"
    timeframe = "5m"
    period = "1d"
    exchange = "SMART"
    df = api.get_candle_data(contract=contract, symbol=symbol, timeframe=timeframe, period=period, exchange=exchange)
    print(df)
