from gitscraper import GitProjectInfo
import pdb

def priority(row):
    priority = 10.0 if "api.github.com/repos/cran/" in row["gitprojects.url"] else \
               8.0  if "api.github.com/repos/Bioconductor/" in row["gitprojects.url"] else \
               7.0  if "api.github.com/repos/ropensci/" in row["gitprojects.url"] else \
               6.0  if "api.github.com/repos/rforge/" in row["gitprojects.url"] else \
               row["gitprojects.forks_count"]*1.0/1000+3 if row["gitprojects.forked_from"] == "" else \
               1
    return priority

# need Version
def extractGitDescription(conn):
    pkgs = conn.execute("select gitprojects.*, group_concat(distinct(gitimports.package_name)) myimports from gitprojects " + \
            "left join gitimports on gitimports.project_id=gitprojects.id where gitprojects.id in " + \
            "(select project_id from gitfiles where path='DESCRIPTION' or path = 'pkg/DESCRIPTION') group by gitprojects.id;")
    desc = {}
    for p in pkgs:
        name = p["gitprojects.name"]
        prj = GitProjectInfo(name, p["gitprojects.id"], p["gitprojects.url"])
        descinfo = prj.projectDescription()
        pri = priority(p)
        if "error" in descinfo:
            print "Couldn't read DESCRIPTION for git project ", name
            descinfo = {
              "Package": [name],
              "Version": "",
              "Title": [p["gitprojects.description"]],
              #"Imports": p["myimports"].split(","),
              "repository": "git",
              "user": prj.username(),
              "URL": ["http://github.com/" + prj.username() + "/" + name],
              "priority": pri
            }
        if name not in desc or desc[name]["priority"] < pri:
            desc[name] = descinfo
        desc[name]["priority"] = pri
        if "authors" not in desc[name]:
            if "Author" in descinfo:
                desc[name]["authors"] = descinfo["Author"]
            else:
                desc[name]["authors"] = ""
        if "user" not in desc[name]:
            desc[name]["user"] = prj.username()
        if "URL" not in desc[name] or desc[name]["URL"] == "" or desc[name]["URL"] == [""]:
            desc[name]["URL"] = ["http://github.com/" + prj.username() + "/" + name]
    return desc

# need url, title, description, repository
def extractGitWebscrape(conn):
    pkgs = conn.execute("select * from gitprojects " + \
            "where gitprojects.id in " + \
            "(select project_id from gitfiles where path='DESCRIPTION');")
    ws = {}
    for p in pkgs:
        prj = GitProjectInfo(p["gitprojects.name"], p["gitprojects.id"], p["gitprojects.url"])
        name = p["gitprojects.name"]
        if name not in ws or ws[name]["priority"] < priority(p):
            ws[p["gitprojects.name"]] = {
              "URL": p["gitprojects.url"],
              "title": p["gitprojects.description"],
              "description": p["gitprojects.description"],
              "priority": priority(p),
              "repository": "git",
              "user": prj.username()
            }
    return ws

