import json
import pdb
import re
import sqlite3
import time
import urllib2
import urllib
from analyzeDeps import parseDESCRIPTION
from bs4 import BeautifulSoup

def unquote(x):
    if (x.startswith('"') and x.endswith('"')):
        return x[1:-1]
    else:
        return x

def do_or_error(f, msg=None):
    try:
        return f()
    except Exception, e:
        return msg or str(e)[0:50]

def getBioconductorWebscrape(limit = 99999):
    categories = {}

    index = BeautifulSoup(urllib2.urlopen("http://www.bioconductor.org/packages/release/bioc/").read())
    packages = index.find("div", class_="do_not_rebase").find_all("a")
    for p in packages[:limit]:
        url = p.get("href")
        name = p.get_text()
        fullurl = "http://www.bioconductor.org/packages/release/bioc/" + url
        detail = BeautifulSoup(urllib2.urlopen(fullurl).read())
        views = detail.find("td", text="biocViews").find_parent().find_all("a")
        viewlist = [v.get_text() for v in views]
        #citation = do_or_error(lambda: detail.find("div", id="bioc_citation").get_text())
        citation = do_or_error(lambda: scrapeCitationBioc(name), msg="")
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
    citeurl = "http://cran.r-project.org/web/packages/" + urllib.quote(name) + "/citation.html"
    print citeurl
    citepage = BeautifulSoup(urllib2.urlopen(citeurl).read())
    return citepage.find("blockquote").find("p").get_text().replace("\n","").strip()

def getCranWebscrape(limit=9999999):
    categories = {}
    
    index = BeautifulSoup(urllib2.urlopen("http://cran.r-project.org/web/packages/available_packages_by_name.html").read())
    packages = index.find("table").find_all("a")
    for p in packages[:limit]:
        url = p.get("href")
        name = p.get_text()
        title = do_or_error(lambda: p.find_parent().find_parent().find_all("td")[-1].get_text())
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
    try:
        conn.execute("drop table %(tb)s;" % {"tb":table} )
    except Exception, e:
        print "ERROR", str(e)
    exc = "create table %(tb)s ( %(flds)s );" % {"tb":table, "flds": flds}
    conn.execute(exc)
    conn.commit()
        
def createMetadataTables(conn):
    recreateTable(conn, "tags", "package_id integer, tag string")
    recreateTable(conn, "ties", "package_id integer, tied_id integer, relationship string")
    recreateTable(conn, "packages", "package_id integer primary key, name string, repository string, " \
                              "url string, " +\
                              "title string, description string, lastversion string, " \
                              "unique(name, repository, url)  on conflict replace")
    recreateTable(conn, "citations", "package_id integer, name string, citation string, canonical boolean")


def saveMetadata(pkgDescription, pkgWebscrape, conn):
    for rec in pkgWebscrape:

        url = pkgDescription[rec].get("URL", [""])
        if not isinstance(url, str):  url = url[0]
        if url == "": url = pkgWebscrape[rec].get("url", "")
        if "/api.github" in url:
            url = "http://github.com/" + pkgWebscrape[rec]["user"] + "/" + rec

        #print url, pkgDescription[rec].get("URL", "?"), pkgWebscrape.get("URL", "")
        #pdb.set_trace()

        conn.execute("insert or ignore into packages (name, repository, url) values (?,?,?)", 
                     (rec, pkgWebscrape[rec]["repository"], url))
        conn.execute("update packages set " + 
                "title=?, description=? where name=? and repository=? and url=?;", 
                 (pkgWebscrape[rec]["title"], 
                 pkgWebscrape[rec]["description"], 
                  rec, pkgWebscrape[rec]["repository"], url))
        if rec in pkgDescription:
            try:
                version = pkgDescription[rec].get("Version", [""])
                if isinstance(version, basestring): version = ""
                elif len(version) == 0: version = ""
                else: version = version[0]
                conn.execute("update packages set " + 
                    "lastversion=? where name=? and repository=? and url=?", 
                     (version, rec, pkgWebscrape[rec]["repository"],url))
            except Exception, e:
                pdb.set_trace()
                print "Could not write package version information"
        conn.commit()

def getCranDescription():
    directory = "http://cran.r-project.org/src/contrib/PACKAGES"
    txt = urllib.urlopen(directory).readlines()
    return parseDESCRIPTION(txt)

def getBioconductorDescription():
    directory = "http://bioconductor.org/packages/3.0/bioc/src/contrib/PACKAGES"
    txt = urllib.urlopen(directory).readlines()
    return parseDESCRIPTION(txt)
