import json
import urllib2
import urllib
import dbutil
import time
from test.sortperf import doit
import traceback
import re
import rscraper
from sympy.physics.quantum.shor import ratioize

#url_query_doi_inst = "https://api.elsevier.com/content/search/scopus?query=DOI({doi})&field=citedby-count&apiKey={scopus}"+ \
#       "&insttoken={scopus_token}"
#url_query_doi = "https://api.elsevier.com/content/search/scopus?query=DOI({doi})&field=citedby-count&apiKey={scopus}"
url_query_doi = "https://api.elsevier.com/content/search/index:SCOPUS?query=DOI({doi})&apiKey={scopus}"
   
#url_query_author_title = "https://api.elsevier.com/content/search/scopus?query=" + \
#    "AUTHLASTNAME({author})%20AND%20TITLE({title})&field=citedby-count" + \
#     "&apiKey={scopus}"

url_query = "https://api.elsevier.com/content/search/scopus?query=" + \
     "{qry}&apiKey={scopus}"
    
#
# Given: a doi OR a citation text OR a synthesized citation text
# Find: a citation count and a link to scopus for those
#
# Route 1:
#     doi -> citation count api
#     doi -> search for docs with this in the references
#     doi -> search for this doc, get
def findCanonicalFromDoi(doi, credentials):
       
    url = url_query_doi.format(doi=doi, scopus=credentials["scopus"])
    
    queryresult = urllib2.urlopen(url).read()
    result = json.loads(queryresult)
    return (queryresult, result)



    
def findCanonicalFromAuthorTitle(author, title, credentials):
    try:
        # Get the first few names, omitting stuff like [aut]
        authorlist = " ".join(rscraper.stripParentheticals(author).split()[:4])
        
        #if len(authorlist):
        #    qry = urllib.quote_plus("(" + " OR ".join(["AUTH(" + a + ")" for a in authorlist[:4]]) + ") AND TITLE(" + title + ")")
        #else:
        #    url = ""
        #    raise Exception("No authors known for this package")
        if " " in title and len(title) > 8:
            qry = urllib.quote_plus("title-abs-key-auth(" + rscraper.justAlphabetics(title) + ")")
        else:
            qry = urllib.quote_plus("title-abs-key-auth(" + rscraper.justAlphabetics(title) + " " + authorlist + ")")
        time.sleep(1)
        url = url_query.format(qry=qry, scopus=credentials["scopus"])
        
        queryresult = urllib2.urlopen(url).read()
        result = json.loads(queryresult)
        return (queryresult, result)
    except Exception, e:
        print url
        print str(e)
        raise e


def totalCountScopusResults(result):
    """
    "opensearch:totalResults": "0",
    "opensearch:startIndex": "0",
    "opensearch:itemsPerPage": "0",
    """
    return result["search-results"]["opensearch:totalResults"]

def countScopusResults(result):
    return len(result["search-results"]["entry"])

def scopusError(result, which=0):
    return result["search-results"]["entry"][which]["error"]
    
def citeCountFromScopusResult(result, which = 0):
    try:
        return result["search-results"]["entry"][which]["citedby-count"]
    except:
        return scopusError(result,which)
        
def citeTitleFromScopusResult(result, which = 0):
    try:
        return result["search-results"]["entry"][which]["dc:title"]
    except:
        return scopusError(result,which)

def doiFromScopusResult(result, which = 0):
    try:
        return result["search-results"]["entry"][which]["prism:doi"]
    except:
        return ""
    
def citeCreatorFromScopusResult(result, which = 0):
    try:
        return result["search-results"]["entry"][which]["dc:creator"]
    except:
        return scopusError(result,which)

def scopusIdFromScopusResult(result, which = 0):
    try:
        api_url = result["search-results"]["entry"][which]["prism:url"] 
        return api_url.split("/")[-1]
    except:
        return scopusError(result,which)
        
def citeUrlFromScopusResult(result, which = 0):
    try:
        api_url = result["search-results"]["entry"][which]["prism:url"] 
        scopus_id = api_url.split("/")[-1]
        return "http://www.scopus.com/inward/citedby.url?partnerID=HzOxMe3b&scp=" + scopus_id
    except:
        return scopusError(result,which)

def findBestScopusMatch(result, actualTitle):
    bestscore = -1
    bestratio = -1
    for res in range(countScopusResults(result)):
        ratio = rscraper.similar(citeTitleFromScopusResult(result, res), actualTitle)
        if ratio > bestratio:
            bestratio = ratio
            bestscore = res
    print "Best match (", bestratio, ") for", actualTitle.replace("\n",""), "is", citeTitleFromScopusResult(result,bestscore)
    if bestratio < .8:
        print "*******Not good enough!!"
        bestscore = -1
    return bestscore

def dumpScopusInfo(result):
    for res in range(countScopusResults(result)):
        print res, "Title: ", citeTitleFromScopusResult(result, res)
        print "  Author: ", citeCreatorFromScopusResult(result, res)
        print "  Cited", citeCountFromScopusResult(result, res), "times"
        print "     (listed here:", citeUrlFromScopusResult(result,res), ")"
        print ""
     
def doScopusLookup(conn):
    creds = rscraper.loadCredentials("credentials.json")
    
    cur = conn.execute("select * from citations where (scopus_lookup_date is null or scopus_lookup_date = '' or " +\
                       "scopus_lookup_date < datetime('now', ' -6 days')) and length(doi) > 0 and (doi_given == 1 or doi_confidence >= 1.0)")
    for c in cur:
        print "Scopus lookup using doi for ", c["citations.package_name"]
        time.sleep(1)
        (raw,parsed) = findCanonicalFromDoi(c["citations.doi"], creds)
        scopus_id = scopusIdFromScopusResult(parsed)
        scopus_url = citeUrlFromScopusResult(parsed)
        citedby_count = citeCountFromScopusResult(parsed)
        conn.execute("update citations set scopus_lookup_date = datetime('now', 'localtime'), " +\
                     "scopus_id=?, scopus_url=?, scopus_citedby_count=? where package_name=? and doi=?;",
                     ((scopus_id, scopus_url, citedby_count, c["citations.package_name"], c["citations.doi"])))
        conn.commit()
    
    cur = conn.execute("select * from citations where (scopus_lookup_date is null or scopus_lookup_date = '' or " +\
                       "scopus_lookup_date < datetime('now', ' -6 days')) and (doi is null or doi = '' or doi_confidence < 1) and " +\
                       "length(author) > 0 and length(title) > 0;")
    for c in cur:
        print "Scopus lookup using author/title for ", c["citations.package_name"], "auth:", c["citations.author"], "title:", c["citations.title"]
        time.sleep(1)
        (raw,parsed) = findCanonicalFromAuthorTitle(c["citations.author"], c["citations.title"], creds)
        dumpScopusInfo(parsed)
        which = findBestScopusMatch(parsed, c["citations.title"])
        print "  Best is #:", which
        if (which > -1):
            scopus_id = scopusIdFromScopusResult(parsed,which)
            citedby_count = citeCountFromScopusResult(parsed,which)
            scopus_title = citeTitleFromScopusResult(parsed,which)
            scopus_url = citeUrlFromScopusResult(parsed,which)
            doi = doiFromScopusResult(parsed,which)
            conn.execute("update citations set scopus_lookup_date = datetime('now', 'localtime'), " +\
                         "scopus_id=?, scopus_url=?, doi=?, doi_title=?, scopus_citedby_count=? where package_name=? and author=? and title=?;",
                         ((scopus_id, scopus_url, doi, scopus_title, citedby_count, c["citations.package_name"], c["citations.author"], c["citations.title"])))
        else:
            conn.execute("update citations set scopus_lookup_date = datetime('now', 'localtime'), " +\
                         "scopus_id=?, scopus_url=?, doi=?, doi_title=?, scopus_citedby_count = ? where package_name=? and author=? and title=?;",
                         (("", "", "", "No match", "", c["citations.package_name"], c["citations.author"], c["citations.title"])))
        conn.commit()
    
def testScopusNames(author = "Annie Bouvier, Kien Kieu, Kasia Adamczyk, and Herve Monod", \
                    title = "Computation of the Integrated Flow of Particles between Polygons", \
                    ):
    creds = rscraper.loadCredentials("credentials.json")
    
    try:
        infos = findCanonicalFromAuthorTitle(author, title, creds)
        print json.dumps(infos[1], indent=4)
        dumpScopusInfo(infos[1])
    except Exception, e:
        print e
    
def testScopusDoi():
    doi = "10.1016/j.envsoft.2008.11.006"
    creds = rscraper.loadCredentials("credentials.json")
    
    infos = findCanonicalFromDoi(doi, creds)
    print infos[0]
    print "-----"
    print json.dumps(infos[1], indent=4)
    with open("scopus_canon_doi.json","w") as f:
        f.write(infos[0])

    dumpScopusInfo(infos[1])
    
    
    
    