import re

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

def justAlphabetics(stuff):
    stuff = re.sub(r"[^a-zA-Z0-9]"," ", stuff)
    stuff = re.sub(r"\s+", " ", stuff)
    return stuff

assert stripParentheticals(" asdf (bob) is (the) very (yat (guy) of [it (no)]) e[x]nd") == " asdf   is   very   e nd", \
    stripParentheticals(" asdf (bob) is (the) very (yat (guy) of [it (no)]) end") 

assert justAlphabetics("      x  !  yz  g ") == " x yz g ", justAlphabetics("      x     yz  g ")
