# -*- coding: UTF-8 -*-
import unittest
from nose.plugins.attrib import attr
import rscraper
from rscraper.dbutil import *
import json
import os
import inspect
from rscraper.utils import *
from rscraperTesting import RscraperTesting


class TestUtils(RscraperTesting):

    def test_date_utils(self):
        self.assertEqual(ymdhms2epoch("2015-04-16 19:47:57"), 1429228077)
        self.assertEqual(epoch2ymdhms(1429228077), "2015-04-16 19:47:57")
        self.assertEqual(ymd2epoch("2015-04-16"), 1429156800)
        self.assertEqual(epoch2ymd(1429156800), "2015-04-16")
        
    def test_strip_parentheticals(self):
        self.assertEquals(stripParentheticals(" asdf (bob) is (the) very (yat (guy) of [it (no)]) e[x]nd")," asdf   is   very   e nd")
        
    def test_just_alphabetics(self):
        self.assertEquals(justAlphabetics("      x  !  yz  g "), " x yz g ")

        

if __name__ == '__main__':
    unittest.main()
