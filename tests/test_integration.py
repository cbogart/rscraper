import unittest
from nose.plugins.attrib import attr
import rscraper
from rscraper.getRepoMetadata import *
from rscraper.dbutil import *
import json
import os
import inspect
import rscraper.crossref
import rscraperTesting


class RscraperTesting(rscraperTesting.RscraperTesting):


    @attr("integration", "internet")
    def test_metadataPopulate_cran_real(self):
        self.helper_test_metadataPopulate_cran(useInternet=True)

    @attr("integration")
    def test_metadataPopulate_cran(self):
        self.helper_test_metadataPopulate_cran(useInternet=False)
        
    def helper_test_metadataPopulate_cran(self, useInternet = False):
        conn = self.getconn()
        createMetadataTables(conn, eraseCitations=True)
    
        if useInternet:
            crand = getCranDescription()
            cws = getCranWebscrape(limitTo = self.interestingPackages)
        else:
            crand = self.jmemo(lambda:getCranDescription(), "tests/crandesctest")
            cws = self.jmemo(lambda:getCranWebscrape(limitTo = self.interestingPackages), "tests/cranwebtest")
        saveMetadata(crand, cws, conn)
        self.oneDbResultEqual(conn, "select count(*) from packages where repository != 'cran';", "0")
        self.oneDbResultEqual(conn, "select lastversion from packages where name='A3'",  "0.9.2")
        
        rscraper.crossref.extractAuthorTitleFromCitations(conn)
        rscraper.crossref.fillInAuthorTitleFromPackage(conn)
        
        if useInternet:
            rscraper.scopus.enable_scopus_proxy(False)
        else:
            rscraper.scopus.enable_scopus_proxy(True)
            
        rscraper.scopus.doScopusLookup(conn, limitTo = self.interestingPackages)
        
        def checkCite(pkg, fld, expected):
            self.oneDbResultEqual(conn, "select {fld} from citations where package_name='{pkg}';" 
                                  .format(pkg=pkg, fld=fld), expected)
        def checkCiteAtLeast(pkg, fld, expected):
            self.assertGreaterEqual(
                int(self.oneDbResult(conn, "select {fld} from citations where package_name='{pkg}';" 
                                  .format(pkg=pkg, fld=fld))), int(expected))
            
        checkCite("testthat", "scopus_id", "84883222645")
        checkCiteAtLeast("testthat", "scopus_citedby_count", 1)
        checkCite("metafor", "scopus_id", "77958110812")
        checkCiteAtLeast("metafor", "scopus_citedby_count", 498)
        checkCite("zoo", "scopus_id", "21244459873")
        checkCiteAtLeast("zoo", "scopus_citedby_count", 41)
        
        #Check dependency scraping
        pegasDeps = self.oneDbResult(conn, 'select group_concat(depends_on) from staticdeps where package_name="pegas";')
        self.assertEqual(set(pegasDeps.split(",")), set(["ape", "adegenet", "R", "graphics", "utils"]))
        
        
    @attr("integration", "internet")
    def test_metadataPopulate_bioconductor_real(self):
        self.helper_test_metadataPopulate_bioconductor(useInternet=True)

    @attr("internet")
    def test_metadataPopulate_github(self):
        conn = self.getconn()
        
        This will not work.  We have to query github as part of this process,
        because otherwise extractGitDescription is working from an empty database.
        Querying git is not set up to where we can cache the results easily.
        
        createMetadataTables(conn, eraseCitations = True)
        clearTaskViews(conn)
        gd = extractGitDescription(conn)
        gw = makeGitPseudoWebscrape(gd)
        saveMetadata(gd,gw,conn)
        
        createMetadataTables(conn, eraseCitations=True)
    
        if useInternet:
            biod = getBioconductorDescription()
            bws = getBioconductorWebscrape(limitTo = self.interestingPackages)
        else: 
            biod = self.jmemo(lambda:getBioconductorDescription(), "tests/biodesctest")
            bws = self.jmemo(lambda:getBioconductorWebscrape(limitTo = self.interestingPackages), "tests/biowebtest")
            
        saveMetadata(biod, bws, conn)
        
        self.assertEquals(self.oneDbResult(conn,"select group_concat(repository) from packages where repository != 'cran';"), 
                          "bioconductor,bioconductor,bioconductor,bioconductor,bioconductor,bioconductor")
        self.assertEquals(self.oneDbResult(conn, "select authors from packages where name='a4Preproc';"), 
                          "Willem Talloen, Tobias Verbeke")
        self.oneDbResultEquals(conn, "select count(*) from citations where package_name='aroma.light';", "0")
        
        rscraper.crossref.extractAuthorTitleFromCitations(conn)
        
        self.oneDbResultEquals(conn, "select title from citations where package_name='XDE';",
                         "A Bayesian model for cross-study differential gene expression")

        rscraper.crossref.fillInAuthorTitleFromPackage(conn)

    @attr("integration")
    def test_metadataPopulate_bioconductor(self):
        self.helper_test_metadataPopulate_bioconductor(useInternet=False)
        
    def helper_test_metadataPopulate_bioconductor(self, useInternet = False):
        conn = self.getconn()
        createMetadataTables(conn, eraseCitations=True)
    
        if useInternet:
            biod = getBioconductorDescription()
            bws = getBioconductorWebscrape(limitTo = self.interestingPackages)
        else: 
            biod = self.jmemo(lambda:getBioconductorDescription(), "tests/biodesctest")
            bws = self.jmemo(lambda:getBioconductorWebscrape(limitTo = self.interestingPackages), "tests/biowebtest")
            
        saveMetadata(biod, bws, conn)
        
        self.assertEquals(self.oneDbResult(conn,"select group_concat(repository) from packages where repository != 'cran';"), 
                          "bioconductor,bioconductor,bioconductor,bioconductor,bioconductor,bioconductor")
        self.assertEquals(self.oneDbResult(conn, "select authors from packages where name='a4Preproc';"), 
                          "Willem Talloen, Tobias Verbeke")
        self.oneDbResultEquals(conn, "select count(*) from citations where package_name='aroma.light';", "0")
        
        rscraper.crossref.extractAuthorTitleFromCitations(conn)
        
        self.oneDbResultEquals(conn, "select title from citations where package_name='XDE';",
                         "A Bayesian model for cross-study differential gene expression")

        rscraper.crossref.fillInAuthorTitleFromPackage(conn)


if __name__ == '__main__':
    unittest.main()
