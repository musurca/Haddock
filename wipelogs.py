from utils import log

logbook = log()
choice = input("Wipe your logbooks? THIS CANNOT BE UNDONE. (y/n): ")
try:
    if choice.upper()=='Y':
        logbook.wipe()
        print("Logbooks wiped.")
except TypeError:
    pass