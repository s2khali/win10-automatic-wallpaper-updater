import ctypes
import os.path
import threading
import time
from urllib import request as ulreq
from PIL import ImageFile
import requests.auth
from win10toast import ToastNotifier
from dotenv import load_dotenv

load_dotenv()

REDDIT_ID = os.getenv("REDDIT_ID")
REDDIT_SECRET = os.getenv("REDDIT_SECRET")

REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")

SUBREDDIT = "wallpapers"

USERAGENT = "windows:{}:v1 (by /u/{})".format(REDDIT_ID, REDDIT_USERNAME)

SCREEN_HEIGHT = 1440
TEMP_LOC = "C:\\Users\\{}\\AppData\\Local\\Temp".format(os.getlogin())
ALLOWED_TYPES = [".png", ".jpg", ".jpeg"]


def getimagesize(uri):
    file = ulreq.urlopen(uri)
    size = file.headers.get("content-length")
    if size:
        size = int(size)
    p = ImageFile.Parser()
    while True:
        data = file.read(1024)
        if not data:
            break
        p.feed(data)
        if p.image:
            return size, p.image.size
    file.close()
    return size, None


def downloadphoto(uri):
    file_type = os.path.splitext(uri)[1]
    if file_type in ALLOWED_TYPES:
        r = requests.get(uri, allow_redirects=True)
        loc = "{}\\temp{}".format(TEMP_LOC, file_type)
        open(loc, "wb").write(r.content)
        return loc
    else:
        return ""


def getaccesstoken():
    client_auth = requests.auth.HTTPBasicAuth(REDDIT_ID, REDDIT_SECRET)
    post_data = {"grant_type": "password", "username": REDDIT_USERNAME, "password": REDDIT_PASSWORD}
    post_headers = {"User-Agent": USERAGENT}

    token_request = requests.post("https://www.reddit.com/api/v1/access_token", auth=client_auth, data=post_data,
                                  headers=post_headers)
    return token_request.json()['access_token']


def getposts(token):
    get_headers = {"Authorization": "bearer {}".format(token), "User-Agent": USERAGENT}

    posts_request = requests.get("https://oauth.reddit.com/r/{}/top?t=week".format(SUBREDDIT), headers=get_headers)

    return posts_request.json()['data']['children']


def removetempfile(loc):
    if os.path.exists(loc):
        os.remove(loc)


def notify():
    toast = ToastNotifier()
    toast.show_toast("Wallpaper Updater Failed!", "Could not get a new wallpaper!", duration=20)  # The duration is
    # set here because running this in a thread quits cleaner than this handling it


temp_file_loc = ""
access_token = getaccesstoken()

for top_post in getposts(access_token):
    if top_post['kind'] == "t3" and top_post['data']['url'].find("i.redd.it/") != -1:
        sizing = getimagesize(top_post['data']['url'])
        height = sizing[1][1]

        if height >= SCREEN_HEIGHT:  # TODO: Make sure resolution matches, not just a minimum height
            temp_file_loc = downloadphoto(top_post['data']['url'])
            break

if not temp_file_loc:

    thread = threading.Thread(target=notify)
    thread.daemon = True  # Make sure we close the thread on quit()
    thread.start()

    time.sleep(5)  # Make sure the notification stays for a bit
    quit()
else:
    ctypes.windll.user32.SystemParametersInfoW(20, 0, temp_file_loc, 3)
    removetempfile(temp_file_loc)
    quit()
