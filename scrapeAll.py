from rscraper import *
import pdb
import json
import time
import datetime
import dateutil.parser

conn = getConnection("caches/repoScrape.db")

with open("config/credentials.json", "r") as f:
    creds = json.loads(f.read())

dates = conn.execute(r"""select date(created_at) created from gitprojects 
                        group by date(created_at) having count(*) > 5 
                        order by created_at desc;""")
delta = datetime.timedelta(days=1)
d = dateutil.parser.parse(dates.next()["created"]).date()
while d <= datetime.datetime.today().date():
    print d
    identifyNewProjects(conn, creds, str(d))
    d += delta
    
try:
    for x in range(0,100000):
        queryRandomProject(conn, creds)
except CaughtUpException:
    print "All caught up"

# Check new downloads from R studio    
downloadLatestRstudioLogs()


def createCranBiocGitTables(conn):
        """Create a table of R packages from CRAN, Bioconductor, and Github.

        Use previously-scraped information about github R projects to populate
        a table of packages ("packages" are defined as github projects that are
        in R and contain a DESCRIPTION file).
        
        Overwrite that information with packages scraped from Bioconductor, then
        again from CRAN.  Thus Cran takes priority over Bioconductor, and both
        take priority over Github.

        Finally, fill in citation information as best as can be scraped from
        the Bioconductor and CRAN sites, and then look them up in Scopus to find
        out how often they have been cited.
        """
        createMetadataTables(conn)
        clearTaskViews(conn)
        print "Git..."
        gd = extractGitDescription(conn)
        saveMetadata(gd,makeGitPseudoWebscrape(gd),conn)
        print "Bioconductor...****************************"
        bws = jmemo(lambda:getBioconductorWebscrape(), "caches/bioc_web_scrape", 30)
        biod = jmemo(lambda:getBioconductorDescription(), "caches/bioc_desc_scrape",10)
        saveMetadata(biod, bws, conn)
        print "CRAN...*************************"
        cws = jmemo(lambda:getCranWebscrape(), "caches/cran_web_scrape", 30)
        crand = jmemo(lambda:getCranDescription(), "caches/cran_desc_scrape",10)
        saveMetadata(crand, cws, conn)
        print "CROSSREF*********************"
        crossref.extractAuthorTitleFromCitations(conn)
        crossref.fillInAuthorTitleFromPackage(conn)
        print "FillINDOIs*********************"
        fillInDois(conn)
        print "SCOPUS***********************"
        enable_scopus_proxy(False)
        doScopusLookup(conn)

createCranBiocGitTables(conn)
