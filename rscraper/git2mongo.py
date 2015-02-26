import csv
from pprint import pprint
import time
import calendar
import sqlite3
import pdb
import json
from analyzeDeps import analyzeImportsManyDescriptions
from analyzeDeps import calcDependencyClosure

# Open the database
conn = sqlite3.connect("githubR.bak.db")
conn.row_factory = sqlite3.Row
conn.execute("pragma short_column_names=OFF;");
conn.execute("pragma full_column_names=ON;");

# Fixed sql statements
filesColumns = "file_id, project_id, path, size, last_edit, retrieved, " +\
               "repos, cb_last_scan, error"
insertFilesSQL = "insert into files (" + filesColumns + ") values (" +\
               "?,?,?,?,?,?,?,?,?);"
importsColumns = "file_id, project_id, package_name, cb_last_scan"
insertImportsSQL = "insert into imports (" + importsColumns + ") values (" +\
               "?,?,?,?);"


# Preexisting dependencies
biocPackages = analyzeImportsManyDescriptions(open("bioc-PACKAGES.txt").readlines())
cranPackages = analyzeImportsManyDescriptions(open("cran-PACKAGES.txt").readlines())
packages = dict(biocPackages.items() + cranPackages.items())

def username(apiurl):
   return apiurl.split("/")[4]

def nodots(k): return k.replace(".","[dot]")

def exportProjects():
   cur = conn.cursor()
   cur.execute("select * from projects where cb_last_scan is not NULL and (error is null or error = '')");
   prjrows = cur.fetchall()
   for prjrow in prjrows:
       user = username(prjrow['projects.url'])
   
       cur2 = conn.cursor()
       cur2.execute("select distinct(package_name) as imp from imports where project_id=?;", (prjrow["projects.id"],))
       importrows = cur2.fetchall()
       
       importlist = [ir['imp'] for ir in importrows]
       importdict = calcDependencyClosure(importlist, packages)
       
       startTime = time.strptime(str(prjrow['projects.pushed_at']),"%Y-%m-%d %H:%M:%S")
       record = { "scimapInfoVersion": 3,
                  "exec": nodots(user + "/" + prjrow['projects.name']),
                  "pkgT": importdict,
                  "user": user,
                  "jobID": user + "/" + prjrow['projects.name'],
                  "platform" : { "hardware" : "unknown", "version": "unknown", "system": "unknown"},
                  "startEpoch": calendar.timegm(startTime),
                  "startTime": prjrow['projects.pushed_at'] }
       print json.dumps(record)

if "__main__" == __name__:
    exportProjects()
