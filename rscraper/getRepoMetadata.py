import json
import pdb
import re
import sqlite3
import time
import urllib2
import urllib
import utils
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

def getBioconductorWebscrape(limit = 99999, limitTo = []):
    categories = {}

    index = BeautifulSoup(urllib2.urlopen("http://www.bioconductor.org/packages/release/bioc/").read())
    packages = index.find("div", class_="do_not_rebase").find_all("a")
    for p in packages[:limit]:
        url = p.get("href")
        name = p.get_text()
        if limitTo and name not in limitTo:
            continue
        fullurl = "http://www.bioconductor.org/packages/release/bioc/" + url
        detail = BeautifulSoup(urllib2.urlopen(fullurl).read())
        views = detail.find("td", text="biocViews").find_parent().find_all("a")
        viewlist = [v.get_text() for v in views]
        #citation = do_or_error(lambda: detail.find("div", id="bioc_citation").get_text())
        citation = do_or_error(lambda: scrapeCitationBioc(name), msg={"citations": "HTTP Error 404: Not Found"})
        titleparent = do_or_error(lambda: detail.find("h1").find_parent())
        title = do_or_error(lambda: titleparent.find("h2").get_text())
        authorlist = do_or_error(lambda: titleparent.find("p", text = re.compile(r'Author:.*')).get_text().replace("Author: ","").strip())
        description = do_or_error(lambda: titleparent.find_all("p")[1].get_text())
        print name, url, '/'.join(viewlist)
        categories[name] = { "url": fullurl, "repository": "bioconductor", "authors": authorlist, "views": viewlist, 
                            "citation": citation["citations"], "title": title, "description": description }

    return categories

def scrapeCitationBioc(name):
    citeurl = "http://bioconductor.org/packages/release/bioc/citations/" + urllib.quote(name) + "/citation.html"
    print citeurl
    time.sleep(1)
    citepage = BeautifulSoup(urllib2.urlopen(citeurl).read())
    # To Do:
    # More structured citation info available from https://hedgehog.fhcrc.org/bioconductor/trunk/madman/Rpacks/  (package)   /inst/CITATION
    #  but it's R code that generates a citation, and it's done in a pretty varied way, so it would have to be parsed by an R subprocess.
    #
    # This is less important than with cran becasue bioconductor citations are a little more structured in their 
    # plain text form
    return { "citations": citepage.get_text() }

def deprecatedGuessTitlesFromCitations(conn):
    cites = conn.execute("select * from citations where doi = '' or doi='none' or doi is null;")
    for cite in cites:
        try:
            citetext = cite["citations.citation"].split("\n\n")[0].replace("\n","")
            auths = citetext.split("(")[0]
            titleCands = citetext.split(")")[1].split(".")
            title = [t.strip() for t in titleCands if t.strip() != ""][0]
            print "Authors:", auths
            print "Title:", title.encode("ascii","replace")
            print "\n"
        except Exception, e:
            cites["citations.title"]



def extractBibtexField(bibtex, fieldname):
    """Get a field out of a bibtex field.
    
    Not a full-blown parser; assumes that close curly plus comma at end of line ends a field. 
    Cleans up accent junk, enough for Scopus search to work.
    Probably wrong in a few rare cases.
    """
    srch =  re.search((r"\b%s\s*=\s*{(.*?)},\s*\n" % fieldname),bibtex,re.DOTALL)
    if srch:
        g = srch.group(1)
        #g = re.sub(r"{\\.(.)}",r"\1", g)
        #g = re.sub(r"\\.{(.)}", r"\1", g)
        g = re.sub(r"""\\[\"v'^`~]""","",g)
        g.replace(r"\AA","A").replace(r"\aa","a")
        g = re.sub(r"\\([A-Za-z])",r"\1",g)
        g = g.replace("{","").replace("}","").replace("\\","")
        return re.sub("\s+"," ", g)
    else:
        return ""
    
def extractBibtexFields(bibtex):
    flds = ["title", "year", "author", "doi"]
    return { fld: extractBibtexField(bibtex, fld) for fld in flds }


def extractCITATIONparts(citation):
    return citation.split("citEntry")

def extractCITATIONfield(citationPart, fieldname):
    srch = re.search(re.compile(r'\b%s\s*=\s*(.*?)}' % fieldname))
    return srch

def extractCITATIONfields(citationPart):
    flds = ["title", "year", "author", "doi"]
    return { fld: extractCITATIONfield(citationPart, fld) for fld in flds }
   
#http://bibtexparser.readthedocs.org/en/latest/_modules/bparser.html
def scrapeCitationCran(name):
    citeurl = "http://cran.r-project.org/web/packages/" + urllib.quote(name) + "/citation.html"
    print citeurl
    citepage = BeautifulSoup(urllib2.urlopen(citeurl).read())
    maincitation = citepage.find("blockquote").find("p").get_text().replace("\n","").strip()
    bibtex = [pre.get_text() for pre in citepage.find_all("pre")]
    return { "citations": maincitation, "bibtex": bibtex}

def getCranWebscrape(limit=9999999, limitTo = []):
    categories = {}
    
    index = BeautifulSoup(urllib2.urlopen("http://cran.r-project.org/web/packages/available_packages_by_name.html").read())
    packages = index.find("table").find_all("a")
    for p in packages[:limit]:
        url = p.get("href")
        name = p.get_text()
        if limitTo and name not in limitTo:
            continue
        title = do_or_error(lambda: p.find_parent().find_parent().find_all("td")[-1].get_text())
        fullurl = "http://cran.r-project.org/web/packages/" + name + "/index.html"
        detail = BeautifulSoup(urllib2.urlopen(fullurl).read())
        try:
            views = detail.find("td", text=re.compile(r'In.*views')).find_parent().find_all("a")
            viewlist = [v.get_text() for v in views]
        except:
            viewlist = []
        print name, fullurl, '/'.join(viewlist)
        try:
            authorlist = detail.find("td", text="Author:").parent.find_all("td")[1].get_text()
        except:
            authorlist = ""
        description = do_or_error(lambda: detail.find("p").get_text())
        try:
            citeinfo = scrapeCitationCran(name)
        except:
            citeinfo = {"citations": "", "bibtex" : [] }
            
        categories[name] = { "url": fullurl, "repository": "cran", "authors": authorlist, "views": viewlist, "bibtex_citations": citeinfo["bibtex"], "citation": citeinfo["citations"], "title": title, "description": description }

    return categories

def recreateTable(conn, table, flds):
    try:
        conn.execute("drop table %(tb)s;" % {"tb":table} )
    except Exception, e:
        print "ERROR", str(e)
    exc = "create table %(tb)s ( %(flds)s );" % {"tb":table, "flds": flds}
    conn.execute(exc)
    conn.commit()
        
def createMetadataTables(conn, eraseCitations=False):
    recreateTable(conn, "tags", "package_name string, tag string, tagtype string")
    recreateTable(conn, "ties", "package_name string, tied string, relationship string")
    recreateTable(conn, "staticdeps", "package_name string, depends_on string")
    recreateTable(conn, "packages", "package_id integer primary key, name string, repository string, " \
                              "url string, " +\
                              "title string, description string, authors string, lastversion string, " \
                              "unique(name)  on conflict replace")
    if (eraseCitations):
        recreateTable(conn, "citations", "package_name string, citation string, year string, " +\
                              "doi_given, boolean, author string, title string, doi string, " +    \
                              "tried_crossref_doi_lookup boolean, scopus_lookup_date string, " + \
                              "scopus_citedby_count int, scopus_url string, scopus_id string, " +\
                              "doi_confidence, doi_title string, canonical boolean")

legalimport = re.compile("[a-zA-Z_0-9\._]+")

def extractDoiFromCitation(citation):
    found = re.findall(r"doi:(10\S+)", citation) + \
            re.findall(r"doi.org/(10\S+)", citation)
    for f in found:
        if f[-1:] in ".,{}()[]\"\'":
            yield f[:-1]
        else:
            yield f
            

def fixDoi(doi):
    if "10" in doi:
        return "10" + "10".join(doi.split("10")[1:])
    else:
        return doi

def saveMetadata(pkgDescription, pkgWebscrape, conn):
    """Save metadata information we've scraped about packages into database tables: packages, citations, tags, staticdeps"""
    for rec in pkgWebscrape:

        # Fix up the URL: github URLs may be in a weird format (api.github instead of just github)
        url = pkgDescription[rec].get("URL", [""])
        if not isinstance(url, str):  url = url[0]
        if url == "": url = pkgWebscrape[rec].get("url", "")
        if "/api.github" in url:
            url = "http://github.com/" + pkgWebscrape[rec]["user"] + "/" + rec

        # Create a unique record if does not exist in the packages table
        conn.execute("insert or ignore into packages (name) values (?)", (rec,))

        # and now overwrite the existing record with the new information
        try:
            conn.execute("update packages set " + 
                "title=?, description=?, authors=?, repository=?, url=? where name=?;",
                 (pkgWebscrape[rec]["title"], 
                 utils.ensure_unicode(pkgWebscrape[rec]["description"]), 
                 pkgWebscrape[rec]["authors"] if "authors" in pkgWebscrape[rec] else "",
                 pkgWebscrape[rec]["repository"], 
                 url,
                 rec))
        except Exception, e:
            print str(e), pkgWebscrape[rec]
            pdb.set_trace()
            print str(e)
        
        # Write whatever citation information we have into the citations table
        if "bibtex_citations" in pkgWebscrape[rec] and len(pkgWebscrape[rec]["bibtex_citations"] ) > 0:
            bibtex = pkgWebscrape[rec]["bibtex_citations"]
            citations = [cite.strip() for cite in pkgWebscrape[rec]["citation"].split("\n\n") if cite.strip() != ""]
            
            for (index, bib) in enumerate(bibtex):
                doi    = fixDoi(extractBibtexField(bib,"doi"))
                year   = extractBibtexField(bib,"year")
                title  = extractBibtexField(bib,"title")
                author = extractBibtexField(bib,"author")
                citetext = citations[index % len(citations)] 
                citepattern = re.sub("R package version \d.*?,", "R package version %,", citetext)
                
                rows = conn.execute("select * from citations where package_name=? and citation like ?;", (rec, citepattern))
                if len(list(rows)) == 0:
                    conn.execute("insert into citations (package_name, citation, title, author, year, doi, canonical, doi_given) " + \
                                 " values (?,?,?,?,?,?,?,?)", \
                                 (rec, citetext, title, author, year, doi, True, doi != ""))

        elif "citation" in pkgWebscrape[rec] and pkgWebscrape[rec]["citation"] != "HTTP Error 404: Not Found":
            citations = [cite.strip() for cite in pkgWebscrape[rec]["citation"].split("\n\n") if cite.strip() != ""]
            citations2 = []
            
            # Pair citations with their embedded DOIs, if they exist
            for cite in citations:
                dois = list(extractDoiFromCitation(cite))
                if len(dois) > 0:
                    for doi in dois:
                        citations2.extend([(cite, doi)])
                else:
                    citations2.extend([(cite,"")])    
            
            # Then write the pairs to the database
            for (cite,doi) in citations2:
                citepattern = re.sub("R package version \d.*?,", "R package version %,", cite)
                rows = conn.execute("select * from citations where package_name=? and citation like ?;", (rec, citepattern))
                if len(list(rows)) == 0:
                    conn.execute("insert into citations (package_name, citation, doi, canonical, doi_given) values (?,?,?,?,?)", \
                                 (rec, cite, fixDoi(doi), True, doi != ""))

        # Now add in any information gleaned from the DESCRIPTION file
        if rec in pkgDescription:
            try:
                version = pkgDescription[rec].get("Version", [""])
                if isinstance(version, basestring): version = ""
                elif len(version) == 0: version = ""
                else: version = version[0]
                conn.execute("update packages set " + 
                    "lastversion=? where name=?;",
                     (version, rec))
            except Exception, e:
                pdb.set_trace()
                print "Could not write package version information"
            
            # Now save static dependencies
            imports = list(set(pkgDescription[rec].get("Imports", []) + 
                               pkgDescription[rec].get("Depends", []) + 
                               pkgDescription[rec].get("Requires", [])))
            imports = [i for i in imports if legalimport.match(i)]
            conn.executemany("insert into staticdeps (package_name, depends_on) values (?,?);",
                [(rec, imp) for imp in imports])

        # Finally, add information about what task view the package is in to the tags table
        if "views" in pkgWebscrape[rec] and len(pkgWebscrape[rec]["views"]) > 0:
            # Don't delete previous tag information; we want to combine what we learn
            # from different repositories
            
            #conn.execute("delete from tags where package_name = ? " + \
            #        " and tagtype ='taskview';", (rec,))
            repo = pkgWebscrape[rec]["repository"]
            conn.executemany("insert into tags (package_name, tag, tagtype) values (?,?,'taskview');",
                [(rec, repo + "/" + taskview) for taskview in pkgWebscrape[rec]["views"]])

        conn.commit()

def clearTaskViews(conn):
    conn.execute("delete from tags where tagtype='taskview';")
    conn.commit()

def getCranDescription():
    directory = "http://cran.r-project.org/src/contrib/PACKAGES"
    txt = urllib.urlopen(directory).readlines()
    return parseDESCRIPTION(txt)

def getBioconductorDescription():
    directory = "http://bioconductor.org/packages/3.0/bioc/src/contrib/PACKAGES"
    txt = urllib.urlopen(directory).readlines()
    return parseDESCRIPTION(txt)
