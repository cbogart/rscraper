from rscraper import *
import pdb
import json
import os

def jmemo(item, filen):
    try:
        with open(filen + ".json", "r") as f:
            return json.loads(f.read())
    except:
        with open(filen + ".json", "w") as f:
            i = item()
            f.write(json.dumps(i, indent=4))
            return i

def assertDbResult(conn, a, qry, msg=""):
    result = conn.execute(qry)
    r1 = result.next()
    assert r1[0] == a, msg + " " + str(a) + " != " + str(r1[0])

def assertEquals(a,b, msg=""):
    assert a == b, msg + " " + str(a) + " != " + str(b)

def assertIn(a,bs, msg=""):
    assert a in bs, msg + " " + str(a) + " not in " + ','.join(bs)

def assertStartsWith(b,a, msg=""):
    assert b.startswith(a), msg + " " + str(b) + " does not start with " + str(a)

def testBioWebscrape():
    bws = jmemo(lambda:getBioconductorWebscrape(limit=5), "biowebtest1")
    assertEquals( bws["a4Base"]["description"] , "Automated Affymetrix Array Analysis", "Webscrape bioc description")
    assertEquals( bws["a4Base"]["repository"] , "bioconductor", "webscrape bioc repository tag")
    assertEquals( bws["a4Base"]["url"] , "http://www.bioconductor.org/packages/release/bioc/html/a4Base.html", "webscrape bioc url")
    assertIn( "Microarray", bws["a4Base"]["views"], "webscrape bioc views")
    assertIn( "Software", bws["a4Base"]["views"], "webscrape bioc views2")
    assertStartsWith( bws["a4Base"]["citation"], "Talloen W, Verbeke", "webscrape bioc citation")

def testBioDescription():
    biod = jmemo(lambda:getBioconductorDescription(), "biodesctest2")
    assertIn( "gridSVG", biod["a4Base"]["Enhances"], "BioDescription bioc Enhances")
    assertIn( "GPL-3", biod["a4Base"]["License"], "BioDescription bioc License")
    assertIn( "multtest", biod["a4Base"]["Depends"], "BioDescription bioc Depends")
    assertEquals( biod["a4Base"]["Version"][0] , "1.14.0", "BioDescription bioc Version")

def testCranWebscrape():
    cws = jmemo(lambda:getCranWebscrape(limit=5), "cranwebtest3")
    assertStartsWith( cws["abc"]["description"], "The package implements several", "Webscrape cran description")
    assertEquals( cws["abc"]["repository"] , "cran", "webscrape cran repository tag")
    assertEquals( cws["abc"]["title"] , "Tools for Approximate Bayesian Computation (ABC)", "webscrape cran title")
    assertEquals( cws["abc"]["url"] , "http://cran.r-project.org/web/packages/abc/index.html", "Webscrape cran url")
    assertIn( "Bayesian", cws["abc"]["views"], "webscrape cran views")
    assertStartsWith( cws["A3"]["citation"],"Scott Fortmann-Roe (2013). Accurate", "webscrape cran citation")

def testCranDescription():
    crand = jmemo(lambda:getCranDescription(), "crandesctest4")
    assertIn( "MixSim" , crand["pmclust"]["Enhances"], "Description cran Enhances")
    assertIn( "GPL" , crand["abc"]["License"], "Description cran License")
    assertIn( "quantreg" , crand["abc"]["Depends"], "Description cran Depends")
    assertEquals( crand["abc"]["Version"][0] , "2.0", "Description cran Version")

def testMetadataPopulate():
    conn = getConnection("test1.db")

    createMetadataTables(conn)
    crand = jmemo(lambda:getCranDescription(), "crandesctest4")
    cws = jmemo(lambda:getCranWebscrape(limit=5), "cranwebtest3")
    saveMetadata(crand, cws, conn)
    assertDbResult(conn,
        "cran,cran,cran,cran,cran",
        "select group_concat(repository) from packages;",
        "Query test failure")

    biod = jmemo(lambda:getBioconductorDescription(), "biodesctest2")
    bws = jmemo(lambda:getBioconductorWebscrape(limit=5), "biowebtest1")
    saveMetadata(biod, bws, conn)
    assertDbResult(conn,
        "cran,cran,cran,bioconductor,bioconductor,bioconductor,bioconductor,bioconductor,cran,cran",
        "select group_concat(repository) from packages;",
        "Query test failure")
    assertDbResult(conn, "0.9.2", "select lastversion from packages where name='A3'", "testMetadataPopulate")

def testAll(internet = False):

    try:
        os.remove("biowebtest1.json")
        os.remove("biodesctest2.json")
        os.remove("cranwebtest3.json")
        os.remove("crandesctest4.json")
    except:
        pass
    
    if (internet):
        testBioWebscrape()
        testBioDescription()
        testCranWebscrape()
        testCranDescription()
    testMetadataPopulate()

testAll()
quit()


conn = getConnection("repoScrape.db")

#update the listing of git projects
#optionally, void git projects that have been touched, and not updated here recently

    
# Save information about the categorizations that the repos use
createMetadataTables(conn)

biowebscrape = jmemo(getBioconductorWebscrape, "bioweb")
biodescription = jmemo(getBioconductorDescription, "biodesc")
crandescription = jmemo(getCranDescription, "crandesc")
cranwebscrape = jmemo(getCranWebscrape, "cranweb")
saveMetadata(biodescription, biowebscrape, conn)
saveMetadata(crandescription, cranwebscrape, conn)

# Transfer specialized format of Git tables to 
gitdescription = jmemo(lambda:extractGitDescription(conn), "gitdesc")
gitwebscrape = jmemo(lambda:extractGitWebscrape(conn), "gitweb")
saveMetadata(gitdescription, gitwebscrape, conn)

