'''
    haddock.py

    TODO: delete log entries for defunct boats
    TODO: more log data viz -- distance since <date>? e.g.
    TODO: probably remove boat names from the log
    TODO: compress log with zlib
    TODO: for destructive log changes, do work in temp then copy over
'''

import os
import sys
import math

from rich.console import Console
from rich.markdown import Markdown

from sailaway import saillog
from nmea import NMEAUpdater
from utils import webviz, units, geo

MAX_LOG_ENTRIES = 8

# WIND
forceDescription = ["calm", "light airs", "light breeze", "gentle breeze", "moderate breeze", "fresh breeze", "strong breeze", "near gale", "full gale", "severe gale", "storm", "violent storm", "hurricane"]

windForceTable = [64,56,48,41,34,27,22,17,11,7,4,1]

# HEADINGS
headingNames = ["north", "north by northeast", "northeast", "east by northeast", "east", "east by southeast", "southeast", "south by southeast", "south", "south by southwest", "southwest", "west by southwest", "west", "west by northwest", "northwest", "north by northwest", "north"]

sailAttitudes = ["`in irons`","beating", "on a close reach", "on a reach", "on a broad reach", "running"]

# Converts a wind speed in knots to its corresponding Force level
def windSpeedToForceLevel(w):
    for i in range(len(windForceTable)):
        if w >= windForceTable[i]:
            return 12-i

def windForceToDesc(f):
    if f >= 0 and f < len(forceDescription):
        return forceDescription[f]
    return "Unknown"

def windForceToStr(f):
    forceStr = "F" + str(f)
    if f > 9:
        forceStr = "`" + forceStr + "`"
    elif f > 7:
        forceStr = "**" + forceStr + "**"
    return forceStr

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

port = 10110

def printArgs():
    sys.exit("\nusage: haddock [port number]\n\nPort number is 10110 by default.\n")

if len(sys.argv) > 1:
    port = sys.argv[1]
    try:
        port = int(port)
    except ValueError:
        printArgs()

console = Console()

# Initialize our NMEA server & background updater
updater = NMEAUpdater(port)
updater.start()

# Initialize our logbook
logbook = updater.getLogbook()

while True:
    boats = updater.getBoats()

    for i in range(len(boats)):
        boat = boats[i]
        boatSpeed = int(round(units.mps_to_kts(boat['sog']),0))
        boatLat, boatLon = geo.latlon_to_str(boat['latitude'], boat['longitude'])
        boatHdg = geo.wrap_angle(boat['cog'])
        headingTxt = headingDesc(boatHdg)
        heelAngle = abs(int(round(boat['heeldegrees'],0)))

        voyageStr = boat['voyage']
        voyDiv = voyageStr.find(" -> ")
        origin = voyageStr[0:voyDiv]
        dest = voyageStr[voyDiv+4:]
        locName = geo.nearestSea(boat['latitude'], boat['longitude'])

        windSpeed = int(round(units.mps_to_kts(boat['tws']),0))
        windDirection = geo.wrap_angle(boat['twd'])
        windForce = windSpeedToForceLevel(windSpeed)
        windForceStr = windForceToStr(windForce)
        windForceDesc = windForceToDesc(windForce)
        windHeadingDesc = headingDesc(windDirection)
        
        sailAtt = sailAttitudeDesc(abs(boat['twa']))
        
        console.print(Markdown("# (" + str(i) + ") *" + boat['boatname'] + "* - " + boat['boattype']))
        console.print(Markdown("**Position:**\t" + locName + " (" + boatLat + ", " + boatLon + ")"))
        console.print(Markdown("**Destination:**\t" + dest))
        console.print(Markdown("**Conditions:**\t" + windForceStr + " - " + windForceDesc + " from " + windHeadingDesc + " at " + str(round(windSpeed,1)) + " knots "))
        console.print(Markdown("**Heading:**\t" + str(int(round(boatHdg,0))) + "° (" + headingTxt + ") at " + str(boatSpeed) + " knots, " + sailAtt ))
        if heelAngle >= 30:
            print("")
            console.print(Markdown("### WARNING: Heel angle " + str(heelAngle) + "°"))
        print("")

    if len(boats) > 1:
        boatNum = input("Enter boat # (or press return to quit): ")
        try:
            boatNum = int(boatNum)
        except ValueError:
            updater.stop()
            sys.exit()
    else:
        boatNum = 0

    if boatNum >= 0 and boatNum < len(boats):
        boat = boats[boatNum]
        while True:
            if len(boats) > 1:
                console.print(Markdown("# *" + boat['boatname'] + "* - " + boat['boattype']))
            console.print(Markdown("**(1)** `Read the logbook`"))
            console.print(Markdown("**(2)** `Plot position on OpenSeaMap`"))
            console.print(Markdown("**(3)** `Plot position on EarthWindMap`"))
            console.print(Markdown("**(4)** `Provide NMEA source to external charting app`"))
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
                    console.print(Markdown("**" + saillog.logTimeToString(entry) + "** - *" + boatLat + ", " + boatLon + "*"))
                    console.print(Markdown("### Heading " + headingDesc(geo.wrap_angle(float(entry['cog']))) + " / " + str(int(round(float(entry['sog']),0))) + " knots / " + forceDescription[windSpeedToForceLevel(float(entry['windspd']))]))
                    print("")
                if len(entries) > 2:
                    firstTime = entries[0]['zulu']
                    lastTime = entries[len(entries)-1]['zulu']
                    totalTimeHrs = (lastTime - firstTime).total_seconds() / (60*60)

                    if lastTime.year == firstTime.year:
                        firstTimeStr = firstTime.strftime("%b %d")
                    else:
                        firstTimeStr = firstTime.strftime("%b %d, %Y")

                    dist = 0
                    for i in range(len(entries)-1):
                        index = i+1
                        curEntry, prevEntry = entries[index], entries[i]
                        curLat, curLon = float(curEntry['lat']), float(curEntry['lon'])
                        prevLat, prevLon = float(prevEntry['lat']), float(prevEntry['lon'])
                        dist += geo.dist_coord(curLat, curLon, prevLat, prevLon)
                    rate = dist / totalTimeHrs
                    console.print(Markdown("**Distance since " + firstTimeStr + ":** " + str(round(dist,1)) + " nm"))
                    console.print(Markdown("**Average speed:** " + str(round(rate,1)) + " knots"))
                    console.print(Markdown("**Distance per day:** " + str(round(rate*24,1)) + " nm"))
                    print("")
                input("(Press any key to continue)")
            elif choice == 2 or choice == 3:
                boatLat = str(round(boat['latitude'],4))
                boatLon = str(round(boat['longitude'],4))
                if choice == 2:
                    webviz.loadURL(webviz.openseamap(boatLat, boatLon))
                else:
                    webviz.loadURL(webviz.earthwindmap(boatLat, boatLon))
            elif choice == 4:
                if boatNum == updater.getBoat():
                    print("\nYou're already serving NMEA sentences for this boat!\n")
                else:
                    updater.setBoat(boatNum)
                    print("\nNow serving NMEA sentences for this boat on TCP port " + str(updater.getPort()) + ". This will continue in the background until you quit the application.\n")
                input("(Press any key to continue)")
updater.stop()