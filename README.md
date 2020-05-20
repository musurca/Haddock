# Haddock
CLI tools for tracking your Sailaway voyages, or connecting them to external charting/routing applications via NMEA.

## HADDOCK

Queries the Sailaway servers for information on your boats, and logs their position and other relevant information to a locally-stored log.

![Haddock screen 1](https://github.com/musurca/Haddock/raw/master/img/haddockscreen1.png)

You can:
- browse your logbooks
- plot your boats' position using OpenSeaMap or EarthWindMap
- send NMEA sentences from one boat to an external charting application like [qtVlm](https://www.meltemus.com/index.php/en/) or [OpenCPN](https://opencpn.org/), via a TCP server.

While running, the application will automatically update every 10 minutes.
  
![Haddock screen 2](https://github.com/musurca/Haddock/raw/master/img/haddockscreen2.png)

```
usage: haddock [<port number>]

OPTIONAL: <port number> specifies the port number for the NMEA TCP server (11010 by default).

```

## NMEA

The NMEA server only. Select one of your boats to start a TCP server and send NMEA sentences to an external charting application. (The server will also continue to update your logbooks in the background.)

![NMEA screen 1](https://github.com/musurca/Haddock/raw/master/img/nmeascreen1.png)

```
usage: nmea [<port number>] [<boat number>]

OPTIONAL: <port number> specifies the port number for the NMEA TCP server (11010 by default).

OPTIONAL: <boat number> specifies the boat number for which to immediately launch a NMEA server.
```

## Other commands

```
wipelogs
```
Wipes your locally-stored sailing logbooks.


## How to install

1) [Download and install latest release of Python 3.](https://www.python.org/downloads/)

2) From the command line:
```
pip install rich
git clone https://github.com/musurca/Haddock.git
cd Haddock/
```

3) Log into your [Sailaway account](https://sailaway.world/myaccount.pl) and copy the URL below the line that reads "API access to all sailing related parameters of your boats."

![API Example](https://github.com/musurca/Haddock/raw/master/img/apiexample.png)

4) In your Haddock folder, open up `key.txt` in a text editor, paste in your Sailaway API URL, and save it.

## Dependencies
* [Python 3](https://www.python.org/downloads/)
* [rich](https://github.com/willmcgugan/rich)

