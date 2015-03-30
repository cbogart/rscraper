import unittest
from rscraper import *
import rscraper
import json


def jmemo(item, filen):
    """Persistently memoize a function returning a json object

    @param item A function that is expensive to compute, and returns json
    @param filen A filename to use for memoization
    @returns The contents of the file; if it does not exist, it is created from item()
    """
    try:
        with open(filen + ".json", "r") as f:
            return json.loads(f.read())
    except:
        with open(filen + ".json", "w") as f:
            i = item()
            f.write(json.dumps(i, indent=4))
            return i

def createCranBiocGitTables():
        """Create a table of R packages from CRAN, Bioconductor, and Github.

        Use previously-scraped information about github R projects to populate
        a table of packages ("packages" are defined as github projects that are
        in R and contain a DESCRIPTION file).
        
        Overwrite that information with packages scraped from Bioconductor, then
        again from CRAN.  Thus Cran takes priority over Bioconductor, and both
        take priority over Github.

        Finally, fill in citation information as best as can be scraped from
        the Bioconductor and CRAN sites, and then look them up in Scopus to find
        out how often they have been cited.
        """
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
    createCranBiocGitTables()
