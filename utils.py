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
    
    def enforceDigitsLeading(numStr, maxDig):
        digits = len(numStr)
        if digits < maxDig:
            for i in range(maxDig-digits):
                numStr = "0" + numStr
        return numStr
        
    def enforceDigitsTrailing(numStr, maxDig):
        digits = len(numStr)
        if digits < maxDig:
            for i in range(maxDig-digits):
                numStr = numStr + "0"
        return numStr

class geo:
    def nearestSea(lat, lon):
        # true if a is inside the range [b, c]
        def within(a, b, c):
            if b > c:
                c,b=b,c
            return a >= b and a <= c

        def inBbox(e):
            lat0,lon0 = float(e['lat0']),float(e['lon0'])
            lat1,lon1 = float(e['lat1']),float(e['lon1'])
            clat,clon = float(e['clat']),float(e['clon'])
            dist = geo.dist_coord(lat, lon, clat, clon)
            return (within(lat, lat0, lat1) and within(lon, lon0, lon1),dist)

        def saveDist(e, args):
            e['dist'] = args[0]

        def sortDist(e):
            return e['dist']

        seas = db.query("./data/worldseas.csv", inBbox, saveDist)
        seas.sort(key=sortDist)
        if len(seas) > 0:
            return seas[0]['name']
        return ""

    def deg_to_dms(deg, type='lat', fmt='dms'):
        # source: https://stackoverflow.com/questions/2579535/convert-dd-decimal-degrees-to-dms-degrees-minutes-seconds-in-python
        decimals, number = math.modf(deg)
        d = int(number)
        compass = {
            'lat': ('N','S'),
            'lon': ('E','W')
        }
        compass_str = compass[type][0 if deg >= 0 else 1]

        if fmt=='nmea':
            # Formatted for NMEA server
            # [D]DD|MM|.SSS,C
            number_size = {
                'lat': 2,
                'lon': 3
            }
            s, m = math.modf(decimals*60)
            return '{}{}{},{}'.format(str(abs(d)).zfill(number_size[type]), str(int(abs(m))).zfill(2), str(abs(round(s,3)))[1:], compass_str)        
        
        # Formatted for printing to console
        m = int(decimals * 60)
        s = (deg - d - m / 60) * 3600.00
        return '{}{}º{}\'{:.2f}"'.format(compass_str, abs(d), abs(m), abs(s))
        
    def format_sog(sogStr:str):
        decimalLoc = sogStr.find(".")
        if decimalLoc == -1 or decimalLoc == (len(sogStr)-1):
            return "{}.0".format(sogStr.zfill(3))
        
        return "{}.{}".format(sogStr[:decimalLoc].zfill(3), sogStr[decimalLoc+1:decimalLoc+2])

    def latlon_to_nmea(lat, lon):
        return geo.deg_to_dms(lat,'lat','nmea')+","+geo.deg_to_dms(lon,'lon','nmea')

    def latlon_to_str(lat, lon):
        return geo.deg_to_dms(lat,'lat'),geo.deg_to_dms(lon,'lon')

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