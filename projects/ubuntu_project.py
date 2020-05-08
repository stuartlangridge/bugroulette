import random
import urllib.request
from bs4 import BeautifulSoup
import math


def get(max_bug):
    # get a random int up to max_bug, but biased towards the more recent
    # https://gamedev.stackexchange.com/a/116875 with min = 0
    while True:
        result = math.floor(max_bug * pow(random.random(), 0.8))
        bug_page = "https://pad.lv/{}".format(result)
        print("trying", bug_page)
        try:
            fp = urllib.request.urlopen(bug_page)
        except:
            continue
        soup = BeautifulSoup(fp.read(), "lxml")
        fp.close()
        status = soup.select("div.status-content")[0].text.strip()
        if status in ("New", "Incomplete"):
            title = soup.select("h1#edit-title")[0].text.strip()
            return {
                "title": title,
                "link": bug_page
            }
        else:
            print("bad status", status)
            continue
    return random.randint(1, max_bug)


def get_max_bug_number():
    fp = urllib.request.urlopen(
        "https://bugs.launchpad.net/ubuntu/+bugs?orderby=-id&start=0")
    soup = BeautifulSoup(fp.read(), "lxml")
    return int(soup.select("span.bugnumber")[0].text[1:])
