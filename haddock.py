'''
    haddock.py

    TODO: delete log entries for defunct boats
    TODO: more log data viz -- distance since <date>? e.g.
    TODO: warning for excessive heeling
    TODO: probably remove boat names from the log
'''

import os
import sys
import math

from rich.console import Console
from rich.table import Column, Table, box
from rich.markdown import Markdown

from utils import sailaway, webviz, log, units, geo

MAX_LOG_ENTRIES = 8

# WIND
forceDescription = ["calm", "light airs", "light breeze", "gentle breeze", "moderate breeze", "fresh breeze", "strong breeze", "near gale", "full gale", "severe gale", "storm", "violent storm", "hurricane"]

windForceTable = [64,56,48,41,34,27,22,17,11,7,4,1]

# HEADINGS
headingNames = ["north", "north by northeast", "northeast", "east by northeast", "east", "east by southeast", "southeast", "south by southeast", "south", "south by southwest", "southwest", "west by southwest", "west", "west by northwest", "northwest", "north by northwest"]

sailAttitudes = ["`in irons`","beating", "on a near reach", "on a reach", "on a broad reach", "running"]

# Converts a wind speed in knots to its corresponding Force level
def windSpeedToForceLevel(w):
    for i in range(len(windForceTable)):
        if w >= windForceTable[i]:
            return 12-i

def windForceToDesc(f):
    forceStr = "F" + str(f)
    if f > 9:
        forceStr = "`" + f + "`"
    elif f > 7:
        forceStr = "**" + f + "**"
    return forceStr

# wraps angle to range [0, 360)
def wrap_angle(b):
    deg = b
    while deg < 0:
        deg = 360+deg
    while deg >= 360:
        deg = deg-360
    return deg

# true if b is within (a-r, a+r]
def withinAngleRange(b, a, r):
    mina = a-r
    maxa = a+r
    if b > mina and b <= maxa:
        return True
    return False

# returns the description of the heading
def headingDesc(h):
    for i in range(len(headingNames)):
        if withinAngleRange(h, i*22.5, 11.25):
            return headingNames[i]

def sailAttitudeDesc(windAng):
    for i in range(len(sailAttitudes)):
        if withinAngleRange(windAng, i*30, 30):
            return sailAttitudes[i]

console = Console()

# get boat info from Sailaway API
api = sailaway()
boats = api.query()

# initialize our log
logbook = log()
logTime = log.zuluTime()

while True:
    for i in range(len(boats)):
        boat = boats[i]
        boatSpeed = int(round(units.mps_to_kts(boat['sog']),0))
        windSpeed = int(round(units.mps_to_kts(boat['tws']),0))
        windDirection = wrap_angle(boat['twd'])
        #windAngle = wrap_angle(180+windDirection)
        windForce = windSpeedToForceLevel(windSpeed)
        windForceStr = windForceToDesc(windForce)
        # sometimes these values are negative!
        sailAtt = sailAttitudeDesc(abs(boat['twa']))

        boatLat, boatLon = geo.latlon_to_str(boat['latitude'], boat['longitude'])

        boatHdg = wrap_angle(boat['cog'])
        headingTxt = headingDesc(boatHdg)

        voyageStr = boat['voyage']
        voyDiv = voyageStr.find(" -> ")
        origin = voyageStr[0:voyDiv]
        dest = voyageStr[voyDiv+4:]

        console.print(Markdown("# (" + str(i) + ") *" + boat['boatname'] + "* - " + boat['boattype']))
        console.print(Markdown("**Destination:**\t" + dest))
        console.print(Markdown("**Position:**\t" + boatLat + ", " + boatLon))
        console.print(Markdown("**Conditions:**\t" + windForceStr + " - " + forceDescription[windForce] + " from " + headingDesc(windDirection) + " at " + str(round(windSpeed,1)) + " knots "))
        console.print(Markdown("**Heading:**\t" + str(int(round(boatHdg,0))) + "° (" + headingTxt + ") at " + str(boatSpeed) + " knots, " + sailAtt))
        logbook.write(logTime, boat)
        print("")

    boatNum = input("Enter boat # (or press return to quit): ")
    try:
        boatNum = int(boatNum)
    except ValueError:
        sys.exit()

    if boatNum >= 0 and boatNum < len(boats):
        boat = boats[boatNum]
        while True:
            console.print(Markdown("# *" + boat['boatname'] + "* - " + boat['boattype']))
            console.print(Markdown("**(1)** `Read the logbook`"))
            console.print(Markdown("**(2)** `Plot position on OpenSeaMap`"))
            console.print(Markdown("**(3)** `Plot position on EarthWindMap`"))
            print("")
            choice = input("Enter # of option (or press return to go back): ")
            try:
                choice = int(choice)
            except ValueError:
                break
            if choice == 1:
                console.print(Markdown("# *" + boat['boatname'] + "* - Captain's Log"))
                entries = logbook.getLog(boat['ubtnr'])
                if len(entries) > MAX_LOG_ENTRIES:
                    showEntries = entries[len(entries)-MAX_LOG_ENTRIES:]
                else:
                    showEntries = entries
                for entry in showEntries:
                    boatLat, boatLon = geo.latlon_to_str(float(entry['lat']), float(entry['lon']))
                    console.print(Markdown("**" + log.logTimeToString(entry) + "** - *" + boatLat + ", " + boatLon + "*"))
                    console.print(Markdown("### Heading " + headingDesc(wrap_angle(float(entry['cog']))) + " / " + str(int(round(float(entry['sog']),0))) + " knots / " + forceDescription[windSpeedToForceLevel(float(entry['windspd']))]))
                    print("")
                if len(entries) > 2:
                    firstTime = entries[0]['zulu']
                    lastTime = entries[len(entries)-1]['zulu']
                    totalTimeHrs = (lastTime - firstTime).seconds / (60*60)
                    dist = 0
                    for i in range(len(entries)-1):
                        index = i+1
                        curEntry, prevEntry = entries[index], entries[i]
                        curLat, curLon = float(curEntry['lat']), float(curEntry['lon'])
                        prevLat, prevLon = float(prevEntry['lat']), float(prevEntry['lon'])
                        dist += geo.dist_coord(curLat, curLon, prevLat, prevLon)
                    rate = round(dist / totalTimeHrs,1)
                    console.print(Markdown("**Distance logged:** " + str(round(dist,1)) + " nm"))
                    console.print(Markdown("**Average speed:** " + str(rate) + " knots"))
                    print("")
                input("(Press any key to continue)")
            elif choice == 2 or choice == 3:
                boatLat = str(round(boat['latitude'],4))
                boatLon = str(round(boat['longitude'],4))
                if choice == 2:
                    url = webviz.openseamap(boatLat, boatLon)
                else:
                    url = webviz.earthwindmap(boatLat, boatLon)
                os.system("open \"" + url + "\"")