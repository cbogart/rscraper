import rscraper


conn = getConnection("test.db")

#update the listing of git projects
#optionally, void git projects that have been touched, and not updated here recently

# Save information about the categorizations that the repos use
createMetadataTables(conn)
biometadata = getBioconductorMetadata()
biopackages = getBioconductorPackageInfo()
cranpackages = getCranPackageInfo()
cranmetadata = getCranMetadata()
saveMetadata(biopackages, biometadata, conn)
saveMetadata(cranpackages, cranmetadata, conn)

# Transfer specialized format of Git tables to 
gitpackages = extractGitPackageInfo()
gitmetadata = extractGitMetadata()
saveMetadata(gitpackages, gitmetadata, conn)

