import rscraper



#update the listing of git projects
#optionally, void git projects that have been touched, and not updated here recently
biotasks = getBioconductorTasks()
crantasks = getCranTasks()
biopackages = getBioconductorPackageInfo()
cranpackages = getCranPackageInfo()
#update the listing of CRAN packages
#update the listing of Bioconductor packages

