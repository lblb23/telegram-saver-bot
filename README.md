# Saver Telegram bot
Telegram bot for saving Youtube and Instagram content to mobile gallery. This bot sends you a video or photo and you can save it to the gallery on the phone.

## Getting Started

1. Create own telegram bot. Manual: https://core.telegram.org/bots
2. Insert your bot token to config.yml.
3. Register on https://chatbase.com/ for storing bot usage statistics and insert chatbase token
4. Install requirements.
5. Run main.py.
```
python3 main.py
```
If you want to run this bot on the server, you can run:
```
nohup python3 main.py & tail -f nohup.out
```
## Hosting this bot on pythonanywhere.com

1. Sign up on [pythonanywhere.com](https://www.pythonanywhere.com/).
2. Upload files to server.
```
git clone https://github.com/lbulygin/telegram-saver-bot
```
3. Add always-on task:
```
python3 /home/{YOUR_USERNAME}/telegram-saver-bot/main.py
```
4. Add daily scheduled task for purging cache folder:
```
rm -rf /home/{YOUR_USERNAME}/telegram-saver-bot/files/*
```

5. Add daily scheduled task for purging messages limits:
```
rm -rf /home/{YOUR_USERNAME}/telegram-saver-bot/db_users_limits.json
```


## Database of users and mailing

This bot saves usernames and their chat_id to *db_users.json* for sending messages.

Users have messages limits in config.yml (messages_limit parameter). Limits are stored in  *db_users_limits.json*.

You can send a message to all your users with this command:
```
python3 mailing_users.py --message "YOUR MESSAGE"
```

## Instagram Authorization 

If you are not authorized, then over time Instagram will redirect you to the page with authorization, so the bot will be unstable.

How auth:
1. Generate *cookies.sqllite* with Firefox. Manual: https://instaloader.github.io/troubleshooting.html
2. Copy *cookies.sqllite* to repo
3. Run
```
python3 generate_cookies.py
```
4. In *config.yml* change authorization to True and insert your login.

## Main requirements

* [instaloader](https://github.com/instaloader/instaloader)
* [pytube3](https://github.com/get-pytube/pytube3)
* [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
