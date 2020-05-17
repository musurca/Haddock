'''
    utils.py

    General utility functions: unit conversions, great-circle
    distances, CSV queries, platform-independent web browsing.
'''

import csv
import math
import webbrowser

# UNIT CONVERSIONS
MPS_TO_KTS = 1.944

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