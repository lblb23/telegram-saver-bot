# Saver Telegram bot
Telegram bot for saving Youtube and Instagram content to mobile gallery. This bot sends you a video or photo and you can save it to the gallery on the phone.

[Implementation (RU)](https://t.me/telesave_bot)

## Getting Started

1. Create own telegram bot. Manual: https://core.telegram.org/bots
2. Insert your bot token to config.yml.
3. Install requirements.
4. Run main.py.
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
3. Add always-on task:
```
python3 /home/{YOUR_USERNAME}/main.py
```
4. Add daily scheduled task for purging cache folder:
```
rm -rf /home/{YOUR_USERNAME}/files/*
```

## Database of users

This bot saves usernames and their chat_id to *db_users.json* for sending messages.
