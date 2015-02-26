directory = "http://cran.r-project.org/src/contrib/PACKAGES"
import urllib

def getCranPackageInfo():
    directory = "http://cran.r-project.org/src/contrib/PACKAGES"
    txt = urlopen(directory).readlines()
    return txt

def getBioconductorPackageInfo():
    directory = "http://bioconductor.org/packages/3.0/bioc/src/contrib/PACKAGES"
    txt = urlopen(directory).readlines()
    return txt
