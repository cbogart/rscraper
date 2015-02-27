from rscraper import *
import pdb
import json

conn = getConnection("repoScrape.db")

#update the listing of git projects
#optionally, void git projects that have been touched, and not updated here recently

def jmemo(item, filen):
    try:
        with open(filen + ".json", "r") as f:
            return json.loads(f.read())
    except:
        with open(filen + ".json", "w") as f:
            f.write(json.dumps(item(), indent=4))
    
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

