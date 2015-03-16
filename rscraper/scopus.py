import json
import urllib2
import urllib
import dbutil
import time
from test.sortperf import doit
import traceback
import re
import rscraper

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


def findRefsFromUrl(url, name, author, title, credentials):
    try:
        authorlist = [a for a in justAlphabetics(stripParentheticals(author)).strip().split(" ") if len(a) > 3]
        
        #if len(authorlist):
        #    qry = urllib.quote_plus("(" + " OR ".join(["AUTH(" + a + ")" for a in authorlist[:4]]) + ") AND TITLE(" + title + ")")
        #else:
        #    url = ""
        #    raise Exception("No authors known for this package")
        
        if "cran.r-project" in url: 
            url = "cran.r-project"
        if "bioconductor" in url:
            url = "bioconductor"
            
        qry = urllib.quote_plus("ref(" + url + " " + name + ")")
        url = url_query.format(qry=qry, scopus=credentials["scopus"])
        print url
        time.sleep(1)

        queryresult = urllib2.urlopen(url).read()
        result = json.loads(queryresult)
        return (queryresult, result)
    except Exception, e:
        print url
        print str(e)
        raise e
    
def findCanonicalFromAuthTitle(author, title, credentials):
    try:
        authorlist = [a for a in justAlphabetics(stripParentheticals(author)).strip().split(" ") if len(a) > 3]
        
        #if len(authorlist):
        #    qry = urllib.quote_plus("(" + " OR ".join(["AUTH(" + a + ")" for a in authorlist[:4]]) + ") AND TITLE(" + title + ")")
        #else:
        #    url = ""
        #    raise Exception("No authors known for this package")
        
        qry = urllib.quote_plus("ref(" + justAlphabetics(title) + " " + " ".join(authorlist[:4]) + ")")
        time.sleep(1)
        url = url_query.format(qry=qry, scopus=credentials["scopus"])
        
        queryresult = urllib2.urlopen(url).read()
        result = json.loads(queryresult)
        return (queryresult, result)
    except Exception, e:
        print url
        print str(e)
        raise e

def findCanonicalFromPackageInfo(packageinfo):
    return 3
    
def findCanonicalFromRawCitationText(rawcitation):
    return 3

def totalCountScopusResults(result):
    """
    "opensearch:totalResults": "0",
    "opensearch:startIndex": "0",
    "opensearch:itemsPerPage": "0",
    """
    return result["search-results"]["opensearch:totalResults"]

def countScopusResults(result):
    return len(result["search-results"]["entry"])

def citeCountFromScopusResult(result, which = 0):
    try:
        return result["search-results"]["entry"][which]["citedby-count"]
    except:
        return result["search-results"]["entry"][which]["error"]
def citeTitleFromScopusResult(result, which = 0):
    try:
        return result["search-results"]["entry"][which]["dc:title"]
    except:
        return result["search-results"]["entry"][which]["error"]

def citeCreatorFromScopusResult(result, which = 0):
    try:
        return result["search-results"]["entry"][which]["dc:creator"]
    except:
        return result["search-results"]["entry"][which]["error"]

def citeUrlFromScopusResult(result, which = 0):
    try:
        api_url = result["search-results"]["entry"][which]["prism:url"] 
        scopus_id = api_url.split("/")[-1]
        return "http://www.scopus.com/inward/citedby.url?partnerID=HzOxMe3b&scp=" + scopus_id
    except:
        return result["search-results"]["entry"][which]["error"]
   
def dumpScopusInfo(result):
    for res in range(countScopusResults(result)):
        print "Title: ", citeTitleFromScopusResult(result, res)
        print "Author: ", citeCreatorFromScopusResult(result, res)
        print "Cited", citeCountFromScopusResult(result, res), "times"
        print "   (listed here:", citeUrlFromScopusResult(result,res), ")"
        print ""
     
def testScopusNames(authorship = "Annie Bouvier, Kien Kieu, Kasia Adamczyk, and Herve Monod", \
                    name = "",
                    title = "Computation of the Integrated Flow of Particles between Polygons", \
                    url = ""):
    creds = rscraper.loadCredentials("credentials.json")
    
    try:
        infos = findRefsFromUrl(url, name, authorship, title, creds)
        
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
    
    
    
    