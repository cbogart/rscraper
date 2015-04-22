'''
Created on Apr 20, 2015

@author: bogart-MBP-isri
'''
import datetime
import os
import urllib
import time

def downloadDownloadsCacheDir():
    dirname = "downloadsCache"
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    return dirname

def downloadDownloadDataForDate(theDate):
    """Download Rstudio download statistics file for date theDate
    
    @param theDate   Date in datetime format
    @returns Nothing: just downloads the file
    """
    fn = str(theDate) + ".csv.gz"
    yr = fn[0:4]
    print "Downloading", fn
    time.sleep(1)
    urllib.urlretrieve("http://cran-logs.rstudio.com/" + yr + "/" + fn, downloadDownloadsCacheDir() + "/" + fn)
    
def newestCacheDate():
    """Finds the most recent date for which we have rstudio download data
    
    @returns Date in datetime format
    """
    files = os.listdir(downloadDownloadsCacheDir())
    if (files == []): 
        return datetime.date(2012,9,30)
    newest = sorted(files)[-1]
    thedate = datetime.datetime.strptime(newest[0:10], "%Y-%m-%d").date()
    return thedate
    
    
def downloadLatestRstudioLogs():
    delta = datetime.timedelta(days=1)
    d = newestCacheDate() + delta
    while d <= datetime.date.today():
        print d
        downloadDownloadDataForDate(d)
        d += delta

if __name__ == '__main__':
    downloadLatestRstudioLogs()