import pandas as pd
import talib as ta


class EntryCondition:

    @staticmethod
    def calculate_ema(df: pd.DataFrame, source: str, period: int):
        df['EMA'] = df[source].ewm(span=period, adjust=False).mean()
        return df['EMA'].iat[-1], df['EMA'].iat[-2]

    @staticmethod
    def calculate_cci(df: pd.DataFrame, period: int):
        cci = ta.func.CCI(df['High'], df['Low'], df['Close'], period)
        return cci[-1]

    @staticmethod
    def is_cci_condition_for_buy(cci_value, y_parameter):
        return cci_value > y_parameter

    @staticmethod
    def is_delta_condition_for_buy(last_closing_price, last_previous_closing_price, last_closing_ema,
                                   last_previous_closing_ema, user_config: dict):
        if (last_closing_price > last_closing_ema) and (last_previous_closing_price < last_previous_closing_ema):
            if last_closing_price > (last_closing_ema(1 + user_config['Delta_Range_%'])):
                return True
        return False

    @staticmethod
    def is_cci_condition_for_sell(cci_value, y_parameter):
        return cci_value < y_parameter

    @staticmethod
    def is_delta_condition_for_sell(last_closing_price, last_previous_closing_price, last_closing_ema,
                                    last_previous_closing_ema, user_config: dict):
        if (last_closing_price < last_closing_ema) and (last_previous_closing_price > last_previous_closing_ema):
            if last_closing_price < (last_closing_ema(1 - user_config['Delta_Range_%'])):
                return True
        return False

    @staticmethod
    def check_for_entry(df: pd.DataFrame, user_config, ema_config, cci_config):
        last_closing_price = df['Close'].iat[-1]
        last_previous_closing_price = df['Close'].iat[-2]
        last_closing_ema, last_previous_closing_ema = EntryCondition.calculate_ema(df, ema_config['Source'],
                                                                                   ema_config['EMA_Length'])
        last_closing_cci = EntryCondition.calculate_cci(df, cci_config['CCI_Length'])

        if EntryCondition.is_cci_condition_for_buy(cci_value=last_closing_cci, y_parameter=user_config[
            'Y_Min_Value_For_CCI']) and EntryCondition.is_delta_condition_for_buy(last_closing_price=last_closing_price,
                                                                                  last_previous_closing_price=last_previous_closing_price,
                                                                                  last_closing_ema=last_closing_ema,
                                                                                  last_previous_closing_ema=last_previous_closing_ema,
                                                                                  user_config=user_config):
            return True, 'Buy'

        if EntryCondition.is_cci_condition_for_sell(cci_value=last_closing_cci, y_parameter=user_config[
            'Y_Min_Value_For_CCI']) and EntryCondition.is_delta_condition_for_buy(last_closing_price=last_closing_price,
                                                                                  last_previous_closing_price=last_previous_closing_price,
                                                                                  last_closing_ema=last_closing_ema,
                                                                                  last_previous_closing_ema=last_previous_closing_ema,
                                                                                  user_config=user_config):
            return True, 'Sell'

        return False, ''
