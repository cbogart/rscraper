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
    print json.dumps(result, indent=4)
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
    
def fillInDois(conn):
    unannotated = conn.execute("select rowid, * from citations where doi = '' or doi is null;")
    toupdate = dict()
    import pdb
    try:
        for cite in unannotated:
            print "Looking up DOI for", cite["citations.package_name"], ": ", cite["citations.citation"]
            time.sleep(2)
            refinfo = citationtext2doi(cite["citations.citation"])
            print "  --->", refinfo["DOI"], refinfo["score"], refinfo["title"][0] if refinfo["title"] else "none", "\n"
            toupdate[cite["citations.rowid"]] = refinfo
    except Exception, e:
        print e
        import pdb
        pdb.set_trace()
    finally:
        To do: add authors (toupdate[r]["author"][x]["family"], given) to title, just to be sure
        conn.executemany("update citations set doi = ?, doi_title=?, doi_confidence=? where rowid=?;", 
                         [(toupdate[r]["DOI"], toupdate[r]["title"][0] if toupdate[r]["title"] else "none", toupdate[r]["score"], r) for r in toupdate])
        conn.commit()
    
if __name__ == '__main__':
    fullref = u'Carvalho BS, Louis TA and Irizarry RA (2010). “Quantifying uncertainty in genotype calls.” Bioinformatics, 15;26(2), pp. 242-9.'
    print citationtext2doi(fullref)
    fr2 = u'J S, T N, K S and K K (2013). “TCC: an R package for comparing tag count data with robust normalization strategies.” BMC Bioinformatics, 14, pp. 219.';
    print citationtext2doi(fr2)
