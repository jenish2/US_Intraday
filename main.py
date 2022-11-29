# Author : Jenish Dholariya

import json
import os
from Bot.bot import Bot
from Bot.BotThreadInteractiveBroker import BotThreadIB

with open(os.path.join(os.path.dirname(__file__), "UserInput", 'User_Settings.json')) as f:
    user_config = json.load(f)
    f.close()

with open(os.path.join(os.path.dirname(__file__), "UserInput", 'CCI_Indicator.json')) as f:
    cci_config = json.load(f)
    f.close()

with open(os.path.join(os.path.dirname(__file__), "UserInput", 'EMA_Indicator.json')) as f:
    ema_config = json.load(f)
    f.close()

# bot = Bot(user_config, cci_config, ema_config)
# bot.run_bot()

stocks_IB = []
if user_config.get('IS_Interactive_BROKER'):
    for stock in user_config.get('Stock_Name'):
        stocks_IB.append(
            BotThreadIB(symbol=stock, user_config=user_config, cci_config=cci_config, ema_config=ema_config))

for threads in stocks_IB:
    threads.start()
# while True:
#     if user_config.get('IS_Interactive_BROKER'):
#         pass
#
#     if user_config.get('IS_TD_AMERITRADE_BROKER'):
#         pass
