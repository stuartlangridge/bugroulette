import random
import urllib.request
from bs4 import BeautifulSoup
import math
import sys


def get(max_bug, override_result=None):
    # get a random int up to max_bug, but biased towards the more recent
    # https://gamedev.stackexchange.com/a/116875 with min = 0
    while True:
        if override_result:
            result = override_result
            override_result = None
        else:
            result = math.floor(max_bug * pow(random.random(), 0.8))
        bug_page = "https://pad.lv/{}".format(result)
        print("trying", bug_page)
        try:
            fp = urllib.request.urlopen(bug_page)
        except:
            continue
        soup = BeautifulSoup(fp.read(), "lxml")
        fp.close()
        dupe = soup.select("div#bug-is-duplicate .bug-duplicate-details a")
        if dupe:
            override_result = dupe[0]["href"].split("/")[-1]
            print("Duplicate of", override_result)
            continue
        try:
            status = soup.select("div.status-content")[0].text.strip()
        except IndexError:
            print("Bug unreadable")
            continue
        if status in ("New", "Incomplete", "Confirmed"):
            title = soup.select("h1#edit-title")[0].text.strip()
            return {
                "title": title,
                "link": bug_page
            }
        else:
            print("Not seeking contributions: status", status)
            continue


def get_max_bug_number():
    fp = urllib.request.urlopen(
        "https://bugs.launchpad.net/ubuntu/+bugs?orderby=-id&start=0")
    soup = BeautifulSoup(fp.read(), "lxml")
    return int(soup.select("span.bugnumber")[0].text[1:])


if __name__ == "__main__":
    # for testing, run as python3 projects/ubuntu_project.py
    # or python3 projects/ubuntu_project.py 434733
    max_bug = get_max_bug_number()
    print(get(max_bug, sys.argv[1] if len(sys.argv) > 1 else None))
