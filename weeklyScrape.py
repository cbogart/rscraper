import unittest
from rscraper import *
import rscraper
import json


def jmemo(item, filen):
    try:
        with open(filen + ".json", "r") as f:
            return json.loads(f.read())
    except:
        with open(filen + ".json", "w") as f:
            i = item()
            f.write(json.dumps(i, indent=4))
            return i

def createCranBiocGitTables():
        # Populate in order of least to highest priority:
        # i.e. if we have a project both in Github and CRAN,
        # the cran information takes priority, so write it in
        # last overriding whatever we found on github.

        conn = getConnection("repoScrape.db")
        createMetadataTables(conn)

        print "Git..."
        gws = extractGitWebscrape(conn)
        gd = extractGitDescription(conn)
        saveMetadata(gd,gws,conn)
        print "Bioconductor...****************************"
        bws = jmemo(lambda:getBioconductorWebscrape(), "bioc_web_scrape")
        biod = jmemo(lambda:getBioconductorDescription(), "bioc_desc_scrape")
        saveMetadata(biod, bws, conn)
        print "CRAN...*************************"
        cws = jmemo(lambda:getCranWebscrape(), "cran_web_scrape")
        crand = jmemo(lambda:getCranDescription(), "cran_desc_scrape")
        saveMetadata(crand, cws, conn)
        print "CROSSREF*********************"
        crossref.extractAuthorTitleFromCitations(conn)
        crossref.fillInAuthorTitleFromPackage(conn)
        print "FillINDOIs*********************"
        fillInDois(conn)
        print "SCOPUS***********************"
        doScopusLookup(conn)

if __name__ == '__main__':
    conn = getConnection("repoScrape.db")
    ##cur = conn.execute("select * from citations where doi_confidence < 1 and package_name = 'metafor' and doi_confidence > 0 order by random() limit 1;")
    #for c in cur:
    #    print c["citations.citation"]
    #    print "Calling with ", c["citations.author"], c["citations.title"], c["citations.doi_confidence"]
    #    testScopusNames(c["citations.author"], c["citations.title"])
    #crossref.fillInAuthorTitleFromPackage(conn)
    #rscraper.createSyntheticCitations(conn)
    createCranBiocGitTables()
    #doScopusLookup(conn)
    #adegenet = getRepoMetadata.scrapeCitationCran("adegenet")
    #print json.dumps(adegenet, indent=4)
    #fillInDois(conn)
   
    #testScopus()
    
    
    