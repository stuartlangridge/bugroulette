import random
import urllib.request
from bs4 import BeautifulSoup
import math
import sys
import sqlite3
import os


def get_db():
    con = sqlite3.connect(os.path.join(os.path.dirname(__file__), "ubuntu.db"))
    con.execute("create table if not exists bugs (id text, isok bool, link text, title text)")
    con.commit()
    return con


def db_fetch(bug_number):
    db = get_db()
    crs = db.cursor()
    crs.execute("select id, isok, link, title from bugs where id = ?", [str(bug_number)])
    rows = crs.fetchall()
    db.close()
    if len(rows) == 0:
        return None
    else:
        return rows[0]


def db_store(bug_number, isok, link="", title=""):
    db = get_db()
    db.execute("insert into bugs (id, isok, link, title) values (?, ?, ?, ?)", [str(bug_number), isok, link, title])
    db.commit()
    db.close()


def get_individual(bug_number, known_good=False):
    if known_good:
        # get a bug from our known good list
        db = get_db()
        crs = db.cursor()
        crs.execute("select id, link, title from bugs where isok = 1 order by random() limit 1")
        rows = crs.fetchall()
        id, link, title = rows[0]
        return True, {"title": title, "link": link}
        db.close()
    else:
        val = db_fetch(bug_number)
        if val is None:
            pass  # if we know nothing of this bug, carry on with it
        else:
            id, isok, link, title = val
            if isok == 0:
                print("Bug", bug_number, "known bad")
                return False, None  # bail if we know this one to be a dud
            else:
                # this bug is known to be ok, then return it
                return True, {"title": title, "link": link}
    bug_page = "https://pad.lv/{}".format(bug_number)
    print("trying", bug_page)
    try:
        fp = urllib.request.urlopen(bug_page)
    except:
        db_store(bug_number, False)
        return False, None
    soup = BeautifulSoup(fp.read(), "lxml")
    fp.close()
    project = soup.select("div#watermark a")[0]["href"].split("/")[-1]
    if project != "ubuntu":
        print("Not Ubuntu project:", project)
        db_store(bug_number, False)
        return False, None
    dupe = soup.select("div#bug-is-duplicate .bug-duplicate-details a")
    if dupe:
        override_result = dupe[0]["href"].split("/")[-1]
        print("Duplicate of", override_result)
        db_store(bug_number, False)
        return False, None
    try:
        status = soup.select("div.status-content")[0].text.strip()
    except IndexError:
        print("Bug unreadable")
        db_store(bug_number, False)
        return False, None
    if status in ("New", "Incomplete", "Confirmed"):
        title = soup.select("h1#edit-title")[0].text.strip()
        db_store(bug_number, True, bug_page, title)
        return True, {
            "title": title,
            "link": bug_page
        }
    else:
        print("Not seeking contributions: status", status)
        db_store(bug_number, False)
        return False, None


def get(max_bug, override_result=None, known_good=False):
    # get a random int up to max_bug, but biased towards the more recent
    # https://gamedev.stackexchange.com/a/116875 with min = 0
    while True:
        if override_result:
            result = override_result
            override_result = None
        else:
            result = math.floor(max_bug * pow(random.random(), 0.8))
        isok, bug = get_individual(result, known_good)
        if not isok:
            if max_bug == 0:
                max_bug = get_max_bug_number()
            continue
        return bug


def get_max_bug_number():
    fp = urllib.request.urlopen(
        "https://bugs.launchpad.net/ubuntu/+bugs?orderby=-id&start=0")
    soup = BeautifulSoup(fp.read(), "lxml")
    return int(soup.select("span.bugnumber")[0].text[1:])


if __name__ == "__main__":
    # for testing, run as python3 projects/ubuntu_project.py
    # or python3 projects/ubuntu_project.py 434733
    # or to get a definitely known good bug, python3 projects/ubuntu_project.py -1
    if len(sys.argv) > 1 and sys.argv[1] == "-1":
        print(get(0, None, True))
    elif len(sys.argv) > 1:
        print(get(0, sys.argv[1]))
    else:
        max_bug = get_max_bug_number()
        print(get(max_bug))
