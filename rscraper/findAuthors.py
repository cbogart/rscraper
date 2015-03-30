'''
Created on Mar 30, 2015

@author: bogart-MBP-isri
'''
from rscraper.getRepoMetadata import recreateTable
import re

def findAuthors(conn):
    recreateTable(conn, "authors", "package_name string, author_name string")
    authors = []
    for package in conn.execute("select * from packages"):
        package_name = package["packages.name"]
        authlist = package["packages.authors"]
        authlist = authlist.replace("\n"," ")
        authlist = authlist.replace("\n"," ")
        authlist = re.sub(r"\[.*?\]","", authlist)
        authlist = re.sub(r"\(.*?\)","", authlist)
        auths = re.split(",|(?: and )", authlist)
        auths = [re.sub(r".*\bby\b(.*)", r"\1", auth) for auth in auths]
        auths = [re.sub(r".*\bfrom\b(.*)", r"\1", auth) for auth in auths]
        auths = [re.sub(r"^'(.*)'$", r"\1", auth) for auth in auths]
        auths = [re.sub(r'"^"(.*)"$"', r"\1", auth) for auth in auths]
        authors.extend([(package_name, auth.strip()) for auth in auths if auth.strip() != ''])
    conn.executemany("insert into authors (package_name, author_name) values (?,?);", authors)
    conn.commit()
    
