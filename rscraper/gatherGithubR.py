import csv
import time
import datetime
# you need easy_install PyGithub or pip install PyGithub for this
from github import Github
import os
import random
import urllib
import urllib2
import sys
import sqlite3
import pdb
import json
from analyzeDeps import analyzeImports

# Open the database
conn = sqlite3.connect("githubR.db")
conn.row_factory = sqlite3.Row
conn.execute("pragma short_column_names=OFF;");
conn.execute("pragma full_column_names=ON;");

# Set up urllib2 to know my github password by default
with open("credentials.json") as f:
   credentials = json.load(f)
   git = Github(credentials["username"], credentials["password"])


# Fixed sql statements
filesColumns = "file_id, project_id, path, size, last_edit, retrieved, " +\
               "repos, cb_last_scan, error"
insertFilesSQL = "insert into files (" + filesColumns + ") values (" +\
               "?,?,?,?,?,?,?,?,?);"
importsColumns = "file_id, project_id, package_name, cb_last_scan"
insertImportsSQL = "insert into imports (" + importsColumns + ") values (" +\
               "?,?,?,?);"


def importGhtorrentProjectCsv(fname):
    """Repopulate from scratch the projects table

    The argument is filename of a csv file downloaded from
    ghtorrent.org/dblite, querying the projects table for ones
    where language=R.
    """

    rownum = 0
    with open(fname, "rb") as csvfile:
        csvreader = csv.reader(csvfile, escapechar='\\', strict=True, doublequote=False)
        hdrs = [h.strip('`') for h in csvreader.next()]
        hdrsComma = ','.join(hdrs)
        try:
            conn.execute("drop table projects;")
        except:
            pass
        createProjectsSQL = "create table projects (" + hdrsComma + ");"
        conn.execute(createProjectsSQL)
        insertProjectsSQL = "insert into projects (" + hdrsComma + ")" + \
              " values (" + ','.join(["?" for h in hdrs]) + ");"
        for row in csvreader:
            rownum = rownum + 1
            conn.execute(insertProjectsSQL, [unicode(r, "UTF-8") for r in row])
            if (rownum%1000 == 0):
                print "Wrote row ", rownum
                conn.commit()    
    conn.commit()    
    conn.execute("alter table projects add column cb_last_scan;");
    conn.execute("alter table projects add column pushed_at;");
    conn.execute("alter table projects add column forks_count;");
    conn.execute("alter table projects add column stargazers_count;");
    conn.execute("alter table projects add column watchers_count;");
    conn.execute("alter table projects add column network_count;");
    conn.execute("alter table projects add column error;");

def createOtherTables():
    try:
        conn.execute("drop table files;")
    except:
        pass
    try:
        conn.execute("drop table imports;")
    except:
        pass
    conn.execute("create table files (" + filesColumns + ");")
    conn.execute("create table imports (" + importsColumns + ");")

   
#remaining = 1
#reset = 1
#
def username(apiurl):
   return apiurl.split("/")[4]

def hasDependencyInfo(path):
   if path == "DESCRIPTION": return True
   if path.endswith(".R"): return True
   if path.endswith(".r"): return True
   return False

def queryRandomProject():
   row = getRandomProject()
   processProject(row)

def getRandomProject():
   cur = conn.cursor()
   cur.execute("select * from projects where cb_last_scan is NULL and (error is null or error = '') and deleted = '0'");
   rows = cur.fetchall()
   if len(rows) == 0:
       print "NO random project could be chosen -- none match the criterion."
       return
   randomrow = random.choice(rows)
   return randomrow

def rest():
   if (git.rate_limiting[0] < 5):
      waitseconds = git.rate_limiting_resettime - time.time()
      awaken_at = (datetime.datetime.now() + datetime.timedelta(seconds = waitseconds)).strftime("%H:%M")
      print "+---------------------------->"
      print "|Sleeping until ", awaken_at
      time.sleep(waitseconds+10)
      print "|Back to the grind!"
      print "+---------------------------->"

def processProject(projectsrow):
   rando_repo = projectsrow['projects.name']
   rando_projid = projectsrow['projects.id']
   rando_url = projectsrow['projects.url']
   user = username(rando_url)
   
   rest()
   print "Project: ", user + "/" + rando_repo, ". Ratelimit: ", \
          git.rate_limiting[0], " reads within ", (git.rate_limiting_resettime - time.time())/60, " minutes"

   error = ""
   try:
       repo = git.get_user(user).get_repo(rando_repo)
       tree = repo.get_git_tree("master", recursive=True)
   
       filenum = 1
       conn.execute("update projects set pushed_at=?, forks_count=?, watchers_count=?,stargazers_count=?,network_count=?  where id=?", \
               (str(repo.pushed_at), repo.forks_count, repo.watchers_count, repo.stargazers_count, repo.network_count, rando_projid))
       conn.execute("delete from files where project_id=?", (rando_projid,))
       conn.commit()
       for leaf in tree.tree:
           if hasDependencyInfo(leaf.path):
               print "    file ", leaf.path
               queryFile(repo, rando_projid, filenum, path=leaf.path, size=leaf.size)
               filenum += 1
               conn.commit()
   except Exception, e:
       error = str(e)[0:100]
       print "    ERROR reading project ", user, rando_repo, error
   finally:
       conn.execute("update projects set cb_last_scan=?, error=? where id=?",
           (int(time.time()), error, rando_projid))
   conn.commit()

def getCachename(user, repo, path):
       return "/".join(["cache",user, repo, path])

def queryFile(repo, project_id, file_id, path, size):
   error = ""
   retrieved = True
   rest()
   try:
       cur = conn.cursor()
       content = repo.get_contents("/" + urllib.quote(path)).decoded_content
       cachename = getCachename(repo.owner.login, repo.name, path)
       if not os.path.exists(os.path.dirname(cachename)):
           os.makedirs(os.path.dirname(cachename))
       with open(cachename, "w") as f:
           f.write(content)
       (language, imports) = analyzeImports(cachename)
       if len(imports) > 0:
           print "        imports: ", ','.join(imports)
       for imp in imports:
           conn.execute(insertImportsSQL, (file_id, project_id, imp, int(time.time())))
   except Exception, e:
       error = str(e)[0:100]
       retrieved = False
       print "        ERROR reading file: ", repo.owner.login, repo.name, path, error
   finally:
       conn.execute(insertFilesSQL,
               (file_id, project_id, path,
                size, None, retrieved, "", int(time.time()), error))
   
def fillInLastDate():
    """Fills in backlog after I added these columns; probably never needed again."""
    try:
        cur = conn.cursor()
        cur.execute("select * from projects where cb_last_scan is not NULL and (error is null or error = '') and (stargazers_count is null) limit 1");
        rows = cur.fetchall()
        for row in rows:
            url = row['projects.url']
            repo_name = row['projects.name']
            user = username(url)
            repo = git.get_user(user).get_repo(repo_name)
            print "Fixing project ", user, repo_name, "to", str(repo.pushed_at), repo.stargazers_count, repo.watchers_count
            conn.execute("update projects set pushed_at=?, forks_count=?, watchers_count=?,stargazers_count=?,network_count=?  where id=?", \
               (str(repo.pushed_at), repo.forks_count, repo.watchers_count, repo.stargazers_count, repo.network_count, row['projects.id']))
            conn.commit()
    except Exception, e:
        print str(e)
    print git.rate_limiting[0], " reads within ", (git.rate_limiting_resettime - time.time())/60, " minutes"
            

if "__main__" == __name__:
    #os.system("rm -rf cache")
    #importGhtorrentProjectCsv("ghtorrent.csv")
    #createOtherTables()
    for _ in range(700):
        queryRandomProject()
    
