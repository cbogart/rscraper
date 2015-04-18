import json
import urllib2
import urllib
import dbutil
import time
from test.sortperf import doit
import traceback
import re
import rscraper
import pickle

url_query_doi = "https://api.elsevier.com/content/search/index:SCOPUS?query=DOI({doi})&apiKey={scopus}"

url_query = "https://api.elsevier.com/content/search/scopus?query={qry}&apiKey={scopus}"
    

scopus_cache = 0
scopus_proxy_enabled = True
def enable_scopus_proxy(enable):
    global scopus_proxy_enabled
    scopus_proxy_enabled = enable
    
def scopus_proxy(url):
    """This is for debugging
    
    We can test the same code over and over without hitting scopus' server more than necessary"""
    
    if scopus_proxy_enabled == False:
        print "     using real scopus query"
        return urllib2.urlopen(url).read()
    
    global scopus_cache
    if isinstance(scopus_cache, int):
        try:
            with open("scopus_cache.pickle") as f:
                scopus_cache = pickle.load(f)
        except Exception, e:
            print str(e)
            scopus_cache = {}
    if url in scopus_cache:
        print "     using scopus proxy"
        return scopus_cache[url]
    else:
        print "     using real scopus query"
        time.sleep(1)
        result = urllib2.urlopen(url).read()
        scopus_cache[url] = result
        with open("scopus_cache.pickle", "w") as f:
            pickle.dump(scopus_cache,f)
        return result
    
    
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
    try:
        queryresult = scopus_proxy(url)
        result = json.loads(queryresult)
        return result
    except Exception, e:
        return {"error": str(e)}

def findCanonicalFromScopusId(scopus_id, credentials):
    #http://api.elsevier.com/content/search/index:scopus?query=scopus-id(77951947707)&apiKey=blah
    url=url_query.format(qry="scopus-id(" + scopus_id + ")", scopus=credentials["scopus"])
    queryresult = scopus_proxy(url)
    return json.loads(queryresult)
    

            
def escapeAnd(q): return re.sub(r"\band\b", '"and"', re.sub(r"\bor\b", '"or"', q, flags=re.I), flags=re.I)
            
def findCanonicalFromAuthorTitle(author, title, credentials):
    try:
        # Get the first few names, omitting stuff like [aut]
        url = "Url not determined yet: ", author, title
        authorlist = " ".join(rscraper.stripParentheticals(author).split()[:4])
        
        asciiTitle = title.encode('ascii','replace')
        asciiAuthorlist = authorlist.encode('ascii','replace')
        if " " in title and len(title) > 8:
            qry = urllib.quote_plus('title-abs-key-auth(' + escapeAnd(rscraper.justAlphabetics(asciiTitle)) + ')')
        else:
            qry = urllib.quote_plus('title-abs-key-auth(' + escapeAnd(rscraper.justAlphabetics(asciiTitle) + " " + asciiAuthorlist) + ')')
        url = url_query.format(qry=qry, scopus=credentials["scopus"])
        
        queryresult = scopus_proxy(url)
        return json.loads(queryresult)
    except Exception, e:
        print str(e)
        print url
        print traceback.format_exc()
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

def scopusError(result, err, which=0):
    try:
        return result["search-results"]["entry"][which]["error"]
    except:
        return str(err)
    
def citeCountFromScopusResult(result, which = 0):
    try:
        return result["search-results"]["entry"][which]["citedby-count"]
    except Exception, e:
        return scopusError(result,e,which)
        
def citeTitleFromScopusResult(result, which = 0):
    try:
        return result["search-results"]["entry"][which]["dc:title"]
    except Exception, e:
        return scopusError(result,e,which)

def doiFromScopusResult(result, which = 0):
    try:
        return result["search-results"]["entry"][which]["prism:doi"]
    except:
        return ""
    
def citeCreatorFromScopusResult(result, which = 0):
    try:
        return result["search-results"]["entry"][which]["dc:creator"]
    except Exception, e:
        return scopusError(result,e,which)

def scopusIdFromScopusResult(result, which = 0):
    try:
        api_url = result["search-results"]["entry"][which]["prism:url"] 
        ident = api_url.split("/")[-1]
        return ident.split(":")[-1]
    except Exception, e:
        return scopusError(result,e,which)
        
def citeUrlFromScopusResult(result, which = 0):
    try:
        api_url = result["search-results"]["entry"][which]["prism:url"] 
        scopus_id = api_url.split("/")[-1].split(":")[-1]
        return "http://www.scopus.com/inward/citedby.url?partnerID=HzOxMe3b&scp=" + scopus_id
    except Exception, e:
        return scopusError(result,e,which)

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
     
def doScopusRefresh(conn, creds):
    cur = conn.execute(r"""
          select distinct(scopus_id) from citations 
          where length(scopus_id) > 0 and 
            scopus_id != 'Result set was empty' and 
            scopus_lookup_date < datetime('now', '-6 days') limit 50;""")
    
    for c in cur:
        print "Refreshing citation for scopus id:", c["citations.scopus_id"]
        try:
            parsed = findCanonicalFromScopusId(c["citations.scopus_id"], creds)
            citedby_count = citeCountFromScopusResult(parsed)
            conn.execute("update citations set scopus_lookup_date = datetime('now', 'localtime'), " +\
                         "scopus_citedby_count=? where scopus_id=?;",
                         ((citedby_count, c["citations.scopus_id"])))
            conn.commit()
        except Exception, e:
            print "    Cannot refresh because", str(e)
    
    
def doScopusLookup(conn, limitTo=[]):
    creds = rscraper.loadCredentials("credentials.json")
    doScopusRefresh(conn,creds)
    
    cur = conn.execute("select * from citations where (scopus_lookup_date is null or scopus_lookup_date = '')" +\
                       "and length(doi) > 0 and (doi_given == 1 or doi_confidence >= 1.0)")
    for c in cur:
        if limitTo and c["citations.package_name"] not in limitTo:
            continue
        print "Scopus lookup using doi for ", c["citations.package_name"]
        parsed = findCanonicalFromDoi(c["citations.doi"], creds)
        scopus_id = scopusIdFromScopusResult(parsed)
        scopus_url = citeUrlFromScopusResult(parsed)
        citedby_count = citeCountFromScopusResult(parsed)
        conn.execute("update citations set scopus_lookup_date = datetime('now', 'localtime'), " +\
                     "scopus_id=?, scopus_url=?, scopus_citedby_count=? where package_name=? and doi=?;",
                     ((scopus_id, scopus_url, citedby_count, c["citations.package_name"], c["citations.doi"])))
        conn.commit()
    
    cur = conn.execute("select * from citations where (scopus_lookup_date is null or scopus_lookup_date = '') " +\
                       "and (doi is null or doi = '' or doi_confidence < 1) and " +\
                       "length(author) > 0 and length(title) > 0;")
    for c in cur:
        if limitTo and c["citations.package_name"] not in limitTo:
            continue
        print "Scopus lookup using author/title for ", c["citations.package_name"], "auth:", \
                c["citations.author"], "title:", c["citations.title"]
        if c["citations.title"].startswith("Error:") or len(c["citations.title"]) < 7:
            print "    Skipping this one"
            continue
        parsed = findCanonicalFromAuthorTitle(c["citations.author"], c["citations.title"], creds)
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
    

    
    
