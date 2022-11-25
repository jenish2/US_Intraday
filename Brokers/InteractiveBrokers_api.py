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
    ID = "VT_API_TWS_IB"
    NAME = "Interactive Brokers TWS API"
    AUTHOR = "Variance Technologies pvt. ltd."
    EXCHANGE = "SMART"
    BROKER = "IB"
    MARKET = "SMART"

    TIMEZONE = "UTC"

    API_THREAD = None
    MAX_WAIT_TIME = 5

    app = None

    orderId = None
    _candle_data = []
    _completed_orders = []
    _contract_detail_info = None
    _expiries_and_strikes = {}
    _open_orders = []
    _tws_orders = {}
    _account = None
    _account_cash_balance = None
    _default_time_in_force = "DAY"
    _commissions = {}
    _executions = {}
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

    def connect_app(self, app) -> None:
        self.app = app

    def get_account_info(self) -> dict:
        """
        Returns account information\n
        """
        a = self.reqAccountSummary(1, "All", AccountSummaryTags.AllTags)
        time.sleep(2)
        return self._account

    def get_account_balance(self) -> float:
        """
        Returns account balance for segment\n
        """
        self.reqAccountSummary(1, "All", AccountSummaryTags.TotalCashValue)
        time.sleep(2)
        return self._account_cash_balance

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

    def place_order(
            self,
            contract: str,
            symbol: str,
            side: str,
            quantity: int,
            order_type: str = "MARKET",
            price: float = ...,
            exchange: str = ...,
            **options,
    ) -> int:
        """
        Places order to account\n
        Params:
            symbol		:	str		=	Ticker symbol
            side		:	str		=	Side to execute. ie. BUY or SELL
            quantity	:	int 	=	No of quantity to trade
            order_type	:	str		=	Entry order type. ie. MARKET or LIMIT or STOP
            price		:	float	= 	Entry limit price if LIMIT order is to be set or STOP price if stop order is to be set

        Returns:
            Permenent order ids of order
        """
        _order_type = {
            "MARKET": "MKT",
            "LIMIT": "LMT",
            "STOP": "STP"
        }

        self._raw_vs_perm_order_id = {}

        # Creating contract
        c = Contract()
        c.symbol = symbol

        c.secType = self._sec_type[contract]
        c.exchange = exchange
        c.currency = "USD"

        # Creating single order
        order_id = self._get_next_order_id()
        order = Order()
        order.orderId = order_id
        order.action = side.upper()
        order.orderType = _order_type[order_type]
        order.totalQuantity = quantity
        order.transmit = True
        order.eTradeOnly = False
        order.firmQuoteOnly = False

        if order_type == 'LIMIT':
            order.lmtPrice = price
            order.tif = self._default_time_in_force

        if order_type == 'STOP':
            order.auxPrice = price
            order.tif = self._default_time_in_force

        self.placeOrder(order_id, c, order)

        time.sleep(options.get('sleep', 5))
        resp = self._tws_orders[order_id]
        resp.update({'temp_id': int(order_id), 'quantity': quantity})
        return resp

    def place_order(self):
        # Create order object
        order = Order()
        order.action = 'BUY'
        order.totalQuantity = 100000
        order.orderType = 'LMT'
        order.lmtPrice = '1.10'
        order.transmit = False

        # Create stop loss order object
        stop_order = Order()
        stop_order.action = 'SELL'
        stop_order.totalQuantity = 100000
        stop_order.orderType = 'STP'
        stop_order.auxPrice = '1.09'
        order.transmit = True


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
    # contract = "stock"
    # symbol = "AAPL"
    # timeframe = "5m"
    # period = "1d"
    # exchange = "SMART"
    # df = api.get_candle_data(contract=contract, symbol=symbol, timeframe=timeframe, period=period, exchange=exchange)
    # print(df)

    contract = "stock"
    symbol = "AAPL"
    timeframe = "5m"
    period = "1d"
    exchange = "SMART"
    api.place_order(contract=contract, symbol=symbol, side='BUY', quantity=1, order_type="MARKET")
