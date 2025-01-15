from RadioRPi3 import Player
from RadioRPi3 import Display
import os
import sys

if len(sys.argv) != 2:
    print("Run Internet Radio Player Client A or B")
    print("Argument: [A | B]")
    exit()

clientchoice = sys.argv[1].strip().upper()
stationfilename = os.environ['HOME'] + "/.radiorpi3/stations.yaml"

if clientchoice == "A":
    withLCD = False
    radioplayer = Player(stationfilename, withLCD)
elif clientchoice == "B":
    withLCD = True
    display = Display("2004")
    radioplayer = Player(stationfilename, withLCD, display)
else:
    print("Invalid option")
    exit()

while True:
    radioplayer.printMenu()
    choice = input("Enter choice: ")
    radioplayer.enterChoice(choice)
