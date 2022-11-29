import time

import pytz
from threading import Thread
from datetime import datetime

from Bot.entry_condition import EntryCondition
from Brokers.InteractiveBrokers_api import InteractiveBrokerAPI
from Brokers.market_data import MarketData
from Bot.SubThreadForTrailingStopLossIB import TrailingStopLoss


class BotThreadIB(Thread):

    def __init__(self, symbol, user_config: dict, cci_config: dict, ema_config: dict):
        Thread.__init__(self, daemon=False)
        self.symbol = symbol
        self.USER_CONFIG = user_config
        self.CCI_CONFIG = cci_config
        self.EMA_CONFIG = ema_config
        self.order_id = None
        self.API = InteractiveBrokerAPI(self.USER_CONFIG['Interactive_Broker_CREDENTIALS'])
        self.API.connect()

    @staticmethod
    def _tick_on_timeframe(self, timeframe: str = '1m'):
        cT = datetime.now(pytz.timezone(self.USER_CONFIG['TimeZone_Pytz']))
        if timeframe[-1] == 'm':
            return (cT.second == 0) and (cT.minute % int(timeframe[:-1])) == 0

    def run(self) -> None:
        print(f"Khush Khabari!!,Stock:- {self.symbol} Ke liye Bot Ne Kaam Shuru Kar diya Hai!!")
        while True:
            if self._tick_on_timeframe(self, self.USER_CONFIG['Time_Frame_In_Minutes']):
                time.sleep(3)
                # getting the data
                _period = {
                    "1m": "7d",
                    "5m": "60d",
                    "15m": "60d",
                    "30m": "60d",
                    "60m": "730d"
                }
                df = MarketData.get_market_data(symbol=self.symbol,
                                                interval=self.USER_CONFIG['Time_Frame_In_Minutes'],
                                                period=_period[
                                                    self.USER_CONFIG['Time_Frame_In_Minutes']]
                                                )
                last_closing_price = df['Close'].iat[-1]

                print(datetime.now(pytz.timezone('America/New_York')))

                # Checking For Entry Condition

                is_enter, side, last_closing_ema = EntryCondition.check_for_entry(df,
                                                                                  self.USER_CONFIG,
                                                                                  self.EMA_CONFIG,
                                                                                  self.CCI_CONFIG)

                if is_enter:
                    _is_valid_target_profit_stop_loss = False
                    take_profit = (last_closing_price * (
                            1 + (self.USER_CONFIG[
                                     'Target_Profit_%'] / 100)) if side == "BUY" else (
                            last_closing_price * (
                            1 - (self.USER_CONFIG['Target_Profit_%'] / 100))))

                    stop_loss = last_closing_ema * (1 - (self.USER_CONFIG[
                                                             'Init_PO_Stop_Limit_%'] / 100)) if side == "BUY" else last_closing_ema * (
                            1 + (self.USER_CONFIG['Init_PO_Stop_Limit_%'] / 100))

                    if side == "BUY":
                        if take_profit > stop_loss:
                            _is_valid_target_profit_stop_loss = True

                    if side == "SELL":
                        if take_profit < stop_loss:
                            _is_valid_target_profit_stop_loss = True

                    is_in_exception_block = False

                    if _is_valid_target_profit_stop_loss:
                        _signal = {
                            'symbol': self.symbol,
                            'take_profit': take_profit,
                            'stop_loss': stop_loss,
                            'side': side,
                            'qtc': self.USER_CONFIG['Quantity'],
                            'trailing_stop_loss_added': False
                        }

                        try:
                            self.order_id = self.API.place_bracket_order(
                                symbol=self.symbol, side=side,
                                quantity=self.USER_CONFIG['Quantity'],
                                take_profit_limit_price=take_profit,
                                stop_loss_price=stop_loss)
                            _signal['order_id'] = self.order_id
                        except Exception as e:
                            is_in_exception_block = True
                            print(e)

                        if not is_in_exception_block:
                            print(f"signale:- {_signal}")
                            trailing_stop_loss_thread = TrailingStopLoss(symbol=self.symbol,
                                                                         price_where_should_add_trailing_stop_loss=(
                                                                                 last_closing_price * (
                                                                                 1 + (self.USER_CONFIG[
                                                                                          'Price_Up_%'] / 100))),
                                                                         stock_purchased_price=last_closing_price,
                                                                         trailing_stop_percentage=self.USER_CONFIG[
                                                                             'Trailing_Stop_%'], side=side,
                                                                         take_profit=take_profit, stop_loss=stop_loss,
                                                                         quantity=self.USER_CONFIG['Quantity'],
                                                                         parent_order_id=self.order_id, api=self.API)
                            trailing_stop_loss_thread.start()
                            trailing_stop_loss_thread.join()
