from rscraper import *



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
        clearTaskViews(conn)
        print "Git..."
        gd = extractGitDescription(conn)
        saveMetadata(gd,makeGitPseudoWebscrape(gd),conn)
        print "Bioconductor...****************************"
        bws = jmemo(lambda:getBioconductorWebscrape(), "bioc_web_scrape", 30)
        biod = jmemo(lambda:getBioconductorDescription(), "bioc_desc_scrape",10)
        saveMetadata(biod, bws, conn)
        print "CRAN...*************************"
        cws = jmemo(lambda:getCranWebscrape(), "cran_web_scrape", 30)
        crand = jmemo(lambda:getCranDescription(), "cran_desc_scrape",10)
        saveMetadata(crand, cws, conn)
        print "CROSSREF*********************"
        crossref.extractAuthorTitleFromCitations(conn)
        crossref.fillInAuthorTitleFromPackage(conn)
        print "FillINDOIs*********************"
        fillInDois(conn)
        print "SCOPUS***********************"
        enable_scopus_proxy(False)
        doScopusLookup(conn)

if __name__ == '__main__':
    conn = getConnection("repoScrape.db")
    createCranBiocGitTables()
    #doScopusLookup(conn)
    #import pdb
    #pdb.set_trace()
    #rscraper.gitscraper.backfillOwnerType(loadCredentials("credentials.json"), conn)
