# -*- coding: utf-8 -*-
import logging
from telegram import InputMediaPhoto, InputMediaVideo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from utils import get_insta_links, check_instagram, check_facebook, \
    download_fb_video, check_vkontakte, get_vk_resolutions, download_vk_video, \
    check_youtube, get_youtube_resolutions, download_yt_video, get_vk_link_by_res, get_yt_link_by_res
import os
from shutil import rmtree
from tinydb import TinyDB, Query
import time
import yaml

with open('config.yml') as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

TOKEN = config['TOKEN']

update_id = None

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
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
        if social_network == 'vk':
            url = get_vk_link_by_res(video_id, res)
        elif social_network == 'yt':
            url = get_yt_link_by_res(video_id, res)
        context.bot.send_message(chat_id=query.from_user.id, parse_mode='Markdown',
                                 text="Telegram allows to send video only up to 50 mb, so we can only give a direct link: [link](" + url + ")")
    else:
        context.bot.send_message(query.from_user.id, "Your video is loading ...")

        if 'vk' in social_network:
            flag, path = download_vk_video(video_id, res)
        elif 'yt' in social_network:
            flag, path = download_yt_video(video_id, res)

        video_file = open(path, 'rb')
        context.bot.send_video(update.callback_query.from_user.id, video_file, timeout=200)

        rmtree(os.path.join("files", path.split('/')[1]), ignore_errors=True)


def handle_message(update, context):
    result = 0
    reason = ''

    if update.message:

        url = update.message.text
        user = update.message.from_user.name

        if check_instagram(url):
            flag, post = get_insta_links(url)

            contents = []

            try:
                for node in post.get_sidecar_nodes():
                    contents.append(node)

                if flag:

                    media_group = []
                    context.bot.send_message(update.message.chat.id, "Your data is loading ...")

                    if len(contents):
                        for node in contents:
                            if node.is_video:
                                # print(node.video_url)
                                media_group.append(InputMediaVideo(node.video_url))
                            else:
                                media_group.append(InputMediaPhoto(node.display_url))
                        context.bot.sendMediaGroup(update.message.chat.id, media_group, timeout=200)
                    else:
                        if post.is_video:

                            context.bot.sendMediaGroup(update.message.chat.id, [InputMediaVideo(post.video_url)],
                                                       timeout=200)
                        else:
                            context.bot.sendMediaGroup(update.message.chat.id, [InputMediaPhoto(post.url)], timeout=200)

                    if post.caption:
                        context.bot.send_message(update.message.chat.id, post.caption)

                    result = 1
                else:
                    reason = 'Instagram error'
                    context.bot.sendMessage(update.message.chat.id,
                                            "Invalid link. Check if the post is public.")
            except Exception as e:
                print(str(e))
                context.bot.sendMessage(update.message.chat.id,
                                        "Invalid link. Check if the post is public.")

        elif check_facebook(url):
            flag, video_path, video_url = download_fb_video(url, "hd")
            print(flag, video_path)

            if flag:
                video_file = open(video_path, 'rb')
                context.bot.send_video(update.message.chat.id, video_file, timeout=200)
                result = 1
            else:
                context.bot.sendMessage(update.message.chat.id,
                                        "Invalid link. Check if the post is public.")
                reason = 'Facebook error'
        elif check_vkontakte(url):
            flag, files, video_id = get_vk_resolutions(url)

            if flag:

                if len(files) > 0:

                    keyboard = []

                    for file in files:
                        text = file.res.split('.')[0] + 'p (' + str(file.size) + ' MB)'
                        callback_data = 'vk' + "--" + video_id + '--' + file.res + '--' + str(file.size)
                        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback_data)])

                    reply_markup = InlineKeyboardMarkup(keyboard)

                    context.bot.send_message(update.message.chat.id, text="Choose resolution",
                                             reply_markup=reply_markup)
                    result = 1
                else:
                    context.bot.send_message(update.message.chat.id,
                                             text="I can’t download the video, there are several possible reasons: \n 1) The video is marked as 18+ \n 2) The video is live broadcast \n 3) The video is private \n 4) The video is uploaded to another hosting, for example, YouTube.")
            else:
                context.bot.sendMessage(update.message.chat.id,
                                        "I can’t download the video, there are several possible reasons: \n 1) The video is marked as 18+ \n 2) The video is live broadcast \n 3) The video is private \n 4) The video is uploaded to another hosting, for example, YouTube.")

        elif check_youtube(url):
            flag, streams, video_id = get_youtube_resolutions(url)

            if flag:

                keyboard = []

                for stream in streams:
                    text = stream.res.split('.')[0] + ' (' + str(stream.size) + ' MB)'
                    callback_data = "yt" + "--" + video_id + '--' + stream.res + '--' + str(stream.size)
                    keyboard.append([InlineKeyboardButton(text=text, callback_data=callback_data)])

                reply_markup = InlineKeyboardMarkup(keyboard)

                context.bot.send_message(update.message.chat.id, text="Choose resolution", reply_markup=reply_markup)
                result = 1
            else:
                context.bot.sendMessage(update.message.chat.id,
                                        "Invalid link. Check if the video is public.")
                reason = 'Youtube error'

        else:
            context.bot.sendMessage(update.message.chat.id, "Invalid link. Check if the post is public.")
            reason = 'Invalid URL'

        print(update.message.from_user.name, update.message.text, time.ctime(int(time.time())), result, reason,
              sep='    ', flush=True)

        user_exist = db_users.search(query.user == update.message.from_user.name)

        if len(user_exist) == 0:
            db_users.insert({'user': update.message.from_user.name, 'chat_id': update.message.chat.id})


if __name__ == '__main__':
    main()
