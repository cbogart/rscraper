from rscraper import *
import pdb
import json

conn = getConnection("repoScrape.db")

with open("credentials.json", "r") as f:
    creds = json.loads(f.read())

queryRandomProject(conn, creds)
