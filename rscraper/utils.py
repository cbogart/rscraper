import re
import time
import datetime
from difflib import SequenceMatcher
import os
import json

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

def jmemo(item, filen, age=None):
    """Persistently memoize a function returning a json object

    @param item   A function that uses an expensive resource, and returns json
    @param filen  A filename to use for memoization
    @param age    Delete cache file if older than this many days (None = keep forever)
    @returns      The contents of the file; if it does not exist, it is created from item()
    """
    filename = filen+".json"
    if age is not None \
            and os.path.isfile(filename) \
            and os.path.getmtime(filename) < int(time.time()) - (age*24*3600):
        os.remove(filename)
    try:
        with open(filename, "r") as f:
            return json.loads(f.read())
    except:
        with open(filename, "w") as f:
            i = item()
            f.write(json.dumps(i, indent=4))
            return i
     
def justAlphabetics(stuff):
    stuff = re.sub(r"[^a-zA-Z0-9]"," ", stuff)
    stuff = re.sub(r"\s+", " ", stuff)
    return stuff

def similar(a, b):     
    return SequenceMatcher(None, a, b).ratio()