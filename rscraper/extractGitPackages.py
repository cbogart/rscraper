
def extractGitPackageInfo(conn):
    pkgs = conn.execute("select * from packages where package_id " + \
       "in (select id from imports where package_name='DESCRIPTION');")
    return {
      "Package": packages.name,
      "Title": packages.description,
      "repository": "git" 
    }
