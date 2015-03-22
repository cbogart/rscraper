import unittest
from nose.plugins.attrib import attr
from rscraper.getRepoMetadata import *
from rscraper.dbutil import *
from rscraper.scopus import *
from rscraper.credentials import loadCredentials
from rscraperTesting import RscraperTesting

class TestScopus(RscraperTesting):


    @attr("scopus","internet")
    def test_findCanonicalFromDoi_real(self):
        enable_scopus_proxy(False)
        self.test_findCanonicalFromDoi()
        
    def test_findCanonicalFromDoi(self):
        canon = findCanonicalFromDoi("10.1016/j.envsoft.2011.09.008", loadCredentials("credentials.json"))
        self.assertEqual(scopusIdFromScopusResult(canon), "84855561999")
        self.assertEqual(citeUrlFromScopusResult(canon), "http://www.scopus.com/inward/citedby.url?partnerID=HzOxMe3b&scp=84855561999")
        self.assertEqual(citeCountFromScopusResult(canon), "75")
        self.assertEqual(citeTitleFromScopusResult(canon), "Openair - An r package for air quality data analysis")
        self.assertEqual(citeCreatorFromScopusResult(canon), "Carslaw, D.C.")
        self.assertEqual(totalCountScopusResults(canon), "1")
        
    @attr("scopus","internet")
    def test_findCanonicalFromScopusId_real(self):
        enable_scopus_proxy(False)
        self.test_findCanonicalFromScopusId()
       
    def test_findCanonicalFromScopusId(self):
        canon = findCanonicalFromScopusId("21244459873",loadCredentials("credentials.json"))
        self.assertEqual(citeTitleFromScopusResult(canon), "Zoo: S3 infrastructure for regular and irregular time series")
        
    @attr("scopus","internet")
    def test_findCanonicalFromAuthorTitle_real(self):
        enable_scopus_proxy(False)
        self.test_findCanonicalFromAuthorTitle()
        
    def test_escapeAnd(self):
        self.assertEquals(rscraper.scopus.escapeAnd('this and that'), 'this "and" that')
        self.assertEquals(rscraper.scopus.escapeAnd('this hand that or the other'), 'this hand that "or" the other')
        self.assertEquals(rscraper.scopus.escapeAnd('Let them eat cake and'), 'Let them eat cake "and"')
            
    def test_findCanonicalFromAuthorTitle(self):
        canon = findCanonicalFromAuthorTitle("Hadley Wickham","testthat: Get Started with Testing", loadCredentials("credentials.json"))
        self.assertEqual(scopusIdFromScopusResult(canon), "84883222645")
        self.assertEqual(citeCountFromScopusResult(canon), "1")
        canon = findCanonicalFromAuthorTitle("Wolfgang Viechtbauer","Conducting meta-analyses in R with the metafor package", loadCredentials("credentials.json"))
        self.assertEqual(scopusIdFromScopusResult(canon), "77958110812")
        self.assertEqual(citeCountFromScopusResult(canon), "498")
        canon = findCanonicalFromAuthorTitle("Dirk Eddelbuettel and Romain Fran\ccois","Rcpp: Seamless R and C++ Integration", loadCredentials("credentials.json"))
        self.assertEqual(scopusIdFromScopusResult(canon), "79961240792")
        self.assertEqual(citeCountFromScopusResult(canon), "55")
        canon = findCanonicalFromAuthorTitle("Achim Zeileis and Gabor Grothendieck","zoo: S3 Infrastructure for Regular and Irregular Time Series", loadCredentials("credentials.json"))
        self.assertEqual(scopusIdFromScopusResult(canon), "21244459873")
        self.assertEqual(citeCountFromScopusResult(canon), "41")
        
        
"""
Stuff to especially test:

testthat|Hadley Wickham. testthat: Get Started with Testing. The R Journal, vol. 3, no. 1, pp. 5--10, 2011|2011|0||Hadley Wickham|testthat: Get Started with Testing|||||||||1
testthat|Hadley Wickham. testthat: Get Started with Testing. The R Journal, vol. 3, no. 1, pp. 5--10, 2011|2011|0||Hadley Wickham|testthat: Get Started with Testing|||||||||1

metafor|Wolfgang Viechtbauer (2010). Conducting meta-analyses in R with the metafor package. Journal of Statistical Software, 36(3), 1-48. URL http://www.jstatsoft.org/v36/i03/.|2010|0||Wolfgang Viechtbauer|Conducting meta-analyses in R with the metafor package|||||||||1
metafor|Wolfgang Viechtbauer (2010). Conducting meta-analyses in R with the metafor package. Journal of Statistical Software, 36(3), 1-48. URL http://www.jstatsoft.org/v36/i03/.|2010|0||Wolfgang Viechtbauer|Conducting meta-analyses in R with the metafor package|||||||||1

Rcpp|Dirk Eddelbuettel and Romain Francois (2011). Rcpp: Seamless R and C++ Integration. Journal of Statistical Software, 40(8), 1-18. URL http://www.jstatsoft.org/v40/i08/.|2011|0||Dirk Eddelbuettel and Romain Fran\ccois|Rcpp: Seamless R and + Integration|||||||||1
Rcpp|Dirk Eddelbuettel and Romain Francois (2011). Rcpp: Seamless R and C++ Integration. Journal of Statistical Software, 40(8), 1-18. URL http://www.jstatsoft.org/v40/i08/.|2011|0||Dirk Eddelbuettel and Romain Fran\ccois|Rcpp: Seamless R and + Integration|||||||||1

zoo|Achim Zeileis and Gabor Grothendieck (2005). zoo: S3 Infrastructure for Regular and Irregular Time Series.|2005|0||Achim Zeileis and Gabor Grothendieck|zoo: S3 Infrastructure for Regular and Irregular Time Series|||2015-03-19 19:10:44|41|http://www.scopus.com/inward/citedby.url?partnerID=HzOxMe3b&scp=21244459873|21244459873||Zoo: S3 infrastructure for regular and irregular time series|1
zoo|Achim Zeileis and Gabor Grothendieck (2005). zoo: S3 Infrastructure for Regular and Irregular Time Series. Journal of Statistical Software, 14(6), 1-27. URL http://www.jstatsoft.org/v14/i06/|2005|0||Achim Zeileis and Gabor Grothendieck|zoo: S3 Infrastructure for Regular and Irregular Time Series|||||||||1
"""    
    
    
if __name__ == '__main__':
    unittest.main()
