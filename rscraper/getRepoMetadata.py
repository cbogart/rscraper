import json
from bs4 import BeautifulSoup
import sqlite3
import urllib2
import urllib
import time

def unquote(x):
    if (x.startswith('"') and x.endswith('"')):
        return x[1:-1]
    else:
        return x

def do_or_error(f):
    try:
        return f()
    except Exception, e:
        return str(e)[0:50]

def getBioconductorMetadata():
    categories = {}

    index = BeautifulSoup(urllib2.urlopen("http://www.bioconductor.org/packages/release/bioc/").read())
    packages = index.find("div", class_="do_not_rebase").find_all("a")
    for p in packages:
        url = p.get("href")
        name = p.get_text()
        fullurl = "http://www.bioconductor.org/packages/release/bioc/" + url
        detail = BeautifulSoup(urllib2.urlopen(fullurl).read())
        views = detail.find("td", text="biocViews").find_parent().find_all("a")
        viewlist = [v.get_text() for v in views]
        citation = do_or_error(lambda: detail.find("div", id="bioc_citation").get_text())
        titleparent = do_or_error(lambda: detail.find("h1").find_parent())
        title = do_or_error(lambda: titleparent.find("h2").get_text())
        description = do_or_error(lambda: titleparent.find_all("p")[1].get_text())
        print name, url, '/'.join(viewlist)
        categories[name] = { "url": fullurl, "repos": "bioconductor", "views": viewlist, "citation": citation, "title": title, "description": description }

    return categories


def getCranMetadata():
    categories = {}
    
    index = BeautifulSoup(urllib2.urlopen("http://cran.r-project.org/web/packages/available_packages_by_name.html").read())
    packages = index.find("table").find_all("a")
    for p in packages:
        url = p.get("href")
        name = p.get_text()
        title = do_or_error(lambda: p.find_parent().find_parent().find_all("td")[2].get_text())
        fullurl = "http://cran.r-project.org/web/packages/" + name + "/index.html"
        detail = BeautifulSoup(urllib2.urlopen(fullurl).read())
        try:
            views = detail.find("td", text=re.compile(r'In.*views')).find_parent().find_all("a")
            viewlist = [v.get_text() for v in views]
        except:
            viewlist = []
        print name, fullurl, '/'.join(viewlist)
        description = do_or_error(lambda: detail.find("p").get_text())
        citation = do_or_error(lambda: {
                      citepage = BeautifulSoup(urllib2.urlopen("http://cran.r-project.org/web/packages/" + name + "/citation.html").read())
                      return citepage.find("blockquote").get_text()
                  })
        categories[name] = { "url": fullurl, "repos": "cran", "views": viewlist, "citation": citation, "title": title, "description": description }

    return categories

def recreateTable(conn, table, flds):
    try:
        conn.execute("drop table %(tb)s;" % {"table":table} )
    except:
        pass
    conn.execute("create table %(tb)s ( %(flds)s );" % {"tb":table, "flds": flds})
    conn.commit()
        
def createMetadataTables(conn):
    recreateTable("tags", "package_id as integer, tag as string")
    recreateTable("packages", "package_id as integer, name as string, repository as string, url as string, " +\
                              "title as string, description as string, lastversion as string")
    recreateTable("citations", "package_id as integer, name as string, citation as string, canonical as boolean")


# Packages table: unique for: package URL.  There may be multiple sites for a project, e.g. a CRAN and 15 github projects with that name.
#  That's OK.  The "best" github is one without a fork, and then I guess just pick the most-forked one.
#  Cran beats Bioc beats Github.  Github many-forks beats github no-forks beats github forked, when exporting canonicals, but they're all listed

def saveMetadata(pkgMetadata, pkgPackageInfo, conn):
    for rec in categories:
        pairs = [(rec, categories[rec]["repos"])]
        conn.execute("insert or ignore into packages ("
        for v in categories[rec]["views"]:
            pairs.append( (rec, v) )
        conn.executemany("insert into repositories (name, tag) values (?,?);", pairs)  
        conn.commit()

    
