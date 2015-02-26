import urllib
from analyzeDeps import parseDESCRIPTION


def getCranDescription():
    directory = "http://cran.r-project.org/src/contrib/PACKAGES"
    txt = urllib.urlopen(directory).readlines()
    return parseDESCRIPTION(txt)

def getBioconductorDescription():
    directory = "http://bioconductor.org/packages/3.0/bioc/src/contrib/PACKAGES"
    txt = urllib.urlopen(directory).readlines()
    return parseDESCRIPTION(txt)
