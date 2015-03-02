from rscraper import *
import pdb
import json
import time

conn = getConnection("repoScrape.db")

with open("credentials.json", "r") as f:
    creds = json.loads(f.read())

for x in range(0,100000):
    queryRandomProject(conn, creds)
    if x%50 == 0:
        print "-----Good time to quit-----"
        time.sleep(1)
        print "-----Resuming!------"
