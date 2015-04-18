import unittest
from nose.plugins.attrib import attr
import rscraper
from rscraper.getRepoMetadata import *
from rscraper.dbutil import *
import json
import os
import inspect
from rscraper.gitscraper import *
from rscraperTesting import RscraperTesting


class TestGitscraper(RscraperTesting):

    projects = ["rforge/BaSTA2.0", "cbogart/scimapClient"]
    
    @attr("internet", "github")
    def test_queryGithub(self):
        return self.helper_test_queryGithub(queryInternet = True)
    
    def test_queryGithub_offline(self):
        return self.helper_test_queryGithub(queryInternet = False)
        
    def helper_test_queryGithub(self, queryInternet = False):
        conn = self.getconn()
        with open("credentials.json", "r") as f:
            creds = json.loads(f.read())
                
        createMetadataTables(conn, eraseCitations=True)
    
        for p in TestGitscraper.projects:
            queryParticularProject(conn, creds, p)
    
        
    def getconn(self):
        name = inspect.stack()[1][3]
        try:
            os.remove("tests/" + name + ".db")
        except:
            pass
        return getConnection("tests/" + name + ".db")
    
    


if __name__ == '__main__':
    unittest.main()
