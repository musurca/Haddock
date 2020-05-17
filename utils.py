import requests
import json
import csv
import math
import sys
import glob
import os
import webbrowser
from datetime import datetime, timedelta

KEY_PATH = "./key.txt"
LOG_PATH = "./logs/"
LOG_FILE = LOG_PATH + "logs.csv"

# Sailaway API specifies a minimum of 10 minutes between requests
UPDATE_INTERVAL = 600

# UNIT CONVERSIONS
MPS_TO_KTS = 1.944
TIME_FORMAT = "%Y-%m-%d %H-%M-%S"
REQCACHE_FORMAT = "%Y_%m_%d_%H_%M_%S"

class sailaway:
    def __init__(self):
        f = open(KEY_PATH, "r")
        self.key = f.readline()
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

class units:
    def mps_to_kts(mps):
        return mps*MPS_TO_KTS

    def enforceTwoDigits(numStr):
        if len(numStr) == 1:
            return "0"+numStr
        return numStr

class geo:
    def latlon_to_nmea(lat, lon):
        latDeg = lat
        latMin = (latDeg - math.floor(latDeg))*60
        lonDeg = lon
        lonMin = (lonDeg - math.floor(lonDeg))*60
        if latDeg > 0:
            latDir = "N"
        else:
            latDir = "S"
        if lonDeg > 0:
            lonDir = "E"
        else:
            lonDir = "W"
        latMinStr = str(round(latMin,2))
        latMinMajorStr = latMinStr[:latMinStr.find(".")]
        latMinMinorStr = latMinStr[latMinStr.find(".")+1:]
        if len(latMinMajorStr) < 2:
            latMinMajorStr = "0" + latMinMajorStr
        if len(latMinMinorStr) < 2:
            latMinMinorStr = latMinMinorStr + "0"
        latMinStr = latMinMajorStr + "." + latMinMinorStr
        lonMinStr = str(round(lonMin,2))
        lonMinMajorStr = lonMinStr[:lonMinStr.find(".")]
        lonMinMinorStr = lonMinStr[lonMinStr.find(".")+1:]
        if len(lonMinMajorStr) < 2:
            lonMinMajorStr = "0" + lonMinMajorStr
        if len(lonMinMinorStr) < 2:
            lonMinMinorStr = lonMinMinorStr + "0"
        lonMinStr = lonMinMajorStr + "." + lonMinMinorStr

        return str(int(abs(latDeg)))+latMinStr + "," + latDir + "," + str(int(abs(lonDeg)))+lonMinStr + "," + lonDir

    def latlon_to_str(lat, lon):
        latDeg = lat
        latMin = (latDeg - math.floor(latDeg))*60
        lonDeg = lon
        lonMin = (lonDeg - math.floor(lonDeg))*60
        if latDeg > 0:
            latDir = "N"
        else:
            latDir = "S"
        if lonDeg > 0:
            lonDir = "E"
        else:
            lonDir = "W"
        latMinStr = str(round(latMin,2))
        if len(latMinStr) < 5:
            latMinStr = "0" + latMinStr
        lonMinStr = str(round(lonMin,2))
        if len(lonMinStr) < 5:
            lonMinStr = "0" + lonMinStr

        return (latDir + str(int(abs(latDeg))) + "°" + latMinStr + "'", lonDir + str(int(abs(lonDeg))) + "°" + lonMinStr + "'")

        # distance between two global points in nautical miles
    def dist_coord(lat1,lon1,lat2,lon2): 
        # source: https://stackoverflow.com/questions/19412462/getting-distance-between-two-points-based-on-latitude-longitude  
        R = 6373.0 # approximate radius of earth in km
        lat1 = math.radians(lat1)
        lon1 = math.radians(lon1)
        lat2 = math.radians(lat2)
        lon2 = math.radians(lon2)
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return 0.539957*R * c

    # wraps angle to range [0, 360)
    def wrap_angle(b):
        deg = b
        while deg < 0:
            deg = 360+deg
        while deg >= 360:
            deg = deg-360
        return deg

class webviz:
    def loadURL(url):
        webbrowser.open(url)

    def openseamap(lat, lon):
        return "https://map.openseamap.org/?zoom=8&lat=" + lat + "&lon=" + lon + "&mlat=" + lat + "&mlon=" + lon + "&layers=BFTFFFTFFTF0FFFFFFFFFF"

    def pirosail(boatid):
        return "http://piro.biz/tracker/?2d&marineid=" + boatid

    def earthwindmap(lat, lon):
        return "https://earth.nullschool.net/#current/wind/surface/level/orthographic=" + lon + "," + lat + ",3000/loc=" + lon + "," + lat

class db:
    # execute a function on each element of a CSV
    def execute(csvFile, executeFunc):
        with open(csvFile, newline='') as csvfile:
            elements = csv.DictReader(csvfile)
            for element in elements:
                executeFunc(element)

    # return results filtered by a query function, and optionally post-process results
    def query(csvFile, queryFunc, processFunc=None):
        results = []
        with open(csvFile, newline='') as csvfile:
            elements = csv.DictReader(csvfile)
            for element in elements:
                res = queryFunc(element)
                if res[0]:
                    if processFunc != None:
                        processFunc(element, res[1:])
                    results.append(element)
        return results

    # return first element matching query function
    def findFirst(csvFile, queryFunc):
        with open(csvFile, newline='') as csvfile:
            elements = csv.DictReader(csvfile)
            for element in elements:
                if queryFunc(element):
                    return element
        return None

class log:
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
            if delta.seconds < UPDATE_INTERVAL:
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