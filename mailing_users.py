import argparse
from time import sleep

import telegram
import yaml
from tinydb import TinyDB, Query
from tqdm import tqdm

parser = argparse.ArgumentParser()
parser.add_argument(
    "--message", default="Test message", dest="message", help="Message for mailing"
)

args = parser.parse_args()
message = args.message

query = Query()
db_users = TinyDB("db_users.json")

with open("config.yml") as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

bot = telegram.Bot(token=config["telegram_token"])
pause = config["pause_mailing"]

for chat in tqdm(db_users.all()):
    bot.send_message(chat["chat_id"], message)
    sleep(pause)
