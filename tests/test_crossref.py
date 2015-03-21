# -*- coding: UTF-8 -*-
import unittest
from nose.plugins.attrib import attr
import rscraper
from rscraper.dbutil import *
import json
import os
import inspect
import rscraper.crossref
from rscraperTesting import RscraperTesting


class TestCrossref(RscraperTesting):


    def test_parseCitationText(self):
        squadd = r"""
Sankar M, Hardtke sbC and Xenarios I (2012).
SQUADD: Add-on of the SQUAD Software.
R package version 1.16.0, http://www.unil.ch/dbmv/page21142_en.html.
"""
        affym = r"""
Hochreiter S, Clevert D and Obermayer K (2006).
“A new summarization method for affymetrix probe level data.”
Bioinformatics, 22(8), pp. 943–949.
http://bioinformatics.oxfordjournals.org/cgi/content/abstract/22/8/943.
"""
        genes = r"""
Scharpf RB, Tjelmeland H, Parmigiani G and Nobel A (2009).
“A Bayesian model for cross-study differential gene
expression.”
JASA.
10.1198/jasa.2009.ap07611.
"""
        (auths,title,year) = rscraper.crossref.guessAuthorTitleYearFromCitationString(squadd)
        self.assertEqual(year, "2012")
        self.assertEqual(auths, "Sankar M, Hardtke sbC and Xenarios I")
        self.assertEqual(title, "SQUADD: Add-on of the SQUAD Software")
        (auths,title,year) = rscraper.crossref.guessAuthorTitleYearFromCitationString(affym)
        self.assertEqual(year, "2006")
        self.assertEqual(auths, "Hochreiter S, Clevert D and Obermayer K")
        self.assertEqual(title, "A new summarization method for affymetrix probe level data")
        (auths,title,year) = rscraper.crossref.guessAuthorTitleYearFromCitationString(genes)
        self.assertEqual(year, "2009")
        self.assertEqual(auths, "Scharpf RB, Tjelmeland H, Parmigiani G and Nobel A")
        self.assertEqual(title, "A Bayesian model for cross-study differential gene expression")
        

if __name__ == '__main__':
    unittest.main()
