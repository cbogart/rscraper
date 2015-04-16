import csv
import traceback
import time
# you need easy_install PyGithub or pip install PyGithub for this
from github import Github, UnknownObjectException
import os
import random
import datetime
import urllib
from utils import *
from analyzeDeps import analyzeImports, parseDESCRIPTION
import pdb

# Fixed sql statements
filesColumns = "file_id, project_id, path, size, last_edit, retrieved, " +\
               "repos, cb_last_scan, error"
insertFilesSQL = "insert into gitfiles (" + filesColumns + ") values (" +\
               "?,?,?,?,?,?,?,?,?);"
importsColumns = "file_id, project_id, package_name, cb_last_scan"
insertImportsSQL = "insert into gitimports (" + importsColumns + ") values (" +\
               "?,?,?,?);"
projectsColumns = r"""id,url,owner_id,name,description,language,created_at,ext_ref_id,
                  forked_from,deleted,cb_last_scan,error,pushed_at,network_count,
                  watchers_count,stargazers_count,forks_count,owner,ownertype"""
insertProjectsColumns = "insert into gitprojects (" + projectsColumns + ") values (" +\
                  ','.join(["?" for fld in projectsColumns.split(",")]) + ")"

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
        conn.execute("alter table gitprojects add column owner;");
        conn.execute("alter table gitprojects add column ownertype;");
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



class GitProjectInfo:
    def __init__(self, name, project_id, url, gitprojname = None, descpath = None):
        self.name = name
        self.gitprojname = self.name if gitprojname is None else gitprojname
        self.project_id = project_id
        self.url = url
        self.descpath = descpath
    def __str__(self):
        return self.username() + "/" + self.gitprojname
    def username(self):
        return self.url.split("/")[4]
    def cachefilename(self, path):
        return getCachename(self.username(), self.gitprojname, path)
    def projectDescription(self):
        if self.descpath is None:
            self.descpath = "DESCRIPTION"
        try:
            with open(self.cachefilename(self.descpath), "r") as f:
                desc = parseDESCRIPTION(f.readlines())
                return desc[desc.keys()[0]]
        except IOError, e:
            try:
                with open(self.cachefilename("pkg/DESCRIPTION"), "r") as f:
                    desc = parseDESCRIPTION(f.readlines())
                    return desc[desc.keys()[0]]
                print "THIS SHOULD NEVER BE CALLED ANYMORE"
                
            except IOError, e:
                #pdb.set_trace()
                print "Error in getting project description: ", self.cachefilename(self.descpath), str(e)
                return { "error": str(e)}
        except Exception, e:
            # pdb.set_trace()
            print "Error getting project description: ", self.cachefilename(self.descpath), str(e)
            return { "error": str(e)}

# Cache the git object between calls
git = None
def gitInit(credentials):
   global git
   if (git is None):
       git = Github(credentials["username"], credentials["password"], per_page=100)
    
    
def identifyNewProjects(conn, creds, thedate):
    gitInit(creds)
    # Find list of existing project ids, so we can exclude readding them
    urls = conn.execute("select url, pushed_at from gitprojects;")
    urlslist = { ident["gitprojects.url"]: ident["gitprojects.pushed_at"] for ident in urls }
    assert "https://api.github.com/repos/0xack13/RSketch" in urlslist, "Did not read idlist correctly"
    
    # Query for the next ones
    throttleGitAccess(git, margin=10)
    repos = git.search_repositories("pushed:" + thedate + " language:R", )
    insertRepos(repos,conn,urlslist)
    
def insertRepos(repos, conn, excludeUrls):
    throttleGitAccess(git, margin=10)
    for repo in repos:
        throttleGitAccess(git, margin=10)
        fullname = repo.owner.login + "/" + repo.name
        if repo.url not in excludeUrls:
            print "Inserting:",  fullname, "created", repo.created_at
            conn.execute(insertProjectsColumns, 
                 (repo.id,
                  repo.url,
                  repo.owner.id,
                  repo.name,
                  repo.description,
                  repo.language,
                  repo.created_at,
                  None,   # ext_ref_id <- This is something relevant to ghtorrent; has no meaning here
                  "0" if repo.fork else "",
                  "0",   # Deleted.  PResumably it's not deleted if it showed up here. repo.deleted,
                  None,   # cb_last_scan <- we'll fill this date in when we scan the actual files
                  None,   # error <- ditto
                  repo.pushed_at,
                  repo.network_count,
                  repo.watchers_count,
                  repo.stargazers_count,
                  repo.forks_count,
                  repo.owner.login,
                  repo.owner.type \
                  ))
        elif repo.url in excludeUrls and ymdhms2epoch(str(repo.pushed_at)) > ymdhms2epoch(excludeUrls[repo.url]) + (7*24*3600):
            print "Marking", fullname, "for update because", repo.pushed_at, ">", excludeUrls[repo.url]
            conn.execute("update gitprojects set cb_last_scan='' where url=?;", (repo.url,))
        else:
            print "Skipping", fullname
        conn.commit()
    
def queryRandomProject(conn, credentials):
    projinf = getRandomProject(conn)
    gitInit(credentials)
    populateProjectMetadata(projinf, conn, git)

def queryParticularProject(conn, credentials, user_slash_name):
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
    gitInit(credentials)
    populateProjectMetadata(projinf, conn, git)

class CaughtUpException(Exception):
    pass

def getRandomProject(conn):
    cur = conn.cursor()
    cur.execute("select * from gitprojects where cb_last_scan is NULL and (error is null or error = '') and deleted = '0'");
    rows = cur.fetchall()
    if len(rows) == 0:
        raise CaughtUpException("NO random project could be chosen -- none match the criterion.")
    if (len(rows) % 50 == 0):
        print "\t", len(rows), " projects remain at", datetime.datetime.now().isoformat(), "*********   ************   **********"
    randomrow = random.choice(rows)
    return GitProjectInfo(randomrow['gitprojects.name'], randomrow['gitprojects.id'], randomrow['gitprojects.url'])

def throttleGitAccess(git, margin=75):
    if (git.rate_limiting[0] < margin):
        waitseconds = git.rate_limiting_resettime - time.time()
        awaken_at = (datetime.datetime.now() + datetime.timedelta(seconds = waitseconds)).strftime("%H:%M")
        print "Waitseconds = ", waitseconds, "ratelimiting=", git.rate_limiting
        print "+---------------------------->"
        print "|Sleeping until ", awaken_at
        time.sleep(waitseconds+10)
        print "|Back to the grind!"
        print "+---------------------------->"

def getProjectMetadata(projinf, git):
    repo = git.get_user(projinf.username()).get_repo(projinf.name)
    tree = repo.get_git_tree("master", recursive=True)
    return {"repo": repo, "tree": tree}


def backfillOwnerType(credentials, conn):
    gitInit(credentials)
    cur = conn.cursor()
    cur.execute(r"""
       select distinct owner from gitprojects 
       where 
          ownertype = "Unknown" and 
          id in (select project_id from gitfiles where path like "%DESCRIPTION");
        """);
    rows = cur.fetchall()
    print "Searching", len(rows), "Github users"
    otypes = {}
    try:
        for row in rows:
            name = row["gitprojects.owner"]
            throttleGitAccess(git)
            
            # Hard-coded exception: rforge is registered as a user,
            # but it's major, and I know better
            if name == "rforge":
                otypes[name] = "Organization"
            else:
                try:
                    owner = git.get_user(name)
                    otypes[name] = owner.type
                except UnknownObjectException:
                    print "Skipping unknown user", name
                    otypes[name]="missing"
            print name, ":", otypes[name]
                
    except Exception, e:
        print "Error", e
    finally:
        print "Updating", len(otypes), "records"
        cur.executemany("update gitprojects set ownertype=? where owner=?",
                [(otypes[name], name) for name in otypes])
        conn.commit()
        print "Successful commit"

#
#  Note: watchers_count is obsolete, per https://developer.github.com/changes/2012-9-5-watcher-api/
#   Instead, we should look at subscribers_count
#    example: 
#      https://api.github.com/repos/hadley/adv-r
#
#  However, I'm currently not using watchers_count, but stargazers_count instead FWIW,
#  and the backlog of data collected therefore has watchers, so I am 
#  not going to change it for now.
#    cb 3/9/2015
#
def saveProjectMetadata(projinf, projmeta, conn):
    conn.execute("update gitprojects set owner=?, ownertype=?, pushed_at=?, forks_count=?, watchers_count=?,stargazers_count=?,network_count=?  where id=?", \
               (projinf.username(), projmeta["repo"].owner.type,
                str(projmeta["repo"].pushed_at), projmeta["repo"].forks_count, projmeta["repo"].watchers_count, \
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
       content = repo.get_contents("/" + urllib.quote(path.encode('utf-8'))).decoded_content
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
       conn.execute(insertImportsSQL, (filenum, projinf.project_id, imp.strip(), int(time.time())))
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


