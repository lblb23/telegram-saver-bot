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
parser.add_argument(
    "--config_path", default="config.yml", dest="config_path", help="Path to config"
)

args = parser.parse_args()
message = args.message
config_path = args.config_path

query = Query()
db_users = TinyDB("db_users.json")

with open(config_path) as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

bot = telegram.Bot(token=config["telegram_token"])
pause = config["pause_mailing"]

for chat in tqdm(db_users.all()):
    bot.send_message(chat_id=chat["chat_id"], text=message)
    sleep(pause)
