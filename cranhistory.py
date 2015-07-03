from rscraper import *
import pdb
import json
import time
import datetime
import dateutil.parser

with open("credentials.json", "r") as f:
    creds = json.loads(f.read())

getCranHistoricalDependencies(creds)
