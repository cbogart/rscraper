# coding: utf-8
import matplotlib.pyplot
from collections import defaultdict
import pdb
import scipy.stats
from functools import partial

class ImportsTable:
"""For each distinct configuration, stores a weight (usage count) and a 
list of dependencies"""
    def __init__(self):
        self.weight = dict()
        self.import = dict()
        self.users = dict()
    def add(appname, importset, userset, weight=1):
        if (appname not in self.weight):
            self.weight[appname] = weight
            self.importset[appname] = importset
            self.userset[appname] = userset
        else:
            if (self.importset[appname] != importset):
                throw Exception("Imports should be the same for the same app.  Assign a "+
                                "different name to " +  appname + " because " +
                                ",".join(importset) + " is different from " + 
                                ",".join(self.importset[appname])
            self.weight[appname] += weight
            self.userset[appname] = self.userset[appname].union(userset)

def calc_logical_deps():
    # figure logical deps and logical deps users, based on 
    for p1 in programs:
        for p2 in programs:
            if p2 != p1:
                coprojects = programs_project[p1].intersection(programs_project[p2])
                programs_logdeps[p1][p2] = coprojects
                programs_logdeps_users[p1][p2] = set([project_creator[i] for i in coprojects])

calc_logical_deps()
saveState()
   

def calc_fisher(neither, justp1, justp2, both):
  oddsr, pvalue = scipy.stats.fisher_exact([[ neither, justp1 ], [justp2, both]])
  return pvalue

def calc_chisquare(neither, justp1, justp2, both):
  totalNoP1 = neither + justp2
  totalNoP2 = neither + justp1
  totalP1 = both + justp1
  totalP2 = both + justp2
  total = both + justp1 + justp2 + neither
  stat, pvalue = scipy.stats.chisquare([neither, justp1,justp2,both],
        f_exp= [totalNoP1*totalNoP2/total, totalP1*totalNoP2/total,
                totalP2*totalNoP1/total, totalP1*totalP2/total], 
        ddof=2)
  return pvalue

# Do a fisher's exact test for whether
# there's a relationship between programs used in the same project
def related_by_project(p1, p2, maxPvalue):
  total = len(projects)
  both = len(programs_logdeps[p1][p2])
  justp1 = len(programs_project[p1]) - both
  justp2 = len(programs_project[p2]) - both
  neither = total - both - justp1 - justp2
  return maxPvalue >= calc_fisher(neither, justp1, justp2, both)

# Do a fisher's exact test for whether
# there's a relationship between programs used in projects by the same creator
def related_by_user(p1, p2, maxPvalue):
  total = len(projects)
  both = len(programs_logdeps_users[p1][p2])
  justp1 = len(programs_project[p1]) - both
  justp2 = len(programs_project[p2]) - both
  neither = total - both - justp1 - justp2
  return maxPvalue >= calc_fisher(neither, justp1, justp2, both)

def makeHist(caption, dictOfSets):
    #print caption
    #hist = matplotlib.pyplot.hist([len(dictOfSets[x]) for x in dictOfSets])
    #print hist
    #matplotlib.pyplot.show()
    pass

projects = [rec["project.id"] for rec in raw_proj["results"]]
print "Examined %r programs from %r projects " % ( len(programs), len(projects))
makeHist( "Histogram of # of programs with 0, 1, 2, etc. users", programs_users)

def guessLang(progname):
    if progname.endswith(".R") or progname.endswith(".r"):
        lang = "r"
    elif progname.endswith(".py"):
        lang = "python"
    else:
        lang = "unknown"
    return lang
    

try:
    with open('proginfo.pickle') as f:
        lang, progdata = pickle.load(f)
except Exception, e:
    print "Error reading proginfo.pickle: ", str(e)
    print "Programs are:"
    lang = defaultdict(int)
    progdata = dict()
    for prog in programs:
        print prog
        progdata[prog] = dict()
        if prog.startswith("syn"):
            try:
                proginfo = syn.get(prog)
                progdata[prog]["meta"] = dict()
                for p in proginfo.properties:
                    progdata[prog]["meta"][p] = proginfo.properties[p]
                print "   Name:", proginfo.name
                print "   Path:", proginfo.path
                progdata[prog]["path"] = proginfo.path
                lang[guessLang(proginfo.name)] += 1
                progdata[prog]["lang"] = guessLang(proginfo.name)
            except Exception, e2:
                print "   Can't read it:", repr(e2)
                progdata[prog]["error"] = repr(e2)
                progdata[prog]["path"] = prog
        else:
            progdata[prog]["lang"] = guessLang(prog)
            progdata[prog]["path"] = prog
    with open('proginfo.pickle', 'w') as f:
        pickle.dump([lang, progdata], f)
    
print "Language stats: R: ", lang["r"], "   Python: ", lang["python"], "  Other: ", lang["unknown"]

try:
    with open('progImports.pickle') as f:
        prog_imports, lang = pickle.load(f)
except Exception, e:
    prog_imports = dict()
    for prog in progdata:
        print prog,  progdata[prog]["path"]
        try:
            prog_imports[prog] = analyzeImports(progdata[prog]["path"])
            print "\t", prog_imports[prog] 
        except Exception, e3:
            print e3
    with open('progImports.pickle', 'w') as f:
        pickle.dump([prog_imports, lang], f)
    
imports = dict()
for prog in prog_imports:
    for imp in prog_imports[prog]:
        if imp not in imports:
            imports[imp] = 0


print "Examined %r programs from %r projects " % ( len(programs), len(projects))
makeHist( "Histogram of # of programs used in 0, 1, 2, etc. projects", programs_project)

print "%r (=%r%%) forbidden projects (justifies talking to Sage)" % \
         (len(project_forbidden), len(project_forbidden)/len(projects))

def shortname(prog): return prog.split("/")[-1:]
print "-----------------"
print "Logical deps used by more than one project:"
print "   (defined as programs used within the same project)"
print "   Out of ", len(programs), " programs examined"
for p1 in programs_logdeps:
   for p2 in programs_logdeps[p1]:
      if len(programs_logdeps[p1][p2]) > 1 and related_by_project(p1,p2,0.05):
          print "    ", shortname(p1),shortname(p2),len(programs_logdeps[p1][p2])

print "-----------------"
print "Logical deps used by more than one person:"
print "   (defined as programs used by the same user)"
print "   Out of ", len(programs), " programs examined"
for p1 in programs_logdeps_users:
    for p2 in programs_logdeps_users[p1]:
        if len(programs_logdeps_users[p1][p2]) > 1 and related_by_user(p1,p2,0.05):
            print "     ", shortname(p1),shortname(p2),len(programs_logdeps_users[p1][p2])

def invert_dictlist(a_b):
    b_a = dict()
    for a in a_b:
        for b in a_b[a]:
            if b in b_a:
                b_a[b].add(a)
            else:
                b_a[b] = set([a])
    return b_a

def invert_simpledict(a_b):
    return invert_dictlist({ a :  set([a_b[a]]) for a in a_b })

projects_program = invert_dictlist(programs_project)

print "--------"
makeHist("Histogram of # of projects with 0, 1, 2, etc. programs", projects_program)

ancestor_entity = invert_simpledict(entity_ancestor)
makeHist("Histogram of # of projects with 0, 1, 2, etc. objects in them", ancestor_entity)
#!/usr/bin/python

import json
import re
from os import walk
import os
from collections import defaultdict
from datetime import date, timedelta
from datetime import datetime as dt
import datetime
import pdb
import numpy
import json
import cPickle
    
class Tie:
    def __init__(self, v):
        self.v = v
    def __lt__(self, other):
        if (self.v["static"] < other["static"]):
           return True
        elif (self.v["static"] == 0 and other["static"] == 0):
           return self.v["logical"] < other["logical"]
        else:
           return False
    def __gt__(self, other):
        if (self.v["static"] > other["static"]):
           return True
        elif (self.v["static"] == 0 and other["static"] == 0):
           return self.v["logical"] > other["logical"]
        else:
           return False
    def __eq__(self, other):
        if (self.v["static"] == other["static"]):
           return True
        elif (self.v["static"] == 0 and other["static"] == 0):
           return self.v["logical"] > other["logical"]
        else:
           return False
    def toPair(self): return (self.v["static"], self.v["logical"])
    def fromPair(self, p): 
        self.v["static"] = p[0]
        self.v["logical"] = p[1]
   

def clusteringOrder(nodes, links):

    distinctIds = [l["id"] for l in nodes]
    distinctNames = [l["name"] for l in nodes]
    nLabels = nodes
    n = len(nLabels)
    lookup = { nLabels[i]["id"]: i for i in range(0,n) }
    dsm = numpy.zeros((n,n), dtype=('i4,i4'))

    for l in links:
       dsm[lookup[l["source"]], lookup[l["target"]]] = (l["value"]["static"], l["value"]["logical"])

    for i in range(0,n): dsm[i,i] = (500,500)
    g = Graph(dsm, distinctIds)

    g.sortByOutdegree()
    g.tarjan()
    
    #NB: something's horribly wrong with it's neck at this point
    # (g.nLabels has lots of duplicates at the front)
    #
    return sorted(nodes, key=lambda n: g.lookup[n["id"]])

class Graph:
    def __init__(self, dsm, nLabels):
        self.dsm = dsm
        self.nLabels = nLabels
        self.n = len(nLabels)
        self.mkLookup()

    def invariant(self):
        assert self.n == len(self.nLabels), "Not N labels"
        assert self.n == len(set(self.nLabels)), "Not N distinct labels"
 
    def mkLookup(self):
        self.lookup = { self.nLabels[i]: i for i in range(0,self.n) }

    def swapper(self, aname, bname):
        self.invariant()
        a = self.lookup[aname]
        b = self.lookup[bname]
        self.dsm[:, [a,b]] = self.dsm[:, [b,a]]
        self.dsm[[a,b], :] = self.dsm[[b,a], :]
        self.nLabels[a] = bname
        self.nLabels[b] = aname
        self.mkLookup()
        self.invariant()

    def reorderBy(self, newindexing):
        self.invariant()
        self.dsm[:, range(0,self.n)] = self.dsm[:, newindexing]
        self.dsm[range(0,self.n), :] = self.dsm[newindexing, :]
        self.nLabels = {nu: self.nLabels[newindexing[nu]] for nu in range(0,self.n)}
        #self.nLabels = {newindexing[old]: self.nLabels[old] for old in range(0,self.n)}
        self.mkLookup()
        self.invariant()

    def sortByOutdegree(self):
        self.invariant()
        neworder = self.nLabels[:]
        def outdegree(nodename):
            return len(numpy.extract(lambda l: l["static"] > 0 or l["logical"] > 0, self.dsm[self.lookup[nodename],:]))
        neworder = sorted(neworder, key=outdegree)
        self.reorderBy([self.lookup[lab] for lab in neworder])
        self.invariant()

    def strongconnect(self, v):
        n = self.n
        self.indices[v] = self.index
        self.lowlinks[v] = self.index
        self.index += 1
        self.s.append(v)
   
        for w in range(0,n):
            if self.dsm[v,w][0] > 0 or self.dsm[v,w][1] > 0:
                if w not in self.indices:
                    self.strongconnect(w)
                    self.lowlinks[v] = min(self.lowlinks[v], self.lowlinks[w])
                elif w in self.s:
                    self.lowlinks[v] = min(self.lowlinks[v], self.indices[w])
        if self.lowlinks[v] == self.indices[v]:
            self.scc1 = []
            while True:
                w = self.s.pop()
                self.scc1.append(w)
                self.neworder.append(w)
                if (w == v): break
            self.sccs.append(self.scc1) 
  

    def tarjan(self):
        n = self.n
        # Find a root
        
        self.invariant()
        self.indices = dict()
        self.lowlinks = dict()
        self.index = 0
        self.s = []
        self.sccs = []
        self.neworder = []
        for v in range(0,n):
            if v not in self.indices:
                self.strongconnect(v)
        
        self.reorderBy(self.neworder)
        self.invariant()


