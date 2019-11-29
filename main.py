# -*- coding: utf-8 -*-
import logging
import os
import time
from shutil import rmtree

import yaml
from telegram import InputMediaPhoto, InputMediaVideo, InlineKeyboardButton, \
    InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, \
    CallbackQueryHandler
from tinydb import TinyDB, Query

from utils import get_insta_links, check_instagram, check_youtube, \
    get_youtube_resolutions, download_yt_video, get_yt_link_by_res

with open('config.yml') as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

TOKEN = config['TOKEN']

update_id = None

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='.log')

logger = logging.getLogger(__name__)

query = Query()

db_users = TinyDB('db_users.json')


def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))

    dp.add_handler(MessageHandler(Filters.text, handle_message))

    dp.add_handler(CallbackQueryHandler(button))

    dp.add_error_handler(error)

    updater.start_polling()

    updater.idle()


def start(update, context):
    update.message.reply_text(
        'Hello! I can download for you a picture or video from Instagram and Youtube. Just send me a link to the post.')


def help(update, context):
    update.message.reply_text(
        'Just send me a link to an Instagram post or Youtube video.')


def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def button(update, context):
    query = update.callback_query

    context.bot.deleteMessage(query.from_user.id, query.message.message_id)

    social_network, video_id, res, size = query.data.split('--')

    if float(size) > 50:
        if social_network == 'yt':
            url = get_yt_link_by_res(video_id, res)
        context.bot.send_message(chat_id=query.from_user.id,
                                 parse_mode='Markdown',
                                 text="Telegram allows to send video only up to 50 mb, so we can only give a direct link: [link](" + url + ")")
    else:
        context.bot.send_message(query.from_user.id,
                                 "Your video is loading ...")

        if 'yt' in social_network:
            flag, path = download_yt_video(video_id, res)

        video_file = open(path, 'rb')
        context.bot.send_video(update.callback_query.from_user.id, video_file,
                               timeout=200)

        rmtree(os.path.join("files", path.split('/')[1]), ignore_errors=True)


def handle_message(update, context):
    result = 0
    reason = ''

    if update.message:

        url = update.message.text

        if check_instagram(url):
            flag, post = get_insta_links(url)

            contents = []

            try:
                for node in post.get_sidecar_nodes():
                    contents.append(node)

                if flag:

                    media_group = []
                    context.bot.send_message(update.message.chat.id,
                                             "Your data is loading ...")

                    if len(contents):
                        for node in contents:
                            if node.is_video:
                                # print(node.video_url)
                                media_group.append(
                                    InputMediaVideo(node.video_url))
                            else:
                                media_group.append(
                                    InputMediaPhoto(node.display_url))
                        context.bot.sendMediaGroup(update.message.chat.id,
                                                   media_group, timeout=200)
                    else:
                        if post.is_video:

                            context.bot.sendMediaGroup(update.message.chat.id, [
                                InputMediaVideo(post.video_url)],
                                                       timeout=200)
                        else:
                            context.bot.sendMediaGroup(update.message.chat.id, [
                                InputMediaPhoto(post.url)], timeout=200)

                    if post.caption:
                        context.bot.send_message(update.message.chat.id,
                                                 post.caption)

                    result = 1
                else:
                    reason = 'Instagram error'
                    context.bot.sendMessage(update.message.chat.id,
                                            "Invalid link. Check if the post is public.")
            except Exception as e:
                print(str(e))
                context.bot.sendMessage(update.message.chat.id,
                                        "Invalid link. Check if the post is public.")

        elif check_youtube(url):
            flag, streams, video_id = get_youtube_resolutions(url)

            if flag:

                keyboard = []

                for stream in streams:
                    text = stream.res.split('.')[0] + ' (' + str(
                        stream.size) + ' MB)'
                    callback_data = "yt" + "--" + video_id + '--' + stream.res + '--' + str(
                        stream.size)
                    keyboard.append([InlineKeyboardButton(text=text,
                                                          callback_data=callback_data)])

                reply_markup = InlineKeyboardMarkup(keyboard)

                context.bot.send_message(update.message.chat.id,
                                         text="Choose resolution",
                                         reply_markup=reply_markup)
                result = 1
            else:
                context.bot.sendMessage(update.message.chat.id,
                                        "Invalid link. Check if the video is public.")
                reason = 'Youtube error'

        else:
            context.bot.sendMessage(update.message.chat.id,
                                    "Invalid link. Check if the post is public.")
            reason = 'Invalid URL'

        print(update.message.from_user.name, update.message.text,
              time.ctime(int(time.time())), result, reason,
              sep='    ', flush=True)

        user_exist = db_users.search(
            query.user == update.message.from_user.name)

        if len(user_exist) == 0:
            db_users.insert({'user': update.message.from_user.name,
                             'chat_id': update.message.chat.id})


if __name__ == '__main__':
    main()
