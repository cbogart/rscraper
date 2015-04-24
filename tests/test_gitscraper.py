import unittest
from nose.plugins.attrib import attr
from rscraper import *
import json
import os
import inspect
from rscraperTesting import RscraperTesting


class TestGitscraper(RscraperTesting):

    projects = ["cbogart/scimapClient", "DCBraun/FishCounter", "ropensci/taxize"] #"rforge/BaSTA2.0", 
    
        
    @attr("internet", "github")
    def test_queryGithub(self):
        conn = self.getconn()
        with open("credentials.json", "r") as f:
            creds = json.loads(f.read())
                
        createMetadataTables(conn, eraseCitations=True)
        createFreshGitprojectsTable(conn)
        gitscraper.createGitTables(conn)
        
        print "Querying projects:", '\n'.join(TestGitscraper.projects)
        
        git = gitscraper.gitInit(creds)
        git.per_page = 1
        for p in TestGitscraper.projects:
            print p, "-------------------"
            
            repo = git.search_repositories("repo:" + p)
            #print str(repo)
            gitscraper.insertRepos(repo, conn, [])
            queryParticularProject(conn, creds, p)
        print "========\nGit..."
        clearTaskViews(conn)
        gd = extractGitDescription(conn)
        saveMetadata(gd,makeGitPseudoWebscrape(gd),conn)
        
        self.oneDbResultEquals(conn, 
                               "select tag from tags where package_name='taxize' and tag = 'git/ropensci';", 
                               "git/ropensci")
        #self.oneDbResultEquals(conn, 
        #                       "select tag from tags where package='BaSTA2.0' and tag = 'r-forge/basta';", 
        #                       "r-forge/basta")
        #self.assertIn("package estimates survival and mortality",
        #              self.oneDbResult(conn, 
        #                   r"""select description from packages where name='FishCounter';""", 
        #                   "r-forge/basta"))

        
    def test_parseDescription(self):
        #parse description on DCBraun/FishCounter should not throw "list index out of range"
        pass
        
    def getconn(self):
        name = inspect.stack()[1][3]
        try:
            os.remove("tests/" + name + ".db")
        except:
            pass
        return getConnection("tests/" + name + ".db")
    
    


if __name__ == '__main__':
    #unittest.main()
    import pdb
    pdb.set_trace()
    tester = TestGitscraper()
    tester.test_queryGithub()
    