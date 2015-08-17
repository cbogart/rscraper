import re
import dateutil.parser

class DCFFormatError(Exception):
    pass

def parseSections(txt, r_description_file=True):
    """@param: r_description_file: assume it's all one section"""
    if r_description_file:
        yield [t.replace("\n", "") for t in txt.split("\n") if len(t) > 0]
    else:

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

def parseDCF(txt, r_description_file=True):
    """Parses a DCF file (an R package description file)
    
    @param txt The contents of the file as a string
    @param r_description_file True if we're reading R packages, which allow empty lines (unlike the standard)
    @returns A list of dicts: the dicts are the key:value pairs for each blank-line-separated segment of the file
    """

    sections = []

    for sec in parseSections(txt, r_description_file):
        thissection = dict()
        for fld in parseFields(sec):
            code = fld.split(":")[0]
            try:
                rest = fld.split(":", 1)[1]
            except Exception, e:
                raise DCFFormatError("Empty key: " + code)
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
    da = {}
    dc = {}
    dv = {}
    for p in dcfParses:
        if "Version" not in p or "Package" not in p:
            if "Bundle" not in p:
                print "Bad DESCRIPTION file ", p
            continue
        package = p["Package"]
        version = p["Version"]
        da[package] = p.get("Maintainer", p.get("Author", ""))
        if not package in dc: dc[package] = { version : 0 }
        if not package in dv: dv[package] = { version : dict() }
        if not version in dc[package]: dc[package][version] = dateutil.parser.parse("1900-01-01")
        if not version in dv[package]: dv[package][version] = dict()
        if "Date" in p:
            dc[package][version] = p["Date"]
        elif "Date/Publication" in p:
            dc[package][version] = p["Date/Publication"]
        elif "Packaged" in p:
            dc[package][version] = p["Packaged"].split(";")[0]
        else:
            dc[package][version] = ""

        try:
            dc[package][version] = dateutil.parser.parse(dc[package][version])
        except:
            dc[package][version] = dateutil.parser.parse("1901-01-01")
       
        for tag in ["Depends","Imports", "Requires"]:   # Suggests
            if tag in p:
                for dep in p[tag].split(","):
                    (depname, depver) = parsePackageReference(dep)
                    if depname not in dv[package][version]:
                        dv[package][version][depname] = [(tag, depver)]
                    else:
                        dv[package][version][depname].append((tag, depver))

    return (da, dc, dv)

