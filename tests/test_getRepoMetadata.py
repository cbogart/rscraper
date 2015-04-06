import unittest
from nose.plugins.attrib import attr
import rscraper
from rscraper.getRepoMetadata import *
from rscraper.dbutil import *
import json
import os
import inspect
import rscraper.crossref
from rscraperTesting import RscraperTesting


class TestRepoMetadata(RscraperTesting):

    def test_unquote(self):
        self.assertEqual("xyzzy", unquote("xyzzy"))
        self.assertEqual("xyzzy", unquote('"xyzzy"'))
        self.assertEqual('"xyzzy', unquote('"xyzzy'))

    def test_do_or_error(self):
        self.assertEqual("4", do_or_error(lambda: "4", "goober"))
        self.assertEqual("goober", do_or_error(lambda: 3/0, "goober"))

    @attr("bioconductor","internet")
    def test_get_bioconductor_webscrape_real(self):
        bws = getBioconductorWebscrape(limitTo = self.interestingPackages)
        self.assertEqual( bws["a4Base"]["description"] , "Automated Affymetrix Array Analysis")
        self.assertEqual( bws["a4Base"]["repository"] , "bioconductor")
        self.assertEqual( bws["a4Base"]["url"] , "http://www.bioconductor.org/packages/release/bioc/html/a4Base.html")
        self.assertIn("Microarray", bws["a4Base"]["views"])
        self.assertIn("Software", bws["a4Base"]["views"])
        self.assertIn("Talloen W, Verbeke", bws["a4Base"]["citation"])
        
    def test_get_bioconductor_webscrape(self):
        bws = self.jmemo(lambda:getBioconductorWebscrape(limitTo = self.interestingPackages), "tests/biowebtest")
        self.assertEqual( bws["a4Base"]["description"] , "Automated Affymetrix Array Analysis")
        self.assertEqual( bws["a4Base"]["repository"] , "bioconductor")
        self.assertEqual( bws["a4Base"]["url"] , "http://www.bioconductor.org/packages/release/bioc/html/a4Base.html")
        self.assertIn("Microarray", bws["a4Base"]["views"])
        self.assertIn("Software", bws["a4Base"]["views"])
        self.assertIn("Talloen W, Verbeke", bws["a4Base"]["citation"])

    #def test_scrape_citation_bioc(self):
        # self.assertEqual(expected, scrapeCitationBioc(name))
        #assert False # TODO: implement your test here

    #def test_scrape_citation_cran(self):
        # self.assertEqual(expected, scrapeCitationCran(name))
        #assert False # TODO: implement your test here

    @attr("cran","internet")
    def test_get_cran_webscrape(self):
        cws = getCranWebscrape(limitTo=self.interestingPackages)
        self.assertIn("The package implements several", cws["abc"]["description"])
        self.assertEqual( cws["abc"]["repository"] , "cran")
        self.assertEqual( cws["abc"]["title"] , "Tools for Approximate Bayesian Computation (ABC)")
        self.assertEqual( cws["abc"]["url"] , "http://cran.r-project.org/web/packages/abc/index.html")
        self.assertIn("Bayesian", cws["abc"]["views"])
        self.assertIn("Scott Fortmann-Roe (2013). Accurate", cws["A3"]["citation"])
        
    def test_get_cran_webscrape_memoized(self):
        cws = self.jmemo(lambda:getCranWebscrape(limitTo = self.interestingPackages), "tests/cranwebtest")
        self.assertIn("The package implements several", cws["abc"]["description"])
        self.assertEqual( cws["abc"]["repository"] , "cran")
        self.assertEqual( cws["abc"]["title"] , "Tools for Approximate Bayesian Computation (ABC)")
        self.assertEqual( cws["abc"]["url"] , "http://cran.r-project.org/web/packages/abc/index.html")
        self.assertIn("Bayesian", cws["abc"]["views"])
        self.assertIn("Scott Fortmann-Roe (2013). Accurate", cws["A3"]["citation"])
        
        
        
    def test_get_pretty_bibtex_authors(self):
        exampleBibtex = r"""
          @Article{,
            author = {Chris J. Stubben and Brook G. Milligan},
            title = {Estimating and Analyzing Demographic Models Using the
              popbio Package in R},
            journal = {Journal of Statistical Software},
            volume = {22},
            number = {11},
            year = {2007},
          }
        """
        self.assertEquals(extractBibtexField(exampleBibtex, "title"), 
                          "Estimating and Analyzing Demographic Models Using the popbio Package in R")
        self.assertEquals(extractBibtexField(exampleBibtex, "year"), "2007")
        self.assertEquals(extractBibtexField(exampleBibtex,"author"), "Chris J. Stubben and Brook G. Milligan")
        self.assertEquals(extractBibtexField(exampleBibtex,"doi"), "")
        
        
        exampleBibtex2 = r"""
          @Article{,
            title = {{solaR}: Solar Radiation and Photovoltaic Systems with
              {R}},
            author = {Oscar Perpi{\~n}{\'a}n},
            journal = {Journal of Statistical Software},
            year = {2012},
            volume = {50},
            number = {9},
            pages = {1--32},
            url = {http://www.jstatsoft.org/v50/i09/},
          }
          """
        self.assertEquals(extractBibtexField(exampleBibtex2,"author"), "Oscar Perpinan")
        
        exampleBibtex3 = r"""
          @Article{,
            title = {Multiple-Table Data in {R} with the {multitable} Package},
            author = {Steven C Walker and Guillaume Gu\'{e}nard and P\'{e}ter
              S\'{o}lymos and Pierre Legendre},
            journal = {Journal of Statistical Software},
            year = {2012},
            volume = {51},
            number = {8},
            pages = {1--38},
            url = {http://www.jstatsoft.org/v51/i08/},
          }
          """
        self.assertEquals(extractBibtexField(exampleBibtex3,"author"), 
            "Steven C Walker and Guillaume Guenard and Peter Solymos and Pierre Legendre")
        self.assertEquals(extractBibtexField(exampleBibtex3,"title"), 
            "Multiple-Table Data in R with the multitable Package")
        
        exampleBibtex4 = r"""
          @Article{,
            title = {openair --- An R package for air quality data analysis},
            author = {David C. Carslaw and Karl Ropkins},
            journal = {Environmental Modelling & Software},
            volume = {27--28},
            number = {0},
            pages = {52--61},
            year = {2012},
            issn = {1364-8152},
            doi = {10.1016/j.envsoft.2011.09.008},
          }
          """
        self.assertEquals(extractBibtexField(exampleBibtex4,"doi"), "10.1016/j.envsoft.2011.09.008")
        
        exampleBibtex5 = r"""
        @Article{,
            title = {Multi-Objective Parameter Selection for Classifiers},
            author = {Christoph M\"ussel and Ludwig Lausser and Markus Maucher
              and Hans A. Kestler},
            journal = {Journal of Statistical Software},
            year = {2012},
            volume = {46},
            number = {5},
            pages = {1--27},
            url = {http://www.jstatsoft.org/v46/i05/},
          }
          """
        self.assertEquals(extractBibtexField(exampleBibtex5, "author"),
                          "Christoph Mussel and Ludwig Lausser and Markus Maucher and Hans A. Kestler")
        
        exampleBibtex6 = r"""
        @Article{,
            title = {{TPmsm}: Estimation of the Transition Probabilities in
              3-State Models},
            author = {Artur Ara{\'u}jo and Lu{\'\i}s Meira-Machado and Javier
              Roca-Pardi{\~n}as},
            journal = {Journal of Statistical Software},
            year = {2014},
            volume = {62},
            number = {4},
            pages = {1--29},
            url = {http://www.jstatsoft.org/v62/i04/},
          }
          """
          
        self.assertEquals(extractBibtexField(exampleBibtex6,"author"), "Artur Araujo and Luis Meira-Machado and Javier Roca-Pardinas")
        
        exampleBibtex7 = r"""
        @Article{,
            title = {{bayesTFR}: An {R} Package for Probabilistic Projections
              of the Total Fertility Rate},
            author = {Hana \v{S}ev\v{c}\'{\i}kov\'{a} and Leontine Alkema and
              Adrian E. Raftery},
            journal = {Journal of Statistical Software},
            year = {2011},
            volume = {43},
            number = {1},
            pages = {1--29},
            url = {http://www.jstatsoft.org/v43/i01/},
          }
          """
        self.assertEquals(extractBibtexField(exampleBibtex7,"author"), "Hana Sevcikova and Leontine Alkema and Adrian E. Raftery")
        
        exampleBibtex8 = r"""
        @Article{,
            title = {Non-homogeneous dynamic Bayesian networks with Bayesian
              regularization for inferring gene regulatory networks with
              gradually time-varying structure},
            author = {F. Dondelinger and S. L\`{e}bre and D. Husmeier},
            year = {2013},
            journal = {Machine Learning},
            volume = {90},
            issue = {2},
            pages = {191-230},
          }
          """
        self.assertEquals(extractBibtexField(exampleBibtex8,"author"), "F. Dondelinger and S. Lebre and D. Husmeier")
        
    def test_extract_doi(self):
        doiexample = """Revell, L. J. (2012) phytools: An R package for phylogenetic comparative biology (and other things). Methods Ecol. Evol. 3 217-223. doi:10.1111/j.2041-210X.2011.00169.x
            Xiaoyong Sun, Kai Wu, Dianne Cook.                PKgraph: An R package for graphically diagnosing population pharmacokinetic models.                Computer Methods and Programs in Biomedicine. May 7, 2011.                 doi:10.1016/j.cmpb.2011.03.016.
            Fang H. dcGOR: an R package for analysing ontologies and protein domain annotations. PLoS Computational Biology 10(10):e1003929, 2014. http://dx.doi.org/10.1371/journal.pcbi.1003929
            """
        doianswer = ["10.1111/j.2041-210X.2011.00169.x", "10.1016/j.cmpb.2011.03.016", "10.1371/journal.pcbi.1003929"]
        self.assertEquals(list(extractDoiFromCitation(doiexample)), doianswer)
        
    def test_fix_doi(self):
        self.assertEquals(fixDoi("http://dx.doi.org/10.4.4.2/hello/10thousa k"), "10.4.4.2/hello/10thousa k")
        self.assertEquals(fixDoi("blorp"),"blorp")
       
        
 
    #def test_recreate_table(self):
        # self.assertEqual(expected, recreateTable(conn, table, flds))
        #assert False # TODO: implement your test here

    #def test_create_metadata_tables(self):
        # self.assertEqual(expected, createMetadataTables(conn))
        # assert False # TODO: implement your test here

    @attr("cran","internet")
    def test_get_cran_description_real(self):
        crand = getCranDescription()
        self.assertIn("MixSim", crand["pmclust"]["Enhances"])
        self.assertIn("GPL", crand["abc"]["License"])
        self.assertIn("quantreg", crand["abc"]["Depends"])
        self.assertEqual("2.0", crand["abc"]["Version"][0] )

    @attr("bioconductor","internet")
    def test_get_bioconductor_description_real(self):
        biod = getBioconductorDescription()
        self.assertIn("gridSVG", biod["a4Base"]["Enhances"])
        self.assertIn("GPL-3", biod["a4Base"]["License"])
        self.assertIn("multtest", biod["a4Base"]["Depends"])
        self.assertEqual("1.14.0" ,  biod["a4Base"]["Version"][0])


    def test_get_cran_description(self):
        crand = self.jmemo(lambda:getCranDescription(), "tests/crandesctest")
        self.assertIn("MixSim", crand["pmclust"]["Enhances"])
        self.assertIn("GPL", crand["abc"]["License"])
        self.assertIn("quantreg", crand["abc"]["Depends"])
        self.assertEqual("2.0", crand["abc"]["Version"][0] )

    def test_get_bioconductor_description(self):
        biod = self.jmemo(lambda:getBioconductorDescription(), "tests/biodesctest")
        self.assertIn("gridSVG", biod["a4Base"]["Enhances"])
        self.assertIn("GPL-3", biod["a4Base"]["License"])
        self.assertIn("multtest", biod["a4Base"]["Depends"])
        self.assertEqual("1.14.0" ,  biod["a4Base"]["Version"][0])
        
    def getconn(self):
        name = inspect.stack()[1][3]
        try:
            os.remove("tests/" + name + ".db")
        except:
            pass
        return getConnection("tests/" + name + ".db")
    
    


if __name__ == '__main__':
    unittest.main()
