import time

import pytz
import logging
import threading
from datetime import datetime
from Brokers.TD_Ameritrade_api import TD_Ameritrade_api
from Brokers.InteractiveBrokers_api import InteractiveBrokerAPI
from Bot.entry_condition import EntryCondition
from Brokers.market_data import MarketData

_position = {}
_all_threads = []


def checking_the_trailing_stop_to_be_add_IB(api, priceWhereShouldAddTrailingStopLoss, stock, stock_purchased_price,
                                            trailing_stop_percentage):
    while True:
        time.sleep(10)
        df = MarketData.get_market_data(symbol=stock,
                                        interval="1m",
                                        period="1d"
                                        )


        try:
            if _position.get(stock)['side'] == "BUY":
                if df['High'].iat[-1] >= _position.get(stock)['take_profit']:
                    del _position[stock]
                    break
                if df['Low'].iat[-1] <= _position.get(stock)['stop_loss']:
                    del _position[stock]
                    break

                if df['High'].iat[-1] > priceWhereShouldAddTrailingStopLoss:
                    api.update_order_stop_loss(symbol=stock, side=_position.get(stock)['side'],
                                               quantity=_position.get(stock)['qtc'],
                                               parent_order_id=_position.get(stock)['side'],
                                               stop_loss_price_updated=stock_purchased_price,
                                               trail_percentage=trailing_stop_percentage)

                    del _position[stock]
                    break

            if _position.get(stock)['side'] == "SELL":
                if df['Low'].iat[-1] <= _position.get(stock)['take_profit']:
                    del _position[stock]
                    break
                if df['High'].iat[-1] >= _position.get(stock)['stop_loss']:
                    del _position[stock]
                    break

                if df['Low'].iat[-1] < priceWhereShouldAddTrailingStopLoss:
                    api.update_order_stop_loss(symbol=stock, side=_position.get(stock)['side'],
                                               quantity=_position.get(stock)['qtc'],
                                               parent_order_id=_position.get(stock)['side'],
                                               stop_loss_price_updated=stock_purchased_price,
                                               trail_percentage=trailing_stop_percentage)

                    del _position[stock]
                    break
        except Exception as e:
            print(e)


class Bot:

    def __init__(self, user_config: dict, cci_config: dict, ema_config: dict):
        self.API = None
        self.USER_CONFIG = user_config
        self.CCI_CONFIG = cci_config
        self.EMA_CONFIG = ema_config

    # Helper methods
    @staticmethod
    def _tick_on_timeframe(timeframe: str = '1m'):
        cT = datetime.now(pytz.timezone('America/New_York'))
        if timeframe[-1] == 'm':
            return (cT.second == 0) and (cT.minute % int(timeframe[:-1])) == 0

    @staticmethod
    def _from_current_date_check_market_is_open(credentials):
        cT = datetime.now(pytz.timezone('America/New_York'))
        td_ameritrade_api = TD_Ameritrade_api(credentials)
        if td_ameritrade_api.is_market_open(str(cT.date().today())):

            starting_time = cT.replace(hour=9, minute=30, second=0, microsecond=0)
            ending_time = cT.replace(hour=16, minute=0, second=0, microsecond=0)

            if starting_time <= cT < ending_time:
                return True, td_ameritrade_api
        return False, td_ameritrade_api

    def run_bot(self):
        print("Bot Started!!")
        while True:
            if self._tick_on_timeframe(self.USER_CONFIG['Time_Frame_In_Minutes']):
                time.sleep(2)
                try:
                    is_market_open, td_ameritrade_api = self._from_current_date_check_market_is_open(
                        self.USER_CONFIG['TD_AMERITRADE_CREDENTIALS'])
                    if is_market_open:
                        try:
                            print("Hi")
                            # creating connection with the broker
                            if self.USER_CONFIG['IS_TD_AMERITRADE_BROKER']:
                                self.API = td_ameritrade_api
                                self.API.connect()
                            elif self.USER_CONFIG['IS_Interactive_BROKER']:
                                self.API = InteractiveBrokerAPI(self.USER_CONFIG['Interactive_Broker_CREDENTIALS'])
                                self.API.connect()
                                print(id(self.API))
                            else:
                                print("Broker Issue")
                                break

                            for stock_symbol in self.USER_CONFIG['Stock_Name']:
                                # getting the data
                                _period = {
                                    "1m": "7d",
                                    "5m": "60d",
                                    "15m": "60d",
                                    "30m": "60d",
                                    "60m": "730d"
                                }
                                df = MarketData.get_market_data(symbol=stock_symbol,
                                                                interval=self.USER_CONFIG['Time_Frame_In_Minutes'],
                                                                period=_period[
                                                                    self.USER_CONFIG['Time_Frame_In_Minutes']]
                                                                )
                                last_closing_price = df['Close'].iat[-1]

                                print(datetime.now(pytz.timezone('America/New_York')))

                                # Checking For Entry Condition
                                if stock_symbol not in _position:
                                    time.sleep(1)
                                    is_enter, side, last_closing_ema = EntryCondition.check_for_entry(df,
                                                                                                      self.USER_CONFIG,
                                                                                                      self.EMA_CONFIG,
                                                                                                      self.CCI_CONFIG)
                                    is_enter = True
                                    side = "BUY"
                                    if is_enter:
                                        if self.USER_CONFIG['IS_Interactive_BROKER']:
                                            _is_valid_target_profit_stop_loss = False
                                            take_profit = (last_closing_price * (
                                                    1 + (self.USER_CONFIG[
                                                             'Target_Profit_%'] / 100)) if side == "BUY" else (
                                                    last_closing_price * (
                                                    1 - (self.USER_CONFIG['Target_Profit_%'] / 100))))

                                            stop_loss = last_closing_ema * (1 - (self.USER_CONFIG[
                                                                                     'Init_PO_Stop_Limit_%'] / 100)) if side == "BUY" else last_closing_ema * (
                                                    1 + (self.USER_CONFIG['Init_PO_Stop_Limit_%'] / 100))
                                            _signal = {
                                                'symbol': stock_symbol,
                                                'take_profit': take_profit,
                                                'stop_loss': stop_loss,
                                                'side': side,
                                                'qtc': self.USER_CONFIG['Quantity'],
                                                'trailing_stop_loss_added': False
                                            }
                                            if side == "BUY":
                                                if take_profit > stop_loss:
                                                    _is_valid_target_profit_stop_loss = True

                                            if side == "SELL":
                                                if take_profit < stop_loss:
                                                    _is_valid_target_profit_stop_loss = True
                                            is_in_exception_block = False

                                            if _is_valid_target_profit_stop_loss:
                                                try:
                                                    order_id = self.API.place_bracket_order(
                                                        symbol=stock_symbol, side=side,
                                                        quantity=self.USER_CONFIG['Quantity'],
                                                        take_profit_limit_price=take_profit,
                                                        stop_loss_price=stop_loss)
                                                    _signal['order_id'] = order_id
                                                except Exception as e:
                                                    is_in_exception_block = True
                                                    print(e)
                                                if not is_in_exception_block:
                                                    _position[stock_symbol] = _signal.copy()
                                                    thread_1 = threading.Thread(
                                                        target=checking_the_trailing_stop_to_be_add_IB,
                                                        args=(
                                                            self.API,
                                                            (last_closing_price * (
                                                                    1 + (self.USER_CONFIG[
                                                                             'Price_Up_%'] / 100))),
                                                            stock_symbol, last_closing_price,
                                                            self.USER_CONFIG[
                                                                'Trailing_Stop_%']))
                                                    _all_threads.append(thread_1)
                                                    thread_1.start()
                                            else:
                                                print(
                                                    f"Target Profit :-{take_profit}    StopLoss :- {stop_loss}  Side:-{side}")
                                                print("TAKE PROFIT AND STOP LOSS IS INVALID")
                                            print(_position)
                        except Exception as e:
                            print(e)
                except Exception as e:
                    print(e)
