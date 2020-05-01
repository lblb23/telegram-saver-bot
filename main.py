# -*- coding: utf-8 -*-
import logging
import os
import ssl
import time
from shutil import rmtree

import yaml

ssl._create_default_https_context = ssl._create_unverified_context

from chatbase import Message
from telegram import (
    InputMediaPhoto,
    InputMediaVideo,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
)
from tinydb import TinyDB, Query

from utils import (
    get_insta_links,
    check_instagram,
    check_youtube,
    get_youtube_resolutions,
    download_yt_video,
    get_yt_link_by_res,
)

with open("config.yml") as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

update_id = None

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename=".log",
)

logger = logging.getLogger(__name__)
query = Query()
db_users = TinyDB("db_users.json")


def main():
    updater = Updater(config["telegram_token"], use_context=True)
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
        "Hello! I can download for you a picture or video from Instagram and Youtube. Just send me a link to the post."
    )


def help(update, context):
    update.message.reply_text(
        "Just send me a link to an Instagram post or Youtube video."
    )


def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def button(update, context):
    query = update.callback_query

    context.bot.deleteMessage(query.from_user.id, query.message.message_id)

    social_network, video_id, res, size = query.data.split("--")

    if float(size) > 50:
        if social_network == "yt":
            url = get_yt_link_by_res(video_id, res)
        context.bot.send_message(
            chat_id=query.from_user.id,
            parse_mode="Markdown",
            text="Telegram allows to send video only up to 50 mb, so we can only give a direct link: [link]("
            + url
            + ")",
        )
    else:
        context.bot.send_message(query.from_user.id, "Your video is loading ...")

        if "yt" in social_network:
            flag, path = download_yt_video(video_id, res)

        video_file = open(path, "rb")
        context.bot.send_video(
            update.callback_query.from_user.id, video_file, timeout=200
        )

        rmtree(os.path.join("files", path.split("/")[1]), ignore_errors=True)


def handle_message(update, context):
    result = False
    reason = ""
    platform = ""

    if update.message:
        username = update.message.from_user.name
        chat_id = update.message.chat.id

        url = update.message.text

        if check_instagram(url):
            flag, post = get_insta_links(url)
            platform = "Instagram"

            contents = []

            try:
                for node in post.get_sidecar_nodes():
                    contents.append(node)

                if flag:

                    media_group = []
                    context.bot.send_message(
                        chat_id=chat_id, text="Your data is loading ..."
                    )

                    if len(contents):
                        for node in contents:
                            if node.is_video:
                                media_group.append(InputMediaVideo(node.video_url))
                            else:
                                media_group.append(InputMediaPhoto(node.display_url))
                        context.bot.sendMediaGroup(
                            chat_id=chat_id, media=media_group, timeout=200
                        )
                    else:
                        if post.is_video:

                            context.bot.sendMediaGroup(
                                chat_id=chat_id,
                                media=[InputMediaVideo(post.video_url)],
                                timeout=200,
                            )
                        else:
                            context.bot.sendMediaGroup(
                                chat_id=chat_id,
                                media=[InputMediaPhoto(post.url)],
                                timeout=200,
                            )

                    if post.caption:
                        context.bot.send_message(chat_id=chat_id, text=post.caption)

                    result = True
                else:
                    reason = "Instagram error"
                    context.bot.sendMessage(
                        chat_id=chat_id,
                        text="Invalid link. Check if the post is public.",
                    )
            except Exception as e:
                print(str(e))
                context.bot.sendMessage(
                    chat_id=chat_id, text="Invalid link. Check if the post is public."
                )

        elif check_youtube(url):
            flag, streams, video_id = get_youtube_resolutions(url)
            platform = "YouTube"

            if flag:

                keyboard = []

                for stream in streams:
                    text = stream.res.split(".")[0] + " (" + str(stream.size) + " MB)"
                    callback_data = (
                        "yt"
                        + "--"
                        + video_id
                        + "--"
                        + stream.res
                        + "--"
                        + str(stream.size)
                    )
                    keyboard.append(
                        [InlineKeyboardButton(text=text, callback_data=callback_data)]
                    )

                reply_markup = InlineKeyboardMarkup(keyboard)

                context.bot.send_message(
                    chat_id, text="Choose resolution", reply_markup=reply_markup,
                )
                result = True
            else:
                context.bot.sendMessage(
                    chat_id, "Invalid link. Check if the video is public.",
                )
                reason = "Youtube error"

        else:
            context.bot.sendMessage(
                chat_id=chat_id, text="Invalid link. Check if the post is public."
            )
            reason = "Invalid URL"
            platform = "Unknown"

        print(
            username,
            url,
            time.ctime(int(time.time())),
            result,
            reason,
            sep="    ",
            flush=True,
        )

        msg = Message(
            api_key=config["chatbase_token"],
            platform=platform,
            user_id=username,
            message=url,
            not_handled=~result,
        )
        msg.send()

        user_exist = db_users.search(query.user == update.message.from_user.name)

        if len(user_exist) == 0:
            db_users.insert({"user": username, "chat_id": chat_id})


if __name__ == "__main__":
    main()
