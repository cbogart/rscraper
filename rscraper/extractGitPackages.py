
# need Version
def extractGitDescription(conn):
    pkgs = conn.execute("select gitprojects.*, group_concat(distinct(gitimports.package_name)) myimports from gitprojects " + \
            "left join gitimports on gitimports.project_id=gitprojects.id where gitprojects.id in " + \
            "(select project_id from gitfiles where path='DESCRIPTION') group by gitprojects.id;")
    desc = {}
    for p in pkgs:
        name = p["gitprojects.name"]
        prj = GitProjectInfo(name, p["gitprojects.id"], p["gitprojects.url"])
        descinfo = prj.projectDescription()
        if "error" in descinfo:
            print "Couldn't read DESCRIPTION for git project ", name
            desc[name] = {
              "Package": [name],
              "Version": "",
              "Title": [p["gitprojects.description"]],
              #"Imports": p["myimports"].split(","),
              "repository": "git" 
            }
        else:
            desc[name] = descinfo
    return desc

# need url, title, description, repository
def extractGitWebscrape(conn):
    pkgs = conn.execute("select * from gitprojects " + \
            "where gitprojects.id in " + \
            "(select project_id from gitfiles where path='DESCRIPTION');")
    ws = {}
    for p in pkgs:
        ws[p["gitprojects.name"]] = {
          "url": p["gitprojects.url"],
          "title": p["gitprojects.description"],
          "description": p["gitprojects.description"],
          "repository": "git" 
        }
    return ws

