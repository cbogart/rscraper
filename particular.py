from rscraper import *
import pdb
import json
import time
import sys

conn = getConnection("repoScrape.db")

with open("credentials.json", "r") as f:
    creds = json.loads(f.read())

queryParticularProject(conn, creds, sys.argv[1])
