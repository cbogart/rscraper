import re

def parseSections(txt):
    chunk = []
    for line in txt.split("\n"):
        endless = line.replace("\n","")
        if endless == "":   #  old way: if endless.strip() == "":
            if (len(chunk) > 0): 
                yield chunk
            chunk = []
        else:
            chunk.append(endless)
    if len(chunk) > 0:
        yield chunk

def parseFields(chunk):
    fld = ""
    for line in chunk:
        if re.match(r"""\S+:""", line):   # old way: line[0] not in (" ", "\t"):
            if (fld != ""):
                yield fld
                fld = ""
        fld = fld + line.strip() + " "
    if fld != "": 
        yield fld

def dcf2dict(txt):
    return listdict2dictdict(parseDCF(txt), "Package")

def listdict2dictdict(listdict, keyfield):
    """Turns a list of dictionaries into a dictionary of dictionaries
    
    Turns [{a:b, x:y},{a:c, x:y}, {a:c, z:w}] into
          {b:{a:b, x:y}, c: {a:c, x:y}, c_2: {a:c, z:w}}
    @param listdict A list of dictionaries
    @param keyfield The key within each inner dict to use as key for the outer dict
    @returns A dict of dicts
    """
    makeunique = 2
    dictdict = {}
    for ld in listdict:
        key = listdict[ld].get(keyfield,"")
        if key in dictdict:
            key = key + "_" + makeunique
            makeunique += 1
        dictdict[key] = listdict[ld]
    return dictdict

def parseDCF(txt):
    """Parses a DCF file (an R package description file)
    
    @param txt The contents of the file as a string
    @returns A list of dicts: the dicts are the key:value pairs for each blank-line-separated segment of the file
    """

    sections = []

    for sec in parseSections(txt):
        thissection = dict()
        for fld in parseFields(sec):
            code = fld.split(":")[0]
            rest = fld.split(":", 1)[1]
            rest = rest.strip()
            thissection[code] = rest  
        sections.append(thissection)
    return sections

def parsePackageReference(packref):
    parts = packref.split("(")
    if len(parts) == 1: return (packref.strip(), "")
    elif len(parts) > 1: return (parts[0].strip(), parts[1].replace(")","").strip())
    else: return ("","")

def DCFparse2DependencyLists(dcfParses):
    dc = {}
    dv = {}
    for p in dcfParses:
        print p["Package"], "..."
        if "Version" not in p:
            print "Bad DESCRIPTION file with no version number"
            return {}
        if not p["Package"] in dc: dc[p["Package"]] = { p["Version"] : 0 }
        if not p["Package"] in dv: dv[p["Package"]] = { p["Version"] : dict() }
        if "Date" in p:
            dc[p["Package"]][p["Version"]] = p["Date"]
        else:
            dc[p["Package"]][p["Version"]] = ""
        for tag in ["Depends","Imports", "Suggests", "Requires"]:
            if tag in p:
                for dep in p[tag].split(","):
                    (depname, depver) = parsePackageReference(dep)
                    if depname not in dv[p["Package"]][p["Version"]]:
                        dv[p["Package"]][p["Version"]][depname] = [(tag, depver)]
                    else:
                        dv[p["Package"]][p["Version"]][depname].append((tag, depver))

    return (dc, dv)

