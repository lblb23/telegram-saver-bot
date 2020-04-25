import os
import random

import instaloader
import requests
from bs4 import BeautifulSoup
from instaloader import Post
from pytube import YouTube

L = instaloader.Instaloader(
    sleep=True,
    download_geotags=False,
    filename_pattern="{shortcode}",
    quiet=False,
    download_video_thumbnails=False,
    download_comments=False,
)

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
    r = requests.get(url)

    parsed_html = BeautifulSoup(r.text)
    a = parsed_html.find("meta", attrs={"property": "al:android:url"})
    shortcode = a.attrs["content"].split("/")[-2]

    return shortcode


def get_insta_links(url: str) -> tuple:
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


def get_youtube_resolutions(url: str) -> tuple:
    """
    Return list of available resolutions and video_id from youtube URL
    :param url: URL
    :return: success status, list of available resolutions and video_id
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

        return True, available_resolutions, video_id

    except Exception as e:

        print(str(e))
        return False, [], ""


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
