import pytz
import logging
from datetime import datetime
from Brokers.TD_Ameritrade_api import TD_Ameritrade_api
from Brokers.InteractiveBrokers_api import InteractiveBrokerAPI
from Bot.entry_condition import EntryCondition
from Brokers.market_data import MarketData


class Bot:
    _position = {}

    def __init__(self, user_config: dict, cci_config: dict, ema_config: dict):
        self.API = None
        self.USER_CONFIG = user_config
        self.CCI_CONFIG = cci_config
        self.EMA_CONFIG = ema_config

    # Helper methods
    @staticmethod
    def _tick_on_timeframe(timeframe: str = '1m'):
        # cT = datetime.now(pytz.timezone('America/New_York'))
        # if timeframe[-1] == 'm':
        #     return (cT.second == 0) and (cT.minute % int(timeframe[:-1])) == 0
        return True

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
                is_market_open, td_ameritrade_api = self._from_current_date_check_market_is_open(
                    self.USER_CONFIG['TD_AMERITRADE_CREDENTIALS'])

                if is_market_open:
                    # creating connection with the broker
                    if self.USER_CONFIG['IS_TD_AMERITRADE_BROKER']:
                        self.API = td_ameritrade_api
                    elif self.USER_CONFIG['IS_Interactive_BROKER']:
                        self.API = InteractiveBrokerAPI(self.USER_CONFIG['Interactive_Broker_CREDENTIALS'])
                    else:
                        logging.error("No Broker is SELECTED Please Select the broker In User_Setting.json file")
                        logging.log("Stopping the bot!!")
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
                                                        period=_period[self.USER_CONFIG['Time_Frame_In_Minutes']]
                                                        )

                        print(datetime.now(pytz.timezone('America/New_York')))

                        # Checking For Entry Condition
                        if stock_symbol not in self._position:
                            is_enter, side = EntryCondition.check_for_entry(df, self.USER_CONFIG, self.EMA_CONFIG,
                                                                            self.CCI_CONFIG)
                            if is_enter:
                                if side == "Buy":
                                    pass
                                if side == "Sell":
                                    pass
                        else:
                            # checking for the Exit Condition
                            pass
