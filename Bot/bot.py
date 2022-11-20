from datetime import datetime
import pytz


class Bot:
    _position = {}

    def __init__(self, user_config: dict, cci_config: dict, ema_config: dict):
        self.USER_CONFIG = user_config
        self.CCI_CONFIG = cci_config
        self.EMA_CONFIG = ema_config

        # Helper methods

    @staticmethod
    def _tick_on_timeframe(timeframe: str = '1m'):
        cT = datetime.now(pytz.timezone('UTC'))
        if timeframe[-1] == 'm':
            return (cT.second == 0) and (cT.minute % int(timeframe[:-1])) == 0

    def run_bot(self):
        print("Bot Started!!")
