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

def do_weekly():
        bws = jmemo(lambda:getBioconductorWebscrape(limit=5), "biowebtest1")
        cws = jmemo(lambda:getCranWebscrape(limit=5), "cranwebtest3")
        biod = jmemo(lambda:getBioconductorDescription(), "biodesctest2")
        crand = jmemo(lambda:getCranDescription(), "crandesctest4")

        conn = getConnection("test42.db")
        createMetadataTables(conn)
        saveMetadata(crand, cws, conn)
        saveMetadata(biod, bws, conn)

        gws = extractGitWebscrape(conn)
        gd = extractGitDescription(conn)
        saveMetadata(gd,gws,conn)

if __name__ == '__main__':
    do_weekly()
