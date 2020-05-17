# Haddock
A CLI tool for tracking Sailaway voyages.

## The Tools

```
haddock
```
Queries the Sailaway servers for information on your boats, and logs their position and other relevant information to a locally-stored log.

![Haddock screen 1](https://github.com/musurca/Haddock/raw/master/img/haddockscreen1.png)

You can:
- browse your logbooks
- plot your boats' position using OpenSeaMap or EarthWindMap
- send NMEA sentences from one boat to an external charting application like [qtVlm](https://www.meltemus.com/index.php/en/) or [OpenCPN](https://opencpn.org/).
  
![Haddock screen 2](https://github.com/musurca/Haddock/raw/master/img/haddockscreen2.png)

```
nmea
```
The NMEA server only. Select one of your boats to start a TCP server and send NMEA sentences to an external charting application.

![NMEA screen 1](https://github.com/musurca/Haddock/raw/master/img/nmeascreen1.png)

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

