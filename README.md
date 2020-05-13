# Haddock
A CLI tool for tracking Sailaway voyages.

```
haddock
```

Queries the Sailaway servers for information on your boats, and logs their position and other relevant information to a locally-stored log. You can then browse your logbooks, or plot your boats' position using OpenSeaMap or EarthWindMap.

## How to install

1) [Download and install latest release of Python 3.](https://www.python.org/downloads/)

2) From the command line:
```
pip install rich
git clone https://github.com/musurca/Haddock.git
```

3) Open up `key.txt` in the repository, and paste in your Sailaway API URL. You can find it by logging into your [Sailaway account](https://sailaway.world/myaccount.pl) and copying the URL below the line that reads "API access to all sailing related parameters of your boats."

## Dependencies
* [Python 3](https://www.python.org/downloads/)
* [rich](https://github.com/willmcgugan/rich)

