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

def oneDbResult(conn, qry):
    result = conn.execute(qry)
    r1 = result.next()
    return r1[0]

class TestRepoMetadata(unittest.TestCase):

    def oneDbResult(self, conn, a, qry):
        result = conn.execute(qry)
        r1 = result.next()
        self.assertEqual(r1[0], a)

    def test_unquote(self):
        self.assertEqual("xyzzy", rscraper.unquote("xyzzy"))
        self.assertEqual("xyzzy", rscraper.unquote('"xyzzy"'))
        self.assertEqual('"xyzzy', rscraper.unquote('"xyzzy'))

    def test_do_or_error(self):
        self.assertEqual("4", do_or_error(lambda: "4", "goober"))
        self.assertEqual("goober", do_or_error(lambda: 3/0, "goober"))

    def test_get_bioconductor_webscrape(self):
        bws = jmemo(lambda:getBioconductorWebscrape(limit=5), "biowebtest1")
        self.assertEqual( bws["a4Base"]["description"] , "Automated Affymetrix Array Analysis")
        self.assertEqual( bws["a4Base"]["repository"] , "bioconductor")
        self.assertEqual( bws["a4Base"]["url"] , "http://www.bioconductor.org/packages/release/bioc/html/a4Base.html")
        self.assertIn(bws["a4Base"]["views"], "Microarray")
        self.assertIn(bws["a4Base"]["views"], "Software")
        self.assertIn(bws["a4Base"]["citation"], "Talloen W, Verbeke")

    #def test_scrape_citation_bioc(self):
        # self.assertEqual(expected, scrapeCitationBioc(name))
        #assert False # TODO: implement your test here

    #def test_scrape_citation_cran(self):
        # self.assertEqual(expected, scrapeCitationCran(name))
        #assert False # TODO: implement your test here

    def test_get_cran_webscrape(self):
        cws = jmemo(lambda:getCranWebscrape(limit=5), "cranwebtest3")
        self.assertIn("The package implements several", cws["abc"]["description"])
        self.assertEqual( cws["abc"]["repository"] , "cran")
        self.assertEqual( cws["abc"]["title"] , "Tools for Approximate Bayesian Computation (ABC)")
        self.assertEqual( cws["abc"]["url"] , "http://cran.r-project.org/web/packages/abc/index.html")
        self.assertIn(cws["abc"]["views"], "Bayesian")
        self.assertIn(cws["A3"]["citation"],"Scott Fortmann-Roe (2013). Accurate")

    #def test_recreate_table(self):
        # self.assertEqual(expected, recreateTable(conn, table, flds))
        #assert False # TODO: implement your test here

    #def test_create_metadata_tables(self):
        # self.assertEqual(expected, createMetadataTables(conn))
        # assert False # TODO: implement your test here

    def test_save_metadata(self):
        conn = getConnection("test1.db")

        createMetadataTables(conn)
        crand = jmemo(lambda:getCranDescription(), "crandesctest4")
        cws = jmemo(lambda:getCranWebscrape(limit=5), "cranwebtest3")
        saveMetadata(crand, cws, conn)
        self.assertEqual(
            oneDbResult(conn, "select group_concat(repository) from packages;"),
            "cran,cran,cran,cran,cran")
    
        biod = jmemo(lambda:getBioconductorDescription(), "biodesctest2")
        bws = jmemo(lambda:getBioconductorWebscrape(limit=5), "biowebtest1")
        saveMetadata(biod, bws, conn)
        self.assertEqual(oneDbResult(conn, "select group_concat(repository) from packages;"),
            "cran,cran,cran,bioconductor,bioconductor,bioconductor,bioconductor,bioconductor,cran,cran")
        self.assertEqual(oneDbResult(conn, "select lastversion from packages where name='A3'"), "0.9.2")


    def test_get_cran_description(self):
        crand = jmemo(lambda:getCranDescription(), "crandesctest4")
        self.assertIn(crand["pmclust"]["Enhances"], "MixSim")
        self.assertIn(crand["abc"]["License"], "GPL")
        self.assertIn(crand["abc"]["Depends"], "quantreg")
        self.assertEqual( crand["abc"]["Version"][0] , "2.0")

    def test_get_bioconductor_description(self):
        biod = jmemo(lambda:getBioconductorDescription(), "biodesctest2")
        self.assertIn(biod["a4Base"]["Enhances"], "gridSVG")
        self.assertIn(biod["a4Base"]["License"], "GPL-3")
        self.assertIn(biod["a4Base"]["Depends"], "multtest")
        self.assertEqual( biod["a4Base"]["Version"][0] , "1.14.0")

if __name__ == '__main__':
    unittest.main()
