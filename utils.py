import instaloader
from instaloader import Post
import os
import random
import requests
import re
import urllib.request
from bs4 import BeautifulSoup
import vk
from urllib.request import urlopen, urlretrieve
from pytube import YouTube

access_token = "VK TOKEN"
session = vk.Session(access_token=access_token)
api = vk.API(session)

L = instaloader.Instaloader(sleep=True, download_geotags=False, filename_pattern="{shortcode}", quiet=False,
                            download_video_thumbnails=False, download_comments=False)

vk_video_reg = re.compile("-\d+_\d+")

resolutions = ["144p", "240p", "360p", "480p", "720p", "1080p"]

class Video_info:
     def __init__(self, res, size):
         self.res = res
         self.size = size

def check_instagram(url):
    if "instagram.com" in url:
        return True
    else:
        return False


def check_facebook(url):
    if "fb.com" in url or "facebook.com" in url:
        return True
    else:
        return False


def check_vkontakte(url):
    if "vk.com" in url or "vkontakte.ru" in url:
        return True
    else:
        return False

def check_youtube(url):
    if "youtube.com" in url or "youtu.be" in url:
        return True
    else:
        return False


def check_coub(url):
    instareg = re.compile('(https?:\/\/www\.)?instagram\.com(\/p\/[a-zA-Z0-9-_]+\/?)')
    if instareg.search(url) == None:
        return False
    return True


def get_fb_link(html, quality):

    if quality == "sd":
        # Standard Definition video
        url = re.search('sd_src:"(.+?)"', html)[0]
    else:
        # High Definition video
        url = re.search('hd_src:"(.+?)"', html)[0]

    # cleaning the url
    url = url.replace('hd_src:"', '')
    url = url.replace('sd_src:"', '')
    url = url.replace('"', "")

    return url


def get_insta_shortcode(url):
    r = requests.get(url)

    parsed_html = BeautifulSoup(r.text)
    a = parsed_html.find('meta', attrs={'property': 'al:android:url'})
    shortcode = a.attrs['content'].split('/')[-2]

    return shortcode


def download_fb_video(url, quality):

    try:
        # Get source code
        r = requests.get(url)

        # Get download links
        file_url = get_fb_link(r.text, quality)

        name = str(random.random())[3:12] + ".mp4"
        folder_name = str(random.random())[3:12] + "_facebook"
        path = os.path.join("files", folder_name, name)

        if not os.path.exists(os.path.join("files", folder_name)):
            os.makedirs(os.path.join("files", folder_name))

        urllib.request.urlretrieve(file_url, path)

        return True, path, url
    except Exception as e:
        print(str(e))
        return False, "", ""


def download_instagram_content(url):

    try:
        shortcode = get_insta_shortcode(url)
        # Generate random seed for non duplicate folders
        # random_seed = random.randint(1,100)
        # folder_name = shortcode + str(random_seed)
        folder_name = str(random.random())[3:12] + "_instagram_" + shortcode

        # Create folder for file
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        # Download content
        post = Post.from_shortcode(L.context, shortcode)
        a = L.download_post(post, target=os.path.join("files", folder_name))

        # Get all content
        relevant_path = os.path.join("files", folder_name)
        included_extensions = ['jpg', 'mp4']
        file_names = [os.path.join("files", folder_name, fn) for fn in os.listdir(relevant_path) if any(fn.endswith(ext) for ext in included_extensions)]

        ## print(file_names)

        return True, file_names

    except AttributeError:
        return False, []

def get_insta_links(url):

    try:
        shortcode = get_insta_shortcode(url)

        post = Post.from_shortcode(L.context, shortcode)

        return True, post

    except Exception as e:
        print(str(e))
        return False, []


def get_vk_link(url):

    pos_id = vk_video_reg.search(url)
    video_id = url[pos_id.start():pos_id.end()]

    a = api.video.get(videos=video_id, v="5.92")
    player_url = a['items'][0]['player']

    return player_url, video_id


def get_vk_resolutions(url):

    try:

        player_url, video_id = get_vk_link(url)

        #if check_youtube(player_url):
        #    flag, files, video_id = get_youtube_resolutions(url)
        #    return flag, 'yt', files, video_id

        source = requests.get(player_url).text

        parsed_html = BeautifulSoup(source)
        tags = parsed_html.findAll('source')
        urls = []

        for tag in tags:
            urls.append(tag.attrs['src'])

        files = []

        for res in ['1080.mp4', '720.mp4', '480.mp4', '360.mp4', '240.mp4']:
            for url in urls:
                if res in url:
                    #resolutions.append(res)
                    size = get_filesize_by_link(url)
                    files.append(Video_info(res, size))
                    #sizes.append(size)

        return True, files, video_id

    except Exception as e:
        print(str(e))

        return False, [], ""

def download_vk_video(video_id, res):

    a = api.video.get(videos=video_id, v="5.92")
    player_url = a['items'][0]['player']

    html = requests.get(player_url).text

    parsed_html = BeautifulSoup(html)
    tags = parsed_html.findAll('source')
    urls = []

    for tag in tags:
        urls.append(tag.attrs['src'])

    folder_name = str(random.random())[3:12] + "_vk_" + video_id

    if not os.path.exists(os.path.join("files", folder_name)):
        os.makedirs(os.path.join("files", folder_name))

    for url in urls:
        if res in url:
            source = url.replace('\\/', '/')
            reg = re.compile('/([^/]*\.mp4)')
            name = reg.findall(source)[0]
            path = os.path.join("files", folder_name, name)
            urlretrieve(source, path)
            break

    return True, path


def download_yt_video(video_id, res):

    url = "https://youtu.be/" + video_id

    yt = YouTube(url)

    filename = video_id + '.mp4'
    folder_name = str(random.random())[3:12] + "_yt_" + video_id
    folder_path = os.path.join("files", folder_name)

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    filepath = yt.streams.filter(subtype='mp4', res=res, audio_codec='mp4a.40.2').first().download(output_path=os.path.join("files", folder_name),
                                                                  filename=filename)

    return True, filepath


def get_youtube_resolutions(url):

    try:

        available_resolutions = []

        yt = YouTube(url)

        streams = yt.streams
        video_id = yt.video_id

        for res in resolutions:
            filter_streams = streams.filter(subtype='mp4', res=res, audio_codec='mp4a.40.2').all()
            if len(filter_streams) > 0:
                available_resolutions.append(Video_info(res=res, size=int(filter_streams[0].filesize / 1000000)))

        return True, available_resolutions, video_id

    except Exception as e:

        print(str(e))
        return False, [], ""


def get_filesize_by_link(url):
    site = urlopen(url)
    meta = site.info()

    return round(int(meta["Content-Length"]) / 1000000, 2)


def get_vk_link_by_res(video_id, res):
    a = api.video.get(videos=video_id, v="5.92")
    player_url = a['items'][0]['player']

    html = requests.get(player_url).text

    parsed_html = BeautifulSoup(html)
    tags = parsed_html.findAll('source')
    urls = []

    for tag in tags:
        urls.append(tag.attrs['src'])

    folder_name = str(random.random())[3:12] + "_vk_" + video_id

    if not os.path.exists(os.path.join("files", folder_name)):
        os.makedirs(os.path.join("files", folder_name))

    for url in urls:
        if res in url:
            source = url.replace('\\/', '/')
            return source

    return False


def get_yt_link_by_res(video_id, res):

    url = "https://youtu.be/" + video_id

    yt = YouTube(url)

    direct_url = yt.streams.filter(subtype='mp4', res=res, audio_codec='mp4a.40.2').first().url

    return direct_url


def download_yt_video(video_id, res):

    url = "https://youtu.be/" + video_id

    yt = YouTube(url)

    filename = video_id + '.mp4'
    folder_name = str(random.random())[3:12] + "_yt_" + video_id
    folder_path = os.path.join("files", folder_name)

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    filepath = yt.streams.filter(subtype='mp4', res=res, audio_codec='mp4a.40.2').first().download(output_path=os.path.join("files", folder_name),
                                                                  filename=filename)

    return True, filepath