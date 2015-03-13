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

def createCranBiocGitTables():
        # Populate in order of least to highest priority:
        # i.e. if we have a project both in Github and CRAN,
        # the cran information takes priority, so write it in
        # last overriding whatever we found on github.

        conn = getConnection("repoScrape.db")
        createMetadataTables(conn)

        gws = extractGitWebscrape(conn)
        gd = extractGitDescription(conn)
        saveMetadata(gd,gws,conn)

        bws = jmemo(lambda:getBioconductorWebscrape(), "biowebtest1")
        biod = jmemo(lambda:getBioconductorDescription(), "biodesctest2")
        saveMetadata(biod, bws, conn)

        cws = jmemo(lambda:getCranWebscrape(), "cranwebtest3")
        crand = jmemo(lambda:getCranDescription(), "crandesctest4")
        saveMetadata(crand, cws, conn)
        fillInDois(conn)

if __name__ == '__main__':
    #createCranBiocGitTables()
    conn = getConnection("repoScrape.db")
    fillInDois(conn)
   
