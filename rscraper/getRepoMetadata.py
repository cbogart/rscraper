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

def getBioconductorWebscrape():
    categories = {}

    index = BeautifulSoup(urllib2.urlopen("http://www.bioconductor.org/packages/release/bioc/").read())
    packages = index.find("div", class_="do_not_rebase").find_all("a")
    for p in packages[:5]:
        url = p.get("href")
        name = p.get_text()
        fullurl = "http://www.bioconductor.org/packages/release/bioc/" + url
        detail = BeautifulSoup(urllib2.urlopen(fullurl).read())
        views = detail.find("td", text="biocViews").find_parent().find_all("a")
        viewlist = [v.get_text() for v in views]
        #citation = do_or_error(lambda: detail.find("div", id="bioc_citation").get_text())
        citation = do_or_error(lambda: scrapeCitationBioc(name))
        titleparent = do_or_error(lambda: detail.find("h1").find_parent())
        title = do_or_error(lambda: titleparent.find("h2").get_text())
        description = do_or_error(lambda: titleparent.find_all("p")[1].get_text())
        print name, url, '/'.join(viewlist)
        categories[name] = { "url": fullurl, "repository": "bioconductor", "views": viewlist, "citation": citation, "title": title, "description": description }

    return categories

def scrapeCitationBioc(name):
    citeurl = "http://bioconductor.org/packages/release/bioc/citations/" + urllib.quote(name) + "/citation.html"
    print citeurl
    citepage = BeautifulSoup(urllib2.urlopen(citeurl).read())
    return citepage.get_text()

def scrapeCitationCran(name):
    citeurl = "http://cran.r-project.org/packages/release/bioc/citations/" + urllib.quote(name) + "/citation.html"
    print citeurl
    citepage = BeautifulSoup(urllib2.urlopen(citeurl).read())
    return citepage.get_text()

def getCranWebscrape():
    categories = {}
    
    index = BeautifulSoup(urllib2.urlopen("http://cran.r-project.org/web/packages/available_packages_by_name.html").read())
    packages = index.find("table").find_all("a")
    for p in packages[:5]:
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
        citation = do_or_error(lambda: scrapeCitationCran(name))
        categories[name] = { "url": fullurl, "repository": "cran", "views": viewlist, "citation": citation, "title": title, "description": description }

    return categories

def recreateTable(conn, table, flds):
    print "----", table
    try:
        conn.execute("drop table %(tb)s;" % {"tb":table} )
    except Exception, e:
        print "ERROR", str(e)
    exc = "create table %(tb)s ( %(flds)s );" % {"tb":table, "flds": flds}
    print exc
    conn.execute(exc)
    conn.commit()
        
def createMetadataTables(conn):
    recreateTable(conn, "tags", "package_id integer, tag string")
    recreateTable(conn, "ties", "package_id integer, tied_id integer, relationship string")
    recreateTable(conn, "packages", "package_id integer primary key, name string, repository string, " \
                              "url string, " +\
                              "title string, description string, lastversion string, " \
                              "unique(name, repository)  on conflict replace")
    recreateTable(conn, "citations", "package_id integer, name string, citation string, canonical boolean")


# Packages table: unique for: package URL.  There may be multiple sites for a project, e.g. a CRAN and 15 github projects with that name.
#  That's OK.  The "best" github is one without a fork, and then I guess just pick the most-forked one.
#  Cran beats Bioc beats Github.  Github many-forks beats github no-forks beats github forked, when exporting canonicals, but they're all listed

#
#  pkgWebscrape has for each package:
#     citation, title, description, views
#  pkgDescription has
#     License, Package, Imports, MD5sum, Depends, Version, NeedsCompilation, etc.
def saveMetadata(pkgDescription, pkgWebscrape, conn):
    for rec in pkgWebscrape:
        import pdb
        conn.execute("insert or ignore into packages (name, repository) values (?,?)", 
                     (rec, pkgWebscrape[rec]["repository"]))
        conn.execute("update packages set " + 
                "url = ?, title=?, description=? where name=? and repository=?;", 
                 (pkgWebscrape[rec]["url"], pkgWebscrape[rec]["title"], 
                 pkgWebscrape[rec]["description"], 
                  rec, pkgWebscrape[rec]["repository"]))
        if rec in pkgDescription:
            conn.execute("update packages set " + 
                "lastversion=? where name=? and repository=?", 
                 (pkgDescription[rec].get("Version", [""])[0],
                  rec, pkgWebscrape[rec]["repository"]))
        conn.commit()

    
