# Client B - include LCD display that shows stations information and IP address
# Assumes a 20x4 display for now

import yaml
import musicpd
import os
import subprocess
from RPLCD.i2c import CharLCD
import threading
import time
from unidecode import unidecode

# Prints the stations in two column format
def printtwocols(stationlist):
    stationlistsize = len(stationlist)
    termcols = os.get_terminal_size(0)[0]
    if termcols > 60:
        print("\nStations")
        for i in range((stationlistsize+1)//2):
            # print("line " + str(i))
            colleft = '{:<30}'.format(str(i) + " - " + stationlist[i]['shortname'])
            colright = ''
            if i + (stationlistsize+1)//2 != stationlistsize:
                colright = '{:<30}'.format(str(i + (stationlistsize+1)//2) + " - " + stationlist[i + (stationlistsize+1)//2]['shortname'])
            print(colleft + " " + colright)
    else:
        print("\nStations")
        i = 0
        for item in stationlist:
            print(str(i) + " - " + item['shortname'])
            i = i + 1

# Get a list of IP addresses associated with the host using the output from the ifconfig command
# localhost and empty addresses will not be included
def getIPaddresslist():
    # print("in getIPaddresslist")
    getoutput = subprocess.Popen("ifconfig | grep 'inet ' | awk '{print $2}'", shell=True, stdout=subprocess.PIPE).stdout
    output = getoutput.read()
    # print(output) # this is in bytes format b'...'
    # print(output.decode()) # this decodes it to string format
    outputlist = output.decode().split("\n")

    # print(outputlist)
    IPlist = []
    for address in outputlist:
        if (address != "127.0.0.1") and (address.strip() != ''):
            IPlist.append(address)

    # print(IPlist)
    return IPlist

# This function takes only the following args to remove reliance on globals
# This is to prep for display of changing of title info
# There will be no return value from this function now
# lcd, stationlist, currentstationid, IPaddress
def displaystationLCD2004(lcd, stationlist, currentstationid, IPaddress):
    # print("in displaystationLCD2004")
    fb = ["", "", "", ""]
    stationinfotext = str(currentstationid) + ": "
    stationinfotext = stationinfotext + stationlist[currentstationid]['shortname']
    fb[0] = stationinfotext.ljust(20)[:20]
    fb[1] = IPaddress.ljust(20)[:20]
    fb[2] = "".ljust(20)
    fb[3] = "".ljust(20)

    # lcd.clear()
    lcd.display_enabled = True
    lcd.backlight_enabled = True

    lcd.cursor_pos = (0,0)
    lcd.write_string(fb[0])
    lcd.cursor_pos = (1,0)
    lcd.write_string(fb[1])
    lcd.cursor_pos = (2,0)
    lcd.write_string(fb[2])
    lcd.cursor_pos = (3,0)
    lcd.write_string(fb[3])

# This function takes only the following args
# lcd, IP address
def clearLCD2004(lcd, IPaddress):
    fb = ["", "", "", ""]
    fb[0] = IPaddress.ljust(20)[:20]
    fb[1] = "".ljust(20)
    fb[2] = "".ljust(20)
    fb[3] = "".ljust(20)

    # lcd.clear()
    lcd.display_enabled = True
    lcd.backlight_enabled = True
    
    lcd.cursor_pos = (0,0)
    lcd.write_string(fb[0])
    lcd.cursor_pos = (1,0)
    lcd.write_string(fb[1])
    lcd.cursor_pos = (2,0)
    lcd.write_string(fb[2])
    lcd.cursor_pos = (3,0)
    lcd.write_string(fb[3])

# Display station, changing title and IP address for those stations that support it
# Checks playingstationwithtitle flag once every 5s
# Exits when playstationwithtitle == False, but there's a lag of 10s before exiting, and potentially this function may run simulataneously with displaystationLCD2004, causing garbage characters to be shown on the display
# Fix is to ensure that this function exits before running displaystationLCD2004 - see code in main section
def displaystationtitleLCD2004(lcd, stationlist, currentstationid, IPaddress, client):
    # print("in displaystationtitleLCD2004")
    global playingstationwithtitle
    fb = ["", "", "", ""]
    fulltitle = ""
    stationinfotext = str(currentstationid) + ": "
    stationinfotext = stationinfotext + stationlist[currentstationid]['shortname']
    fb[0] = stationinfotext.ljust(20)
    fb[1] = " " * 20
    fb[2] = " " * 20
    fb[3] = IPaddress.ljust(20)

    # lcd.clear()
    lcd.cursor_pos = (0,0)
    lcd.write_string(fb[0])
    lcd.cursor_pos = (1,0)
    lcd.write_string(fb[1])
    lcd.cursor_pos = (2,0)
    lcd.write_string(fb[2])
    lcd.cursor_pos = (3,0)
    lcd.write_string(fb[3])

    # time.sleep(5)
    
    while playingstationwithtitle:
        trackoutput = client.currentsong()
        # print(trackoutput)
        try:
            # Does the title key exists? Sometimes it ceases to exist momentarily
            fulltitle = trackoutput['title']
            # print(type(fulltitle))
            # print(fulltitle)
            # fulltitle = fulltitle.encode('ascii', 'replace')
            # LCD does not display accented characters well
            # to normalize such characters
            fulltitle = unidecode(fulltitle)
            # print(fulltitle)
        except:
            fulltitle = ""

        if fulltitle[:20].ljust(20) != fb[1]:
            fb[1] = fulltitle[:20].ljust(20)
            lcd.cursor_pos = (1,0)
            lcd.write_string(fb[1])

        if fulltitle[20:40].ljust(20) != fb[2]:
            fb[2] = fulltitle[20:40].ljust(20)
            lcd.cursor_pos = (2,0)
            lcd.write_string(fb[2])

        time.sleep(5)


# Read playlist from ~/.radiorpi3/stations.yaml into dictionary
with open(os.environ['HOME'] + "/.radiorpi3/stations.yaml", 'r') as fp:
    stationlist = yaml.safe_load(fp) # need to define loader here?

# WARNING - this will initialize the client and clear out any existing playlist
client = musicpd.MPDClient()
client.connect()
client.clear()

# Add stations to the mpd playlist
for listitem in stationlist:
    client.add(listitem['URL'])

# Initialize LCD
lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1, cols=20, rows=4, dotsize=8)

# Print this to see if initialization is done properly
# print(client.playlistinfo())

print("Mini internet radio player")
print("MPD version = " + client.mpd_version)

currentstationid = 0
# Used in displaystationtitleLCD2004() as a flag
playingstationwithtitle = False

while True:
    # TODO - Show the current song ('title' from .playlistinfo()) on the LCD display, checking every 10mins. But first there needs to be a mechanism to check if something is currently playing? Maybe usingn .status()? This should be implemented under the 'P' choice. Multithreads might be needed.
    print('''
Please choose an option
L - List stations
P - Play a station
T - Show programme or track info if available
S - Stop playing
X - Exit    
    ''')
    choice = input("Enter choice: ")

    if choice.upper().strip() == "L":
        # list stations
        printtwocols(stationlist)
    elif choice.upper().strip() == "P":
        stationchoice = input("Enter id of station (0-" + str(len(stationlist)-1) + ") to play: ")
        if (stationchoice.isnumeric() and
            (int(stationchoice) >= 0) and
            (int(stationchoice) < len(stationlist) ) ):
            stationchoicenum = int(stationchoice)
            print("Playing " + stationlist[stationchoicenum]['shortname'])
            try:
                client.play(stationchoicenum)
                currentstationid = stationchoicenum
                trackkey = stationlist[currentstationid]['mpdtracknamekey']
                if trackkey != None:
                    playingstationwithtitle = False
                    try:
                        x.join()
                    except:
                        pass
                    playingstationwithtitle = True
                    x = threading.Thread(target=displaystationtitleLCD2004, args=(lcd, stationlist, currentstationid, getIPaddresslist()[0], client,))
                    x.start()
                    # displaystationtitleLCD2004(lcd, stationlist, currentstationid, getIPaddresslist()[0], client)
                else:
                    playingstationwithtitle = False
                    # Ensures thread exits before running displaystationLCD2004 - there could be a race condition that caused the garbage characters in the LCD when these two functions write to LCD simulataneously. Same reason for other x.join()s in this code
                    try:
                        x.join()
                    except:
                        pass
                    displaystationLCD2004(lcd, stationlist, currentstationid, getIPaddresslist()[0])
            except:
                client.connect()
                client.play(stationchoicenum)
                currentstationid = stationchoicenum
                trackkey = stationlist[currentstationid]['mpdtracknamekey']
                if trackkey != None:
                    playingstationwithtitle = False
                    try:
                        x.join()
                    except:
                        pass
                    playingstationwithtitle = True
                    x = threading.Thread(target=displaystationtitleLCD2004, args=(lcd, stationlist, currentstationid, getIPaddresslist()[0], client,))
                    x.start()
                else:
                    playingstationwithtitle = False
                    try:
                        x.join() 
                    except:
                        pass
                    displaystationLCD2004(lcd, stationlist, currentstationid, getIPaddresslist()[0])
        else:
            print("Please enter a valid id")
    elif choice.upper().strip() == "T":
        # print(client.status())
        try:
            statusoutput = client.status()
        except:
            client.connect()
            statusoutput = client.status()
        if (statusoutput['state'] == 'play'):
            print("Station: " + stationlist[currentstationid]['shortname'])
            trackoutput = client.currentsong()
            trackkey = stationlist[currentstationid]['mpdtracknamekey']
            # usually trackkey == 'title'
            if (trackkey != None) and (trackkey in trackoutput):
                print("Now playing: " + trackoutput[trackkey])
            else:
                print("Track or programme information not available")
        elif (statusoutput['state'] == 'stop'):
            print("Please play a station")
    elif choice.upper() == "S":
        # Stop play but do not exit script
        print("Stopping...")
        playingstationwithtitle = False
        try:
            client.stop()
            try:
                x.join()
            except:
                pass
            clearLCD2004(lcd, getIPaddresslist()[0])
        except:
            client.connect()
            client.stop()
            try:
                x.join()
            except:
                pass
            clearLCD2004(lcd, getIPaddresslist()[0])
    elif choice.upper().strip() == "X":
        playingstationwithtitle = False
        # Exit program
        try:
            client.clear()
        except:
            client.connect()
            client.clear()
        # print(client.playlistinfo())
        client.close()
        client.disconnect()
        try:
            x.join()
        except:
            pass
        clearLCD2004(lcd, getIPaddresslist()[0])
        exit()
