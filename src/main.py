from currybot import CurryBot
import json
import os

CURRENCY_API_KEY = ""
DISCORD_API_KEY = ""

import traceback

def main():
    try:
        if os.path.exists("config.json"): # Configuration file available
            with open("config.json") as f:
                config = json.load(f)
                CURRENCY_API_KEY = config["CURRENCY_API_KEY"]
                DISCORD_API_KEY = config["DISCORD_API_KEY"]
            pass

            bot = CurryBot(CURRENCY_API_KEY)
            bot.run(DISCORD_API_KEY)

        else: # The configuration is required; Throw error
            raise FileExistsError("Couldn't find config file")

    except Exception as e:
        # TODO(ama): Proper error handling
        print(traceback.print_exc())
        pass

if __name__ == '__main__':
    main()