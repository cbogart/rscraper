import re
import time
import datetime
from difflib import SequenceMatcher

def stripParentheticals(stuff):
    oldstuff = ""
    while oldstuff != stuff:
        oldstuff = stuff
        stuff = re.sub(r'\([^\(\)]*\)', " ", stuff)
    oldstuff = ""
    while oldstuff != stuff:
        oldstuff = stuff
        stuff = re.sub(r'\[[^\[\]]*\]', " ", stuff)
        
    return stuff
def ensure_unicode(stuff):
    if type(stuff) is unicode:
        return stuff
    elif isinstance(stuff, str):
        return stuff.decode('utf8')
    elif stuff is None:
        return unicode("")
    else:
        return unicode(stuff)

def epoch2ymd(epoch): return time.strftime('%Y-%m-%d', time.localtime(int(epoch)+0)) 
     
def epoch2ymdhms(epoch):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(epoch)))     

def ymdhms2epoch(dt):
    return int(datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M:%S").strftime("%s"))
    
def ymd2epoch(ymd): return int(datetime.datetime.strptime(ymd, "%Y-%m-%d").date().strftime("%s"))


     
def justAlphabetics(stuff):
    stuff = re.sub(r"[^a-zA-Z0-9]"," ", stuff)
    stuff = re.sub(r"\s+", " ", stuff)
    return stuff

def similar(a, b):     
    return SequenceMatcher(None, a, b).ratio()