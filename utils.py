import os
import random
import re
from shutil import rmtree

from instaloader import Post, Instaloader
from pytube import YouTube
from telegram import (
    Update,
    InputMediaPhoto,
    InputMediaVideo,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import CallbackContext

resolutions = ["144p", "240p", "360p", "480p", "720p", "1080p"]


class Video_info:
    def __init__(self, res, size):
        self.res = res
        self.size = size


def check_instagram(url: str) -> bool:
    """
    Check if url from instagram
    :param url: URL
    :return: True if url from instagram else False
    """
    if "instagram.com" in url:
        return True
    else:
        return False


def check_youtube(url: str) -> bool:
    """
    Check if url from youtube
    :param url: URL
    :return: True if url from youtube else False
    """
    if "youtube.com" in url or "youtu.be" in url:
        return True
    else:
        return False


def get_insta_shortcode(url: str) -> str:
    """
    Return shortcode of post from instagram URL
    :param url: URL
    :return: shortcode of post
    """
    shortcode = re.findall(
        r"(?:(?:http|https):\/\/)?(?:www.)?(?:instagram.com|instagr.am)\/p\/([A-Za-z0-9-_.]+)",
        url,
    )[0]

    return shortcode


def get_insta_links(L: Instaloader, url: str) -> tuple:
    """
    Return list of shortcodes
    :param url: URL
    :return: success status and list of shortcodes
    """
    try:
        shortcode = get_insta_shortcode(url)

        post = Post.from_shortcode(L.context, shortcode)

        return True, post

    except Exception as e:
        print(str(e))
        return False, []


def send_instagram_data(
    insta_context: Instaloader,
    context: CallbackContext,
    chat_id: int,
    url: str,
    messages: dict,
) -> tuple:
    """
    Send instagram data to user with chat_id
    1. Get nodes from post
    2. Send to user loading message
    3. If post contains >0 nodes then collect media group and send
    4. If post contains 0 nodes - it's can be video, try to send video
    :param context: callback context
    :param chat_id: chat id with user
    :param url: messsage from usersend_instagram_data
    :param messages: dict with templates of messages
    :return: success status and reason if failed
    """
    flag, post = get_insta_links(L=insta_context, url=url)

    contents = []

    try:
        for node in post.get_sidecar_nodes():
            contents.append(node)

        if flag:
            media_group = []
            context.bot.send_message(chat_id=chat_id, text=messages["loading"])

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
                        chat_id=chat_id, media=[InputMediaPhoto(post.url)], timeout=200
                    )

            if post.caption:
                context.bot.send_message(chat_id=chat_id, text=post.caption)

            result = True
            traceback = "Success"
        else:
            result = False
            traceback = "Instagram: Failed with loading data"
            context.bot.sendMessage(
                chat_id=chat_id, text=messages["invalid_url"],
            )
    except Exception as e:
        result = False
        traceback = str(e)
        context.bot.sendMessage(chat_id=chat_id, text=messages["invalid_url"])

    return result, traceback


def send_youtube_data(
    context: CallbackContext, chat_id: int, url: str, messages: dict
) -> tuple:
    """
    NOT USED
    Send video with highest resolution and filesize < 50mb
    :param context: callback context
    :param chat_id: chat id with user
    :param url: messsage from user
    :param messages: dict with templates of messages
    :return: success status and reason if failed
    """
    yt = YouTube(url)

    try:
        stream_found = False
        stream = None
        for stream in (
            yt.streams.filter(subtype="mp4", audio_codec="mp4a.40.2")
            .order_by("filesize")
            .desc()
        ):
            if stream.filesize / 1000000 < 49:
                stream_found = True
                break
            else:
                continue

        if stream_found:
            context.bot.send_video(chat_id=chat_id, video=stream.url, timeout=10)
            result = True
            traceback = "Success"
        else:
            context.bot.send_message(chat_id=chat_id, text=messages["error_youtube"])
            result = False
            traceback = "Not found suitable stream for uploading"
    except Exception as e:
        result = False
        traceback = str(e)
        context.bot.sendMessage(chat_id=chat_id, text=messages["invalid_url"])

    return result, traceback


def get_youtube_resolutions(url: str) -> tuple:
    """
    Return list of available resolutions and video_id from youtube URL
    :param url: URL
    :return: success status, list of available resolutions, video_id and error traceback
    """
    try:
        available_resolutions = []

        yt = YouTube(url)

        streams = yt.streams
        video_id = yt.video_id

        for res in resolutions:
            filter_streams = streams.filter(
                subtype="mp4", res=res, audio_codec="mp4a.40.2"
            ).all()
            if len(filter_streams) > 0:
                available_resolutions.append(
                    Video_info(res=res, size=int(filter_streams[0].filesize / 1000000))
                )

        result = True
        traceback = "Success"
    except Exception as e:
        result = False
        available_resolutions = []
        video_id = ""
        traceback = str(e)

    return result, available_resolutions, video_id, traceback


def get_yt_link_by_res(video_id: str, res: str) -> str:
    """
    Get direct url of video with video_id and resolution
    :param video_id: youtube video_id
    :param res: resolution
    :return: direct url of video
    """
    url = "https://youtu.be/" + video_id

    yt = YouTube(url)

    direct_url = (
        yt.streams.filter(subtype="mp4", res=res, audio_codec="mp4a.40.2").first().url
    )

    return direct_url


def download_yt_video(video_id: str, res: str) -> tuple:
    """
    Download video and return filepath
    :param video_id: youtube video_id
    :param res: resolution
    :return: success status and filepath
    """
    url = "https://youtu.be/" + video_id

    yt = YouTube(url)

    filename = video_id + ".mp4"
    folder_name = str(random.random())[3:12] + "_yt_" + video_id
    folder_path = os.path.join("files", folder_name)

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    filepath = (
        yt.streams.filter(subtype="mp4", res=res, audio_codec="mp4a.40.2")
        .first()
        .download(output_path=os.path.join("files", folder_name), filename=filename)
    )

    return True, filepath


def send_youtube_button(
    context: CallbackContext, chat_id: int, url: str, messages: dict
) -> tuple:
    """
    Send video user
    :param context: callback context
    :param chat_id: chat id with user
    :param url: message from user
    :param messages: dict with templates of messages
    :return: success status and reason if failed
    """
    result, streams, video_id, traceback = get_youtube_resolutions(url)

    if result:

        keyboard = []

        for stream in streams:
            text = stream.res.split(".")[0] + " (" + str(stream.size) + " MB)"
            callback_data = (
                "yt" + "--" + video_id + "--" + stream.res + "--" + str(stream.size)
            )
            keyboard.append(
                [InlineKeyboardButton(text=text, callback_data=callback_data)]
            )

        reply_markup = InlineKeyboardMarkup(keyboard)

        context.bot.send_message(
            chat_id=chat_id,
            text=messages["choice_resolution"],
            reply_markup=reply_markup,
        )
    else:
        context.bot.sendMessage(chat_id=chat_id, text=messages["invalid_url"])

    return result, traceback


def handle_youtube_button(update: Update, context: CallbackContext, messages: dict):
    """
    Handle answer from youtube button
    :param update: telegram update
    :param context: telegram context
    :param messages: dict with templates of messages
    :return:
    """
    query = update.callback_query
    context.bot.deleteMessage(query.from_user.id, query.message.message_id)

    social_network, video_id, res, size = query.data.split("--")

    if float(size) > 50:
        url = get_yt_link_by_res(video_id, res)

        context.bot.send_message(
            chat_id=query.from_user.id,
            parse_mode="Markdown",
            text=messages["size_limit"].format(url),
        )
    else:
        context.bot.send_message(chat_id=query.from_user.id, text=messages["loading"])

        flag, path = download_yt_video(video_id, res)

        video_file = open(path, "rb")
        context.bot.send_video(
            chat_id=update.callback_query.from_user.id, video=video_file, timeout=200
        )

        rmtree(os.path.join("files", path.split("/")[1]), ignore_errors=True)


def send_error_message(context: CallbackContext, chat_id: int, messages: dict) -> tuple:
    """
    Send error message
    :param context: telegram context
    :param chat_id: chat id with user
    :param messages: dict with templates of messages
    :return: fail status and reason
    """
    context.bot.send_message(chat_id=chat_id, text=messages["invalid_url"])
    result = False
    traceback = "Invalid URL"

    return result, traceback


def send_unsupported_message(
    context: CallbackContext, chat_id: int, messages: dict, platform: str
) -> tuple:
    """
    Send error message about unsupported platform
    :param context: telegram context
    :param chat_id: chat id with user
    :param messages: dict with templates of messages
    :param platform: platform name
    :return: fail status and reason
    """
    context.bot.send_message(
        chat_id=chat_id, text=messages[f"unsupported_{platform.lower()}"]
    )
    result = False
    traceback = "Unsupported platform"

    return result, traceback
