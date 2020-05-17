'''
    wipelogs.py

    Wipes all sailing logbooks.
'''

from sailaway import saillog

logbook = saillog()
choice = input("Wipe your logbooks? THIS CANNOT BE UNDONE. (y/n): ")
try:
    if choice.rstrip().upper() == 'Y':
        logbook.wipe()
        print("Logbooks wiped.")
except TypeError:
    pass