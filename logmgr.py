'''
    logmgr.py

    Manage your sailing logbooks.
'''
import sys

from rich.console import Console
from rich.markdown import Markdown

from sailaway import sailaway, saillog

console = Console()
logbook = saillog()

def inputYN(question):
    yn = input(question + " (y/n): ")
    try:
        if yn.rstrip().upper() == 'Y':
            return True
    except TypeError:
        pass
    return False

console.print(Markdown("# LOGBOOK MANAGER"))
console.print(Markdown("**(1)** `Remove log entries for deleted boats`"))
console.print(Markdown("**(2)** `Wipe your logbook`"))
print("")
choice = input("Enter option #, or press return to quit: ")
try:
    choice = int(choice)
except ValueError:
    sys.exit()
if choice==1:
    if inputYN("Remove log entries for all deleted boats? This cannot be undone."):
        validBoatIds = []
        api = sailaway()
        boats = api.query()
        for boat in boats:
            if not (boat['ubtnr'] in validBoatIds):
                validBoatIds.append(boat['ubtnr'])
        if len(validBoatIds) == 0:
            if not inputYN("No valid boats found. This will wipe your logs. Do you wish to continue?"):
                sys.exit("Aborted.")
        logbook.rewrite(validBoatIds)
        print("Done.")
elif choice==2:
    if inputYN("Wipe your logbooks? This cannot be undone."):
        logbook.wipe()
        print("Logbooks wiped.")