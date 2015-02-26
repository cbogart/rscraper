import json


def loadCredentials(credfile):
    with open(credfile) as f:
        credentials = json.load(f)
    return credentials


    
