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

# Grab whatever online stuff gives a basic package list/minimal metadata and put it in this filename
# Git:  search list of (new?) packages, OR use ghtorrent.
# CRAN: PACKAGES.txt
def downloadListing(listingCache, style):
        if style == "github":
            print "https://api.github.com/search/repositories?q=created:%3E2015-02-13%20language:R"
        elif style == "ghtorrent":
            print "query ghtorrent site here"
        print "write to ", listingCache" 

def importGhtorrentProjectCsv(fname, conn):
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

def createGitTables(conn):
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
def hasDependencyInfo(path):
   if path == "DESCRIPTION": return True
   if path.endswith(".R"): return True
   if path.endswith(".r"): return True
   return False


# Fixed sql statements
filesColumns = "file_id, project_id, path, size, last_edit, retrieved, " +\
               "repos, cb_last_scan, error"
insertFilesSQL = "insert into files (" + filesColumns + ") values (" +\
               "?,?,?,?,?,?,?,?,?);"
importsColumns = "file_id, project_id, package_name, cb_last_scan"
insertImportsSQL = "insert into imports (" + importsColumns + ") values (" +\
               "?,?,?,?);"

class GitProjectInfo:
   def __init__(self, name, project_id, url):
       self.name = name
       self.project_id = project_id
       self.url = url
   def username(self):
       return self.url.split("/")[4]

# Cache the git object between calls
git = None
def queryRandomProject(credentials):
   global git
   projinf = getRandomProject()
   if (git is None):
       git = Github(credentials["username"], credentials["password"])
   populateProjectMetadata(projinf, conn, git)

def getRandomProject(conn):
   cur = conn.cursor()
   cur.execute("select * from projects where cb_last_scan is NULL and (error is null or error = '') and deleted = '0'");
   rows = cur.fetchall()
   if len(rows) == 0:
       print "NO random project could be chosen -- none match the criterion."
       return
   randomrow = random.choice(rows)
   return GitProjectInfo(row['projects.name'], row['projects.id'], row['projects.url'])

def throttleGitAccess(git):
   if (git.rate_limiting[0] < 5):
      waitseconds = git.rate_limiting_resettime - time.time()
      awaken_at = (datetime.datetime.now() + datetime.timedelta(seconds = waitseconds)).strftime("%H:%M")
      print "+---------------------------->"
      print "|Sleeping until ", awaken_at
      time.sleep(waitseconds+10)
      print "|Back to the grind!"
      print "+---------------------------->"

def getProjectMetadata(projinf, git):
    repo = git.get_user(projinf.username()).get_repo(projinf.name)
    tree = repo.get_git_tree("master", recursive=True)
    return {"repo": repo, "tree": tree}

def saveProjectMetadata(projinf, projmeta, conn):
    conn.execute("update projects set pushed_at=?, forks_count=?, watchers_count=?,stargazers_count=?,network_count=?  where id=?", \
               (str(projmeta["repo"].pushed_at), projmeta["repo"].forks_count, projmeta["repo"].watchers_count, \
               projmeta["repo"].stargazers_count, projmeta["repo"].network_count, projinf.project_id))
    conn.execute("delete from files where project_id=?", (projinf.project_id,))
    conn.commit()

def queryFile(repo, projinf, path)
   error = ""
   try:
       content = repo.get_contents("/" + urllib.quote(path)).decoded_content
       cachename = getCachename(repo.owner.login, repo.name, path)
       if not os.path.exists(os.path.dirname(cachename)):
           os.makedirs(os.path.dirname(cachename))
       with open(cachename, "w") as f:
           f.write(content)
       (language, imports) = analyzeImports(cachename)
   except Exception, e:
       error = str(e)[0:100]
       print "    ERROR reading ", path, projinf.username(), projinf.name, error
   return {"language": language, "imports": imports, "error": error }

def saveFileImportInfo(projinf, fileinf, leaf, conn, filenum)
   for imp in fileinf["imports"]:
       conn.execute(insertImportsSQL, (filenum, projinf.project_id, imp, int(time.time())))
   conn.execute(insertFilesSQL,
       (filenum, projinf.project_id, fileinf["path"], leaf.size, None, retrieved, "", int(time.time()), fileinf["error"]))
   
def updateProjectScanStatus(projinf, error, conn):
   conn.execute("update projects set cb_last_scan=?, error=? where id=?",
       (int(time.time()), error, projinf.project_id))

def populateProjectMetadata(projinf, conn, git):
   throttleGitAccess(git)
   error = ""
   try:
       projmeta = getProjectMetadata(projinf, git)
       saveProjectMetadata(projinf, projmeta, conn)
       filenum = 1
       for leaf in tree.tree:
           if hasDependencyInfo(leaf.path):
               print "    file ", leaf.path
               fileinf = queryFile(projmeta["repo"], projinf, leaf.path) 
               safeFileInfo(projinf, fileinf, leaf, conn, filenum)
               filenum += 1
   except Exception, e:
       error = str(e)[0:100]
       print "    ERROR reading project ", projinf.username(), projinf.name, error
   finally:
       updateProjectScanStatus(projinf, error, conn)
   

def getCachename(user, repo, path):
       return "/".join(["cache",user, repo, path])

