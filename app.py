import os
import random
import glob
import time
import importlib.util
from flask import Flask, g, abort, render_template, request

app = Flask(__name__)


def read_projects():
    projects_folder = os.path.join(os.path.dirname(__file__), "projects")
    projects_files = glob.glob(os.path.join(projects_folder, "*_project.py"))
    projects = {}
    for f in projects_files:
        _, fn = os.path.split(f)
        name = "_".join(fn.split("_")[:-1])
        spec = importlib.util.spec_from_file_location(name, f)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        projects[name] = {
            "get": getattr(mod, "get"),
            "get_max_bug_number": getattr(mod, "get_max_bug_number"),
            "max_file": os.path.join(projects_folder, "{}.max".format(name)),
            "name": name
        }
    return projects


def setup(g):
    g.projects = read_projects()


@app.route("/")
def index():
    if "initialised" not in g: setup(g)
    return render_template("index.html")


@app.route("/<project_name>/")
def for_project(project_name):
    if "initialised" not in g: setup(g)
    if project_name not in g.projects:
        if project_name == "any":
            project_name = random.choice(list(g.projects.keys()))
        else:
            return abort(404)
    project = g.projects[project_name]
    try:
        age_max = os.stat(project["max_file"]).st_mtime
    except FileNotFoundError:
        age_max = 0
    if time.time() - age_max > 60 * 60:
        max_bug = int(project["get_max_bug_number"]())
        with open(project["max_file"], mode="w") as fp:
            fp.write(str(max_bug))
    else:
        with open(project["max_file"], mode="r") as fp:
            try:
                max_bug = int(fp.read().strip())
            except ValueError:
                max_bug = int(project["get_max_bug_number"]())
                with open(project["max_file"], mode="w") as fp:
                    fp.write(str(max_bug))
    bug = project["get"](max_bug, known_good="quick" in request.args)
    return render_template("bug.html", bug=bug, project=project)
