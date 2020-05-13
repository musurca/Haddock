import requests
import json
import csv
import math
import sys
from datetime import datetime, timedelta

KEY_PATH = "./key.txt"
LOG_PATH = "./logs/logs.csv"

# UNIT CONVERSIONS
MPS_TO_KTS = 1.944
TIME_FORMAT = "%Y-%m-%d %H-%M-%S"

class sailaway:
    def __init__(self):
        f = open(KEY_PATH, "r")
        self.key = f.readline()
        if self.key == "":
            sys.exit("You must first paste your API key into key.txt.")
    
    def query(self):
        try:
            r = requests.get(self.key)
        except requests.exceptions.Timeout:
            sys.exit("Error: connection to Sailaway server timed out.")
        except requests.exceptions.TooManyRedirects:
            sys.exit("Error: cannot connect to Sailaway server.")
        except requests.exceptions.RequestException as e:
            sys.exit("Error: cannot connect to Sailaway server.")
        return json.loads(r.text)

class units:
    def mps_to_kts(mps):
        return mps*MPS_TO_KTS

    def enforceTwoDigits(numStr):
        if len(numStr) == 1:
            return "0"+numStr
        return numStr

class geo:
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
        return (latDir + str(int(abs(latDeg))) + "°" + str(round(latMin,2)) + "'", lonDir + str(int(abs(lonDeg))) + "°" + str(round(lonMin,2)) + "'")

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

class webviz:
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
        db.execute(LOG_PATH, addEntry)

    def processEntry(self, e):
        e['zulu']=datetime.strptime(e['zulu'], TIME_FORMAT)
        if e['boatid'] in self.entries:
            boatlog = self.entries[e['boatid']]
        else:
            boatlog = []
            self.entries[e['boatid']] = boatlog
        boatlog.append(e)

    def zuluTime():
        return datetime.utcnow()
    
    def logTimeToString(entry):
        time = entry['zulu']
        return str(time.year) + "-" + str(time.month) + "-" + str(time.day) + " " + units.enforceTwoDigits(str(time.hour)) + ":" + units.enforceTwoDigits(str(time.minute)) + " UTC"
    
    def write(self, zulu, boat):
        boatid = str(boat['ubtnr'])
        if boatid in self.entries:
            prevEntries = self.entries[boatid]
            lastEntry = prevEntries[len(prevEntries)-1]
            delta = zulu - lastEntry['zulu']
            if delta.seconds < 300:
                return
        zuluStr = zulu.strftime(TIME_FORMAT)
        entry = [boat['ubtnr'], boat['boatname'], zuluStr, boat['latitude'], boat['longitude'], boat['cog'], units.mps_to_kts(boat['sog']), units.mps_to_kts(boat['tws'])]
        with open(LOG_PATH,"a") as csvfile:
            logwriter = csv.writer(csvfile, delimiter=',')
            logwriter.writerow(entry)
        self.processEntry({'boatid':entry[0],'name':entry[1],'zulu':entry[2],'lat':entry[3],'lon':entry[4],'cog':entry[5],'sog':entry[6],'windspd':entry[7]})

    def wipe(self):
        with open(LOG_PATH,"w") as csvfile:
            logwriter = csv.writer(csvfile, delimiter=',')
            logwriter.writerow(['boatid','name','zulu','lat','lon','cog','sog','windspd'])
        self.entries = {}

    def getLog(self, boatid):
        boatidStr = str(boatid)
        if boatidStr in self.entries:
            return self.entries[boatidStr]
        return None