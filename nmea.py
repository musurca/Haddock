'''
    nmea.py

    Converts Sailaway API data to NMEA sentences for communication
    with nautical charting software.
'''
import socket
import threading
import sys
from datetime import datetime, timedelta

from rich.console import Console
from rich.markdown import Markdown

from sailaway import sailaway, saillog
from utils import geo, units

SERVER_ADDR = "127.0.0.1"
SERVER_PORT = 10110
BUFFER_SIZE = 1024

NMEA_TIME_FORMAT = "%H%M%S"
NMEA_DATE_FORMAT = "%d%m%y"

class nmea:
    def formatSentence(msgStr,checksum=True):
        msgBytes = bytes(msgStr,'utf-8')
        csum = ""
        if checksum:
            checkSumByte = 0
            for byte in msgBytes:
                checkSumByte ^= byte
            csum = "*" + hex(checkSumByte)[2:]

        sentence = "$" + msgStr + csum + "\n"
        #print(sentence)
        return bytes(sentence, 'utf-8')

class NMEAServer:
    def __init__(self, port):
        self.port = port
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as msg:
            sys.exit("Cannot initialize network socket : " + msg)
        try:
            self.sock.bind((SERVER_ADDR, port))
        except socket.error as msg:
            sys.exit("Cannot bind socket to port " + str(port))
        self.clients = []
        self.listener = None
        self.sender = None
        self.sentence = None

    def listen(self):
        while True:
            try:
                self.sock.listen(1)
                client, addr = self.sock.accept()
            except socket.error as msg:
                break
            self.clients.append(client)
            if len(self.clients) == 1:
                self.startUpdates()

    def startUpdates(self):
        self.refresh()

    def stopUpdates(self):
        if self.sender != None:
            self.sender.cancel()
            self.sender = None

    def start(self):
        self.listener = threading.Thread(target=NMEAServer.listen, args=(self,))
        self.listener.start()
    
    def stop(self):
        self.stopUpdates()
        for client in self.clients:
            client.close()
        self.sock.close()

    # Send updates to all clients every 2 seconds
    def refresh(self):
        if self.sentence != None:
            self.sendAll(self.sentence)
        self.sender = threading.Timer(2, NMEAServer.refresh, args=(self,))
        self.sender.start()

    def sendAll(self, msg):
        badClients = []
        for client in self.clients:
            try:
                client.send(msg)
            except BrokenPipeError:
                client.close()
                badClients.append(client)
            except socket.error:
                #print("Cannot reach client: " + errmsg)
                client.close()
                badClients.append(client)
        # remove disconnected clients from list
        for client in badClients:
            self.clients.remove(client)
        if len(self.clients) == 0:
            self.stopUpdates()

    def update(self, lat, lon, hdg, sog, cog, twd, tws, curTime):
        timeStr = curTime.strftime(NMEA_TIME_FORMAT)
        dateStr = curTime.strftime(NMEA_DATE_FORMAT)
        posStr = geo.latlon_to_nmea(lat, lon)
        hdgStr = str(round(hdg,1)) + ",T"
        sogStr = str(round(sog,1))
        cogStr = str(round(cog,1))
        twaStr = str(round(geo.wrap_angle(twd-hdg),1)) + ",T"
        twsStr = str(round(tws,1)) + ",N"

        # Construct NMEA sentences
        # indicates what follows is from a virtual boat
        sOrigin = nmea.formatSentence("SOL", False)
        # Position
        sGPGLL = nmea.formatSentence("GPGLL," + posStr + "," + timeStr + ",A")
        # Position (GPS)
        sGPGAA = nmea.formatSentence("GPGAA," + timeStr + "," + posStr + ",1,08,0,0,M,,,,")
        # true heading
        sIIHDT = nmea.formatSentence("IIHDT," + hdgStr)
        # true wind speed & angle
        sWIMWV = nmea.formatSentence("WIMWV,"+ twaStr + "," + twsStr + ",A")
        # recommended minimum sentence
        sGPRMC = nmea.formatSentence("GPRMC," + timeStr + ",A," + posStr + "," + sogStr + "," + cogStr + "," + dateStr + ",,,")

        self.sentence = sOrigin + sGPGLL + sGPGAA + sIIHDT + sWIMWV + sGPRMC

class NMEAUpdater:
    def __init__(self, port=SERVER_PORT):
        self.api = sailaway()
        self.logbook = saillog()
        self.isRunning = False
        self.updateThread = None
        self.boatNum = -1
        self.boats = []
        self.serverport = port
    
    def version():
        return "(v0.1.2)"

    def start(self):
        # start the TCP server
        self.server = NMEAServer(self.serverport)
        self.server.start()
        # start the update loop
        self.isRunning = True
        self.queryAndUpdate()

    def getBoats(self):
        return self.boats

    def getPort(self):
        return self.server.port

    def getLogbook(self):
        return self.logbook

    def getBoat(self):
        return self.boatNum

    def setBoat(self, num):
        if num != self.boatNum:
            self.boatNum = num
            self.updateBoat()
        
    def stop(self):
        if self.updateThread != None:
            self.updateThread.cancel()
            self.updateThread = None
        self.isRunning = False
        self.server.stop()

    def updateBoat(self):
        if len(self.boats) > 0 and self.boatNum != -1:
            # update NMEA server with boat information
            boat = self.boats[self.boatNum]

            boatHdg = geo.wrap_angle(boat['hdg'])
            boatSpeed = units.mps_to_kts(boat['sog'])
            boatCourse = geo.wrap_angle(boat['cog'])
            windDirection = geo.wrap_angle(boat['twd'])
            windSpeed = units.mps_to_kts(boat['tws'])
            
            # Update our NMEA sentence clients
            self.server.update(boat['latitude'], boat['longitude'], boatHdg, boatSpeed, boatCourse, windDirection, windSpeed, self.api.lastUpdate)

    def refresh(self):
        # schedule next update
        curTime = datetime.utcnow()
        nextUpdateTime = sailaway.updateInterval() - (curTime - self.api.lastUpdate).total_seconds()
        if nextUpdateTime > 0:
            self.updateThread = threading.Timer(nextUpdateTime, NMEAUpdater.queryAndUpdate, args=(self,))
            self.updateThread.start()
        else:
            self.queryAndUpdate()

    def queryAndUpdate(self):
        # retrieve data from cache or server
        self.boats = self.api.query()
        for b in self.boats:
            self.logbook.write(self.api.lastUpdate, b)

        # Send updated boat positon to NMEA server
        self.updateBoat()
        
        # set up next update
        self.refresh()

def printArgs():
    sys.exit("\nusage: nmea [port number] [boat number]\n\nPort number is " + str(SERVER_PORT) + " by default.\n")

if __name__ == '__main__':
    port = SERVER_PORT
    boatNum = -1

    if len(sys.argv) > 1:
        port = sys.argv[1]
        try:
            port = int(port)
        except ValueError:
            printArgs()
    if len(sys.argv) > 2:
        boatNum = sys.argv[2]
        try:
            boatNum = int(boatNum)
        except ValueError:
            printArgs() 

    console = Console()

    updater = NMEAUpdater(port)
    updater.start()
    console.print(Markdown("### **NMEA** " + NMEAUpdater.version()))
    print("")

    boats = updater.getBoats()
    if len(boats) == 0:
        updater.stop()
        sys.exit("You don't have any boats to track.")
    if boatNum == -1:
        for i in range(len(boats)):
            boat = boats[i]
            console.print(Markdown("# (" + str(i) + ") *" + boat['boatname'] + "* - " + boat['boattype']))
        boatNum = input("Enter boat # for NMEA tracking (or press return to quit): ")
        try:
            boatNum = int(boatNum)
        except ValueError:
            updater.stop()
            sys.exit()
    else:
        boat = boats[boatNum]
        console.print(Markdown("# (" + str(boatNum) + ") *" + boat['boatname'] + "* - " + boat['boattype']))
            
    updater.setBoat(boatNum)
    print("NMEA server now listening on TCP port " + str(updater.getPort()) + " - press return to quit.")
    input("")
    updater.stop()