from rscraper import *
import pdb
import json
import time
import datetime
import dateutil.parser

conn = getConnection("repoScrape.db")

with open("credentials.json", "r") as f:
    creds = json.loads(f.read())

dates = conn.execute("select date(created_at) created from gitprojects group by date(created_at) having count(*) > 5 order by created_at desc;")
delta = datetime.timedelta(days=1)
d = dateutil.parser.parse(dates.next()["created"]).date()
while d <= datetime.datetime.today().date():
    print d
    identifyNewProjects(conn, creds, str(d))
    d += delta
    
try:
    for x in range(0,100000):
        queryRandomProject(conn, creds)
except CaughtUpException:
    print "All caught up"