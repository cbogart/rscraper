import csv
import datetime
import traceback
import sys
import time
import datetime
# you need easy_install PyGithub or pip install PyGithub for this
from github import Github, UnknownObjectException
import os
import random
import urllib
import urllib2
import sys
import sqlite3
import pdb
import json
from analyzeDeps import analyzeImports, parseDESCRIPTION

# Grab whatever online stuff gives a basic package list/minimal metadata and put it in this filename
# Git:  search list of (new?) packages, OR use ghtorrent.
# CRAN: PACKAGES.txt
def downloadListing(listingCache, style):
        if style == "github":
            print "https://api.github.com/search/repositories?q=created:%3E2015-02-13%20language:R"
        elif style == "ghtorrent":
            print "query ghtorrent site here"
        print "write to ", listingCache 

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
                conn.execute("drop table gitprojects;")
            except:
                pass
            createProjectsSQL = "create table gitprojects (" + hdrsComma + ");"
            conn.execute(createProjectsSQL)
            insertProjectsSQL = "insert into gitprojects (" + hdrsComma + ")" + \
                  " values (" + ','.join(["?" for h in hdrs]) + ");"
            for row in csvreader:
                rownum = rownum + 1
                conn.execute(insertProjectsSQL, [unicode(r, "UTF-8") for r in row])
                if (rownum%1000 == 0):
                    print "Wrote row ", rownum
                    conn.commit()    
        conn.commit()    
        conn.execute("alter table gitprojects add column cb_last_scan;");
        conn.execute("alter table gitprojects add column pushed_at;");
        conn.execute("alter table gitprojects add column forks_count;");
        conn.execute("alter table gitprojects add column stargazers_count;");
        conn.execute("alter table gitprojects add column watchers_count;");
        conn.execute("alter table gitprojects add column network_count;");
        conn.execute("alter table gitprojects add column error;");

def createGitTables(conn):
    try:
        conn.execute("drop table gitfiles;")
    except:
        pass
    try:
        conn.execute("drop table gitimports;")
    except:
        pass
    conn.execute("create table gitfiles (" + filesColumns + ");")
    conn.execute("create table gitimports (" + importsColumns + ");")

   
#remaining = 1
#reset = 1
#
def hasDependencyInfo(path):
   if path.split("/")[-1] == "DESCRIPTION": return True
   if path.endswith(".R"): return True
   if path.endswith(".r"): return True
   return False


# Fixed sql statements
filesColumns = "file_id, project_id, path, size, last_edit, retrieved, " +\
               "repos, cb_last_scan, error"
insertFilesSQL = "insert into gitfiles (" + filesColumns + ") values (" +\
               "?,?,?,?,?,?,?,?,?);"
importsColumns = "file_id, project_id, package_name, cb_last_scan"
insertImportsSQL = "insert into gitimports (" + importsColumns + ") values (" +\
               "?,?,?,?);"

class GitProjectInfo:
   def __init__(self, name, project_id, url):
       self.name = name
       self.project_id = project_id
       self.url = url
   def __str__(self):
       return self.username() + "/" + self.name
   def username(self):
       return self.url.split("/")[4]
   def cachefilename(self, path):
       return getCachename(self.username(), self.name, path)
   def projectDescription(self):
       try:
           with open(self.cachefilename("DESCRIPTION"), "r") as f:
               return parseDESCRIPTION(f.readlines())
       except Exception, e:
           print "Error getting project description: ", self.cachefilename("DESCRIPTION"), str(e)
           return {"error": str(e)}

# Cache the git object between calls
git = None
def queryRandomProject(conn, credentials):
   global git
   projinf = getRandomProject(conn)
   if (git is None):
       git = Github(credentials["username"], credentials["password"])
   populateProjectMetadata(projinf, conn, git)

def queryParticularProject(conn, credentials, user_slash_name):
   global git
   cur = conn.cursor()
   cur.execute('select * from gitprojects where url like "%' + user_slash_name + '%";')
   rows = cur.fetchall()
   if (len(rows) != 1):
       print "Found", len(rows), ", not 1, projects matching ", user_slash_name
       print "Aborting."
       return
   r1 = rows[0]
   id = r1["gitprojects.id"]
   print "Updating project", id
   url = r1["gitprojects.url"]
   name = r1["gitprojects.name"]
   conn.execute("update gitprojects set cb_last_scan = null, error='' where id=?;", (id,));
   conn.execute("delete from gitfiles where project_id = ?", (id,))
   conn.execute("delete from gitimports where project_id = ?", (id,))
   conn.commit()
   projinf = GitProjectInfo(name, id, url)
   if (git is None):
       git = Github(credentials["username"], credentials["password"])
   populateProjectMetadata(projinf, conn, git)

def getRandomProject(conn):
   cur = conn.cursor()
   cur.execute("select * from gitprojects where cb_last_scan is NULL and (error is null or error = '') and deleted = '0'");
   rows = cur.fetchall()
   if len(rows) == 0:
       print "NO random project could be chosen -- none match the criterion."
       return
   if (len(rows) % 50 == 0):
       print "\t", len(rows), " projects remain at", datetime.datetime.now().isoformat(), "*********   ************   **********"
   randomrow = random.choice(rows)
   return GitProjectInfo(randomrow['gitprojects.name'], randomrow['gitprojects.id'], randomrow['gitprojects.url'])

def throttleGitAccess(git):
   if (git.rate_limiting[0] < 75):
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
    conn.execute("update gitprojects set pushed_at=?, forks_count=?, watchers_count=?,stargazers_count=?,network_count=?  where id=?", \
               (str(projmeta["repo"].pushed_at), projmeta["repo"].forks_count, projmeta["repo"].watchers_count, \
               projmeta["repo"].stargazers_count, projmeta["repo"].network_count, projinf.project_id))
    conn.execute("delete from gitfiles where project_id=?", (projinf.project_id,))
    conn.commit()

def readCachedFile(user, project_name, path):
   cachename = getCachename(user, project_name, path)
   with open(cachename, "r") as f:
       return f.read()

def queryFile(repo, projinf, path, git):
   error = ""
   cachename = ""
   language = ""
   imports = []
   try:
       throttleGitAccess(git)
       content = repo.get_contents("/" + urllib.quote(path)).decoded_content
       cachename = getCachename(repo.owner.login, repo.name, path)
       if (not path.endswith("DESCRIPTION")):
           cachename = "/tmp/temp.r"
       if not os.path.exists(os.path.dirname(cachename)):
           os.makedirs(os.path.dirname(cachename))
       with open(cachename, "w") as f:
           f.write(content)
       (language, imports) = analyzeImports(cachename)
   except UnknownObjectException, e:
       error = str(e.status) + ": " + e.data["message"]
       print "    ERROR reading ", path, projinf.username(), projinf.name, error
   except Exception, e:
       error = str(e)[0:100]
       print "    ERROR reading ", path, projinf.username(), projinf.name, error
       print traceback.format_exc()
   return {"language": language, "imports": imports, "error": error, "cache": cachename }

def saveFileImportInfo(projinf, fileinf, leaf, conn, filenum):
   for imp in fileinf["imports"]:
       conn.execute(insertImportsSQL, (filenum, projinf.project_id, imp, int(time.time())))
   conn.execute(insertFilesSQL,
       (filenum, projinf.project_id, leaf.path, leaf.size, None, 1 if fileinf["error"] == "" else 0, 
        "", int(time.time()), fileinf["error"]))
   
def updateProjectScanStatus(projinf, error, conn):
   conn.execute("update gitprojects set cb_last_scan=?, error=? where id=?",
       (int(time.time()), error, projinf.project_id))
   conn.commit()

def populateProjectMetadata(projinf, conn, git):
   throttleGitAccess(git)
   print "Scanning ", str(projinf)
   error = ""
   try:
       projmeta = getProjectMetadata(projinf, git)
       saveProjectMetadata(projinf, projmeta, conn)
       filenum = 1
       for leaf in projmeta["tree"].tree:
           if hasDependencyInfo(leaf.path):
               print "    file ", leaf.path
               fileinf = queryFile(projmeta["repo"], projinf, leaf.path, git) 
               saveFileImportInfo(projinf, fileinf, leaf, conn, filenum)
               if (fileinf["error"] != ""): error = fileinf["error"]
               filenum += 1
   except UnknownObjectException, e:
       error = str(e.status) + ": " + e.data["message"]
       print "    ERROR reading project ", projinf.username(), projinf.name, error
   except Exception, e:
       error = str(e)[0:100]
       print "    ERROR reading project ", projinf.username(), projinf.name, error
       print traceback.format_exc()
   finally:
       updateProjectScanStatus(projinf, error, conn)
   

def getCachename(user, repo, path):
       return "/".join(["cache",user, repo, path])


