from rscraper import *
import pdb

conn = getConnection("test.db")

#update the listing of git projects
#optionally, void git projects that have been touched, and not updated here recently

# Save information about the categorizations that the repos use
createMetadataTables(conn)
biowebscrape = getBioconductorWebscrape()
biodescription = getBioconductorDescription()
crandescription = getCranDescription()
cranwebscrape = getCranWebscrape()
saveMetadata(biodescription, biowebscrape, conn)
saveMetadata(crandescription, cranwebscrape, conn)

# Transfer specialized format of Git tables to 
#gitdescription = extractGitDescription()
#gitwebscrape = extractGitWebscrape()
#saveMetadata(gitdescription, gitwebscrape, conn)

