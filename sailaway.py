'''
    sailaway.py

    Queries the Sailaway servers, caches responses, and maintains
    local sailing logbook.
'''
import requests
import json
import csv
import sys
import glob
import os
from datetime import datetime

from utils import db, units, geo

KEY_PATH = "./key.txt"
LOG_PATH = "./logs/"
LOG_FILE = LOG_PATH + "logs.csv"

# Sailaway API specifies a minimum of 10 minutes between requests
UPDATE_INTERVAL = 600

TIME_FORMAT = "%Y-%m-%d %H-%M-%S"
REQCACHE_FORMAT = "%Y_%m_%d_%H_%M_%S"

class sailaway:
    def __init__(self):
        f = open(KEY_PATH, "r")
        self.key = f.readline().rstrip()
        if self.key == "":
            sys.exit("You must first paste your API key into key.txt.")
        self.lastUpdate = None

    # clears cache and writes latest update to it
    def writeReqCache(self, req):
        for file in glob.glob(LOG_PATH + "*.json"):
            os.remove(file)
        curTime = datetime.utcnow()
        reqFile = open(LOG_PATH + curTime.strftime(REQCACHE_FORMAT) + ".json", "w")
        reqFile.write(req)
        reqFile.close()
        self.lastUpdate = curTime

    # return (last update in seconds, path to latest cache file)
    def lastCacheFile(self):
        newestLogTime = 99999
        newestLog = ""
        curTime = datetime.utcnow()
        prevReqList = glob.glob(LOG_PATH + "*.json")
        if len(prevReqList) > 0:
            for f in prevReqList:
                reqTimeStr = f[f.find(LOG_PATH)+len(LOG_PATH):f.find(".json")]
                try:
                    reqTime = datetime.strptime(reqTimeStr, REQCACHE_FORMAT)
                except ValueError:
                    continue
                timeDiff = (curTime - reqTime).total_seconds()
                if timeDiff < newestLogTime:
                    newestLogTime = timeDiff
                    newestLog = f
                    self.lastUpdate = reqTime
        return (newestLogTime, newestLog)
    
    # returns true if query can be run usefully
    def canUpdate(self):
        if self.lastUpdate != None:
            return (datetime.utcnow() - self.lastUpdate).total_seconds() >= UPDATE_INTERVAL
        return True

    def query(self):
        reqText = ""
        # first, check cache to see how old the previous request is
        lastTime, lastReqFile = self.lastCacheFile()
        if lastTime < UPDATE_INTERVAL:
            reqFile = open(lastReqFile, "r")
            reqText = reqFile.read()
            reqFile.close()
        # If we didn't have any recent data cached, request it
        if reqText == "":
            try:
                r = requests.get(self.key)
            except requests.exceptions.Timeout:
                sys.exit("Error: Connection to Sailaway server timed out. Please try again later.")
            except requests.exceptions.TooManyRedirects:
                sys.exit("Error: Cannot connect to Sailaway server. Please try again later.")
            except requests.exceptions.RequestException as e:
                sys.exit("Error: Cannot connect to Sailaway server. Check your internet connection.")
            reqText = r.text
            self.writeReqCache(reqText)
        
        boats = json.loads(reqText)

        # sort boats by ID and return them
        def sortById(b):
            return b['ubtnr']
        if len(boats) > 0:
            boats.sort(key=sortById)
        return boats

    def updateInterval():
        return UPDATE_INTERVAL

class saillog:
    def __init__(self):
        self.entries={}
        def addEntry(e):
            self.processEntry(e)
        db.execute(LOG_FILE, addEntry)

    def processEntry(self, e):
        e['zulu']=datetime.strptime(e['zulu'], TIME_FORMAT)
        if e['boatid'] in self.entries:
            boatlog = self.entries[e['boatid']]
        else:
            boatlog = []
            self.entries[e['boatid']] = boatlog
        boatlog.append(e)
    
    def logTimeToString(entry):
        time = entry['zulu']
        return str(time.year) + "-" + str(time.month) + "-" + str(time.day) + " " + units.enforceTwoDigits(str(time.hour)) + ":" + units.enforceTwoDigits(str(time.minute)) + " UTC"
    
    def write(self, zulu, boat):
        boatid = str(boat['ubtnr'])
        if boatid in self.entries:
            prevEntries = self.entries[boatid]
            lastEntry = prevEntries[len(prevEntries)-1]
            delta = zulu - lastEntry['zulu']
            if delta.seconds < sailaway.updateInterval():
                return
        zuluStr = zulu.strftime(TIME_FORMAT)
        entry = [boat['ubtnr'], boat['boatname'], zuluStr, boat['latitude'], boat['longitude'], geo.wrap_angle(boat['cog']), units.mps_to_kts(boat['sog']), units.mps_to_kts(boat['tws'])]
        with open(LOG_FILE,"a") as csvfile:
            logwriter = csv.writer(csvfile, delimiter=',')
            logwriter.writerow(entry)
        self.processEntry({'boatid':entry[0],'name':entry[1],'zulu':entry[2],'lat':entry[3],'lon':entry[4],'cog':entry[5],'sog':entry[6],'windspd':entry[7]})

    def wipe(self):
        with open(LOG_FILE,"w") as csvfile:
            logwriter = csv.writer(csvfile, delimiter=',')
            logwriter.writerow(['boatid','name','zulu','lat','lon','cog','sog','windspd'])
        self.entries = {}

    def getLog(self, boatid):
        boatidStr = str(boatid)
        if boatidStr in self.entries:
            return self.entries[boatidStr]
        return None