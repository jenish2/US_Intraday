# Author : Jenish Dholariya

import json
import os
from Bot.bot import Bot

with open(os.path.join(os.path.dirname(__file__), "UserInput", 'User_Settings.json')) as f:
    user_config = json.load(f)
    f.close()

with open(os.path.join(os.path.dirname(__file__), "UserInput", 'CCI_Indicator.json')) as f:
    cci_config = json.load(f)
    f.close()

with open(os.path.join(os.path.dirname(__file__), "UserInput", 'EMA_Indicator.json')) as f:
    ema_config = json.load(f)
    f.close()

bot = Bot(user_config, cci_config, ema_config)
bot.run_bot()
