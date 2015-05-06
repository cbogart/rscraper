from gitscraper import GitProjectInfo
from utils import ensure_unicode
import re
import pdb

def priority(row):
    priority = 10.0 if "api.github.com/repos/cran/" in row["gitprojects.url"] else \
               8.0  if "api.github.com/repos/Bioconductor/" in row["gitprojects.url"] else \
               7.0  if "api.github.com/repos/ropensci/" in row["gitprojects.url"] else \
               6.0  if "api.github.com/repos/rforge/" in row["gitprojects.url"] else \
               row["gitprojects.forks_count"]*1.0/1000+3 if row["gitprojects.forked_from"] == "" else \
               1
    return priority


def extractGitDescription(conn):
    pkgs = conn.execute(r"""select gitprojects.*, f1.path descpath
            from gitfiles f1 
            left join gitprojects on f1.project_id=gitprojects.id
            where f1.path like "%DESCRIPTION" and f1.path not like "%/tags/%"
            order by forks_count, stargazers_count desc;
            """)
    
    desc = {}
    for p in pkgs:
        name = p["gitprojects.name"]
        pri = priority(p)
        deep_name = re.search(r"""/([^0-9][^/]+)/DESCRIPTION""", p["descpath"])
        
        # Use the organization name as a pseudo-task view, unless it's RForge,
        # in which case we'll call it a repository (see below)
        taskviews = [p["gitprojects.owner"]] \
             if p["gitprojects.ownertype"] == "Organization" \
             and p["gitprojects.owner"] != "rforge" else []

        # Accrue information about task views based on organizations that have forked this package
        if name in desc:
            desc[name]["views"] = list(set(taskviews + desc[name].get("views",[])))
            
        #if "forge" in p["gitprojects.url"]:
        ##    print p["gitprojects.url"]
        #    pdb.set_trace()
            
        # If the DESCRIPTION file is in a subdirectory, use that as the package name
        #  (unless it's "pkg", which is an r-forge convention)
        #  (NB the query also excludes ones in directories called "tags", because
        #   those are in most cases just information about old versions)
        if deep_name and deep_name.group(0) != "pkg":
            name = deep_name.group(1)
            taskviews = taskviews + [p["gitprojects.name"] ]
            
            
        if name not in desc or desc[name]["priority"] < pri:
            prj = GitProjectInfo(name, p["gitprojects.id"], p["gitprojects.url"], 
                                 p["gitprojects.name"], p["descpath"])
            desc[name] = prj.projectDescription()
            if "error" in desc[name]:
                print "Couldn't read DESCRIPTION for git project ", name
                desc[name] = {
                  "Package": [name],
                  "Version": "",
                  "Title": [p["gitprojects.description"]],
                  # Treat the rforge mirror within github as a repository of its own
                  # just because, man, why talk to yet another API.
                  "repository": "r-forge" if p["gitprojects.owner"]=="rforge" else "git",
                  "user": prj.username(),
                  "URL": ["http://github.com/" + prj.username() + "/" + name],
                  "priority": pri
                }
            desc[name]["views"] = desc[name].get("views",[]) + taskviews
            desc[name]["priority"] = pri
            if "authors" not in desc[name]:
                if "Author" in desc[name]:
                    desc[name]["authors"] = desc[name]["Author"]
                elif "Authors@R" in desc[name]:
                    desc[name]["authors"] = desc[name]["Authors@R"]
                else:
                    desc[name]["authors"] = ""
            if p["gitprojects.owner"] == "rforge":
                desc[name]["repository"] = "r-forge" 
            if "user" not in desc[name]:
                desc[name]["user"] = prj.username()
            if "Title" not in desc[name]:
                desc[name]["Title"] = p["gitprojects.name"]
            if "Description" not in desc[name]:
                desc[name]["description"] = [p["gitprojects.description"] or "(no description)"]
            else:
                desc[name]["description"] = desc[name]["Description"]
            if "URL" not in desc[name] or desc[name]["URL"] == "" or desc[name]["URL"] == [""]:
                desc[name]["URL"] = ["http://github.com/" + prj.username() + "/" + name]
            
        
    return desc


def makeGitPseudoWebscrape(desc):
    ws = {}
    for name in desc:
        
        ws[name] = {
            "title": ensure_unicode(desc[name]["Title"][0]),
            "repository": desc[name].get("repository", "git"),
            "priority": desc[name]["priority"],
            "user": desc[name]["user"],
            "URL": desc[name]["URL"][0],
            "views": desc[name]["views"],
            "description": ", ".join(desc[name]["description"])
            }        
    return ws   

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

