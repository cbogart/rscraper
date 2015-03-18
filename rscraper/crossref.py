# coding: utf-8
import json
import urllib2
import urllib
import dbutil
import time
from test.sortperf import doit
import traceback
from utils import *

def citationtext2doi(fullref):
    asciiquery = fullref.encode('ascii', 'replace')
    asciiquery = asciiquery.replace(":"," ").replace("["," ").replace("]"," ")
    asciiquery = asciiquery.replace("("," ").replace(")"," ").replace("-"," ")
    asciiquery = asciiquery.replace('"', '').replace("/"," ").replace("\\", " ")
    asciiquery = asciiquery.replace('}', '').replace('{','').replace('*','')
    query = urllib.quote_plus(asciiquery)
    print query
    queryresult = urllib2.urlopen("http://api.crossref.org/works?rows=1&query=" + query).read()
    result = json.loads(queryresult)
    if len(result["message"]["items"]) > 0:
        return result["message"]["items"][0]
    else:
        return dict()
    
def createSyntheticCitations(conn):
    needCites = conn.execute("select name, authors, title from packages where name not in (select distinct(package_name) from citations);")
    conn.executemany("insert into citations (package_name, citation, canonical) values (?,?,?);",
        [(cite["packages.name"], stripParentheticals(cite["packages.authors"].replace("Author:","")) + 
          " " + justAlphabetics(cite["packages.title"]), "synthetic") for cite in needCites
            ])
    conn.commit()
    
def flattenJson(jsonobj):
    if isinstance(jsonobj, list):
        return " ".join([flattenJson(l) for l in jsonobj])
    elif isinstance(jsonobj, dict):
        return " ".join([flattenJson(jsonobj[k]) for k in jsonobj])
    else:
        return jsonobj.encode('ascii', 'replace')
  
def fillInAuthorTitleFromPackage(conn):
    cites = conn.execute("select * from packages left join citations on name=package_name where (citations.title = '' or citations.title is null);")
    for cite in cites:
        conn.execute("update citations set title=?, author=? where citation=? and package_name=?;",
                      (cite["packages.name"], cite["packages.authors"], cite["citations.citation"], cite["packages.name"]))
    conn.commit()
        
def extractAuthorTitleFromCitations(conn):
    cites = conn.execute("select citation from citations where canonical = 1 and (author = '' or author is null);")
    for cite in cites:
        citetext = cite["citations.citation"].replace("\n","")
        #print citetext
        try:
            auths = citetext.split("(")[0].encode("ascii","replace")
            year = citetext.split("(")[1].split(")")[0]
            titleCands = "".join(citetext.split(")")[1:]).split(".")
            title = [t.strip() for t in titleCands if t.strip() != ""][0].encode("ascii","replace")
            
            conn.execute("update citations set author=?, title=?, year=? where citation = ?;",
                         (auths, title, year, cite["citations.citation"]))
        except Exception, e:
            print "Error getting author and text from ", citetext
            print " ---> ERROR: ", e
            conn.execute("update citations set author=?, title=?, year=? where citation = ?;",
                         ("?", "Error:" + str(e), "????", cite["citations.citation"]))
    conn.commit()   

        
def fillInDois(conn):
    print "Skipping fillInDois"
    return
    unannotated = conn.execute("select rowid, * from citations where tried_crossref_doi_lookup = 0 or tried_crossref_doi_lookup is null and (author is not null and title is not null and author != '' and title != '') and (doi = '' or doi is null);")
    toupdate = dict()
    import pdb
    for cite in unannotated:
        try:
            print "Looking up DOI for", cite["citations.package_name"], ": ", cite["citations.citation"]
            rowid = cite["citations.rowid"]
            time.sleep(2)
            refinfo = citationtext2doi(cite["citations.citation"])
            print "  --->", refinfo["DOI"], refinfo["score"], refinfo["title"][0] if refinfo["title"] else "none", "\n"
            auth = refinfo["author"] if "author" in refinfo else "no author"
            title = refinfo["title"][0] if refinfo["title"] else "no title"
            citationinfo = flattenJson(auth) + ", " + title 
            
            conn.execute("update citations set doi = ?, doi_title=?, doi_confidence=?, tried_crossref_doi_lookup where rowid=?;", 
                             (refinfo["DOI"], citationinfo, refinfo["score"], True, rowid))
            conn.commit()
            print "Written!"
        except Exception, e:
            print "ERROR!", e
            conn.execute("update citations set doi = ?, doi_title=?, doi_confidence=? where rowid=?;", 
                             ("none", "Error: " + str(e), 0.0, rowid))
            conn.commit()
            
    
if __name__ == '__main__':
    fullref = u'Carvalho BS, Louis TA and Irizarry RA (2010). “Quantifying uncertainty in genotype calls.” Bioinformatics, 15;26(2), pp. 242-9.'
    print citationtext2doi(fullref)
    fr2 = u'J S, T N, K S and K K (2013). “TCC: an R package for comparing tag count data with robust normalization strategies.” BMC Bioinformatics, 14, pp. 219.';
    print citationtext2doi(fr2)
