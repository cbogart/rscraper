
def extractGitDescription(conn):
    #pkgs = conn.execute("select * from gitprojects where id " + \
       #"in (select project_id from gitfiles where project_name='DESCRIPTION');")
    pkgs = conn.execute("select gitprojects.*, group_contact(imports.package_name) myimports from gitprojects " + \
            "left join gitimports on imports.project_id=gitprojects.id where gitprojects.id in " + \
            "(select project_id from gitfiles where project_name='DESCRIPTION');")
    for p in pkgs:
        yield {
          "Package": [pkgs["gitprojects.name"]],
          "Title": [pkgs["gitprojects.description"]],
          "Imports": pkgs["myimports"].split(","),
          "repository": "git" 
        }
