# Importing built-in libraries
import os, json, pytz, time
import datetime as dt
from datetime import datetime
from decimal import Decimal
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

_tws_orders = {}
_completed_orders = []
_open_orders = []
order_id = None


class InteractiveBrokerAPI(EWrapper, EClient):

    def __init__(self, credentials: dict):
        EClient.__init__(self, self)

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

    def _get_next_order_id(self):
        """get the current class variable order_id and increment
        it by one.
        """
        # reqIds can be used to update the order_id, if tracking is lost.
        # self.reqIds(-1)
        current_order_id = self.order_id
        self.order_id += 1
        return current_order_id

    def nextValidId(self, orderId: int):
        """
        Method of EWrapper.
        Is called from EWrapper after a successful connection establishment.
        """
        super().nextValidId(orderId)
        self.order_id = orderId
        return self

    def completedOrder(self, contract: Contract, order: Order, orderState):
        self._completed_orders.append(
            {'symbol': contract.symbol, "order_id": order.permId, "status": orderState.status, "price": order.lmtPrice})

    def openOrder(self, orderId: OrderId, contract: Contract, order: Order, orderState):
        self._open_orders.append({'symbol': contract.symbol, "order_id": order.permId, "status": orderState.status})

        if int(orderId) not in self._tws_orders:
            self._tws_orders[int(orderId)] = {}
            self._tws_orders[int(orderId)].update(
                {'symbol': contract.symbol, 'side': order.action, 'type': order.orderType})

        print('openOrder id:', orderId, contract.symbol, contract.secType, '@', contract.exchange, ':', order.action,
              order.orderType, 'quantity:', order.totalQuantity, orderState.status)

    def orderStatus(self, orderId: OrderId, status: str, filled: float, remaining: float, avgFillPrice: float,
                    permId: int, parentId: int, lastFillPrice: float, clientId: int, whyHeld: str, mktCapPrice: float):
        if int(orderId) in self._tws_orders:
            self._tws_orders[int(orderId)].update({'perm_id': permId})

        print(self._tws_orders)
        if status.upper() == 'FILLED':
            print('orderStatus - orderid:', orderId, 'status:', status, 'filled', filled, 'remaining', remaining,
                  'lastFillPrice', lastFillPrice)
            self._tws_orders[int(orderId)]['fill_price'] = lastFillPrice
            if self.app is not None:
                symbol = self._tws_orders[int(orderId)]['symbol']
                side = self._tws_orders[int(orderId)]['side']
                self.app._on_tws_order_filled(orderId, permId, symbol, side, lastFillPrice, filled)

    def get_contract_with_symbol(self, symbol):
        # Creating contract
        c = Contract()
        c.symbol = symbol
        c.secType = "STK"
        c.exchange = "SMART"
        c.currency = "USD"
        return c

    def place_bracket_order(self, symbol: str, side: str, quantity: Decimal, take_profit_limit_price: float,
                            stop_loss_price: float):

        parent_order_id = self._get_next_order_id()
        c = self.get_contract_with_symbol(symbol)

        self.reqContractDetails(parent_order_id, c)

        parent = Order()
        parent.orderId = parent_order_id
        parent.action = side.upper()
        parent.orderType = "MKT"
        parent.totalQuantity = quantity
        parent.transmit = False
        parent.eTradeOnly = False
        parent.firmQuoteOnly = False

        take_profit = Order()
        take_profit.orderId = parent.orderId + 1
        take_profit.action = "SELL" if side == "BUY" else "BUY"
        take_profit.orderType = "LMT"
        take_profit.totalQuantity = quantity
        take_profit.lmtPrice = take_profit_limit_price
        take_profit.parentId = parent_order_id
        take_profit.transmit = False
        take_profit.eTradeOnly = False
        take_profit.firmQuoteOnly = False

        stop_loss = Order()
        stop_loss.orderId = parent.orderId + 2
        stop_loss.action = "SELL" if side == "BUY" else "BUY"
        stop_loss.orderType = "STP"
        stop_loss.auxPrice = stop_loss_price
        stop_loss.totalQuantity = quantity
        stop_loss.parentId = parent_order_id
        stop_loss.transmit = True
        stop_loss.eTradeOnly = False
        stop_loss.firmQuoteOnly = False

        try:
            self.placeOrder(parent_order_id, c, parent)
            self.placeOrder(take_profit.orderId, c, take_profit)
            self.placeOrder(stop_loss.orderId, c, stop_loss)
        except Exception as e:
            print(e)

        return parent_order_id

    def update_order_stop_loss(self, symbol, side, quantity, parent_order_id, stop_loss_price_updated,
                               trail_percentage):

        c = self.get_contract_with_symbol(symbol)

        self.reqContractDetails(parent_order_id, c)

        stop_loss = Order()
        stop_loss.orderId = parent_order_id + 3
        stop_loss.action = "SELL" if side == "BUY" else "BUY"
        stop_loss.orderType = "STP"
        stop_loss.auxPrice = stop_loss_price_updated
        stop_loss.totalQuantity = quantity
        stop_loss.parentId = parent_order_id
        stop_loss.transmit = False
        stop_loss.eTradeOnly = False
        stop_loss.firmQuoteOnly = False

        trailing_stop_loss = Order()
        trailing_stop_loss.orderId = stop_loss.orderId + 1
        trailing_stop_loss.action = stop_loss.action
        trailing_stop_loss.orderType = "TRAIL"
        trailing_stop_loss.totalQuantity = quantity
        trailing_stop_loss.parentId = parent_order_id
        trailing_stop_loss.trailingPercent = trail_percentage
        trailing_stop_loss.adjustedStopPrice = stop_loss_price_updated
        trailing_stop_loss.adjustedStopLimitPrice = stop_loss_price_updated
        trailing_stop_loss.transmit = True
        trailing_stop_loss.eTradeOnly = False
        trailing_stop_loss.firmQuoteOnly = False

        try:
            self.placeOrder(parent_order_id + 3, c, stop_loss)
            self.placeOrder(trailing_stop_loss.orderId, c, trailing_stop_loss)
        except Exception as e:
            print(e)

    def cancel_order(self, order_id: int) -> None:
        """
        Cancel open order\n
        """
        self.cancelOrder(orderId=order_id)


if __name__ == "__main__":
    creds = {
        "account": "IB",
        "host": "127.0.0.1",
        "port": 7497,
        "client_id": 0
    }
    #
    api = InteractiveBrokerAPI(credentials=creds)
    api.connect()

    id = api.place_bracket_order("AAPL", "BUY", 1, 148.2, 148.05)
    api.update_order_stop_loss(symbol="AAPL", side="BUY", quantity=1, parent_order_id=id,
                               stop_loss_price_updated=148.2,
                               trail_percentage=0.9)

    # print("SIII")
    # api.cancel_order(7)
