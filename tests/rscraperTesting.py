import unittest
from nose.plugins.attrib import attr
import rscraper
from rscraper.getRepoMetadata import *
from rscraper.dbutil import *
import json
import os
import inspect
import rscraper.crossref



class RscraperTesting(unittest.TestCase):

    interestingPackages = ["metafor","testthat","Rcpp","ndl", "a4Base","aroma.light", "a4Preproc","abc", "rfUtilities", "pmclust", "A3", "SQUADD", "farms", "XDE", "zoo"]

    def jmemo(self, item, filen):
        try:
            with open(filen + ".json", "r") as f:
                return json.loads(f.read())
        except:
            with open(filen + ".json", "w") as f:
                i = item()
                f.write(json.dumps(i, indent=4))
                return i

    def oneDbResultEquals(self,conn,qry,a): return self.oneDbResultEqual(conn,qry,a)

    def oneDbResultEqual(self, conn, qry, a):
        result = conn.execute(qry)
        r1 = result.next()
        self.assertEqual(str(r1[0]), str(a))
            
    def oneDbResult(self, conn, qry):
        result = conn.execute(qry)
        r1 = result.next()
        return r1[0]
        
    def getconn(self):
        name = inspect.stack()[1][3]
        try:
            os.remove("tests/" + name + ".db")
        except:
            pass
        return getConnection("tests/" + name + ".db")
    
    


if __name__ == '__main__':
    unittest.main()
