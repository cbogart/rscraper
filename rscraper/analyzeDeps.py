import os
import json, re
from collections import defaultdict
import pdb

def analyzeImports(sourcefilename):
    """Read the source file to determine what packages/libraries/modules it depends on"""
    extent = os.path.splitext(sourcefilename.lower())[1]

    with open(sourcefilename) as f:
        lines = f.readlines()

    if extent == ".r":  
        content = analyzeImportsR(lines)
    elif extent == ".py" or extent == ".ipy" or extent == ".ipynb":  
        content = analyzeImportsPython(lines)
    elif sourcefilename.endswith("DESCRIPTION"):
        content = analyzeImportsDESCRIPTION(lines)
    else:  
        content = analyzeImportsOther(lines)

    return content

def getMatches(text, regex):
    ans = regex.search(text)
    if ans is None: return []
    else: 
        return list(ans.groups())

def analyzeImportsDESCRIPTION(txt):
    """Assumes DESCRIPTION contains exactly one package description block,
    and returns information from it.  If in fact there are many, it returns
    the first one.  If there are none, throw an error"""
    db = analyzeImportsManyDescriptions(txt)
    return ("R", db[db.keys()[0]])

def parseSections(txt):
    chunk = []
    for line in txt:
        endless = line.replace("\n","")
        if endless.strip() == "":
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
        if line[0] not in (" ", "\t"):
            if (fld != ""):
                yield fld
                fld = ""
        fld = fld + line.strip()
    if fld != "": 
        yield fld

def parseDESCRIPTION(txt):
    def removeParenthetical(dep):
        return dep.split("(")[0].strip()

    db = dict()
    #rawdata = dict()

    for sec in parseSections(txt):
        thissection = dict()
        for fld in parseFields(sec):
            code = fld.split(":")[0]
            rest = fld.split(":", 1)[1]
            rest = rest.strip()
            try:
                restList = [removeParenthetical(r.strip()) for r in rest.split(",")]
            except:
                print(rest)
                pdb.set_trace()
                print(rest)

            thissection[code] = restList
        try:
            db[thissection["Package"][0]] = thissection
        except:
            print "coudn't parse Package name in description"
            print thissection

    return db

def analyzeImportsManyDescriptions(txt):
    deps = parseDESCRIPTION(txt)
    for p in deps:
        deps[p] = list(set([]).union(deps[p].get("Imports",set([]))).union(deps[p].get("Depends", set([]))) - set(["R"]))
    return deps

def calcDependencyClosure(thesedepslist, depdictpkg2list):
    closuresDone = False
    closuresCycle = 0
    newdeps = { dep: depdictpkg2list.get(dep,[]) for dep in thesedepslist }
    while(not closuresDone):
        closuresDone = True
        closuresCycle += 1
        alllhs = set(newdeps.keys())
        allrhs = set([d2 for d1 in newdeps for d2 in newdeps[d1]])
        if len(allrhs) > len(alllhs):
            newdeps = dict(newdeps.items() + \
                  [(r, depdictpkg2list.get(r,[])) for r in allrhs])
            closuresDone = False
    return newdeps


def calcDependencyClosureOld(db):
    """Takes dict of form { p1: [d1, p2], p2: [d3, d4] }
    and returns dict of form { p1: { d1: [], p2: [d3, d4] }, p2: { d3: [], d4: [] }}
    The dict's values are only one more layer deep { k -> [v] }"""
    
    closuresDone = False
    closuresCycle = 0
    pdb.set_trace()
    while(not closuresDone):
        closuresDone = True
        closuresCycle += 1
        for pkg in db:
            newdeps = set(db[pkg])
            for otherpkg in set(db[pkg]):
                if otherpkg in db:
                    newdeps = newdeps.union(set(db[otherpkg]))
            if (newdeps != set(db[pkg])):
                db[pkg] = list(newdeps)
                closuresDone = False
    return db


def analyzeImportsPython(text):
    """Search python text for imports"""
    reImport = re.compile(r"""import\s+([a-zA-Z0-9_.]+)""")
    reFrom = re.compile(r"""from\s+([a-zA-Z0-9_.]+).*import""")
    reComma = re.compile(r"""import\s.*,\s+([a-zA-Z0-9_.]+)""")
    res = []
    for line in text:
        prefix = "".join([p + "." for p in getMatches(line, reFrom)])
        res.extend([prefix + pack for pack in getMatches(line, reImport)]) 
        res.extend([prefix + pack for pack in getMatches(line, reComma)]) 
    return ("python", res)

def analyzeImportsR(text):
    """Search R text for imports"""
    reLibrary = re.compile(r"""library\s*\((\s*[a-zA-Z0-9_.]+\s*)\)""")
    reRequire = re.compile(r"""require\s*\((\s*[a-zA-Z0-9_.]+\s*)\)""")
    res = []
    for line in text:
        res.extend(getMatches(line, reLibrary)) 
        res.extend(getMatches(line, reRequire)) 
    return ("R", res)

def analyzeImportsOther(text):
    return ("UNKNOWN", [])
    pass

