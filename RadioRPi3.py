# This file contains the class definitions for RadioRpi3
import os
import musicpd
import yaml
import time
import subprocess
import threading
from unidecode import unidecode
from RPLCD.i2c import CharLCD

# Prints the stations in two column format
# Would os.get_terminal_size cause any problem when run without a terminal?
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
    getoutput = subprocess.Popen("ifconfig | grep 'inet ' | awk '{print $2}'", shell=True, stdout=subprocess.PIPE).stdout
    output = getoutput.read()
    # print(output) # this is in bytes format b'...'                           
    # print(output.decode()) # this decodes it to string format
    outputlist = output.decode().split("\n")
    IPlist = []
    for address in outputlist:
        if (address != "127.0.0.1") and (address.strip() != ''):
            IPlist.append(address)
    return IPlist


class Player:
    '''Class for all mpd interactions
    May want to include flag in constructor to specify if LCD is run'''
    def __init__(self, stationfilename: str, withLCD: bool, displayLCD = None):
        with open(stationfilename, 'r') as fp:
            self.stationlist = yaml.safe_load(fp) # need to define loader here?
        self.withLCD = withLCD # For choosing between Clients A and B
        self.currentstationid = 0
        self.playingstationwithtitle = False # Used in previous displaystationtitleLCD2004() as a flag
        self.display = displayLCD
        
        # WARNING - this will initialize the client and clear out any existing playlist
        self.client = musicpd.MPDClient()
        self.client.connect()
        self.client.clear()
        for listitem in self.stationlist:
            self.client.add(listitem['URL'])

        # This combination of settings ensures that mpd would not go on to the next item in the stationlist in cases where the chosen URL is not accessible for any  reason
        self.client.single(1)
        self.client.repeat(1)
        self.client.consume(0)
        self.client.random(0)

        print("Mini internet radio player")
        print("MPD version = " + self.client.mpd_version)

    def printMenu(self):
        print('''
Please choose an option
L - List stations
P - Play a station
T - Show programme or track info if available
S - Stop playing
X - Exit    
        ''')

    def enterChoice(self, choice):
        if choice.upper().strip() == "L":
            # list stations
            self.printStationList()

        elif choice.upper().strip() == "P":
            stationchoice = input("Enter id of station (0-" + str(len(self.stationlist)-1) + ") to play: ")
            if (stationchoice.isnumeric() and
                (int(stationchoice) >= 0) and
                (int(stationchoice) < len(self.stationlist) ) ):
                stationchoicenum = int(stationchoice)
                print("Playing " + self.stationlist[stationchoicenum]['shortname'])
                if self.withLCD:
                    self.playStationWithLCD(stationchoicenum)
                else:
                    self.playStation(stationchoicenum)
            else:
                print("Please enter a valid id")

        elif choice.upper().strip() == "T":
            self.printTrackInfo()
            
        elif choice.upper() == "S":
            # Stop play but do not exit
            print("Stopping...")
            self.stopPlayer()

        elif choice.upper().strip() == "X":
            # Exit program
            self.exitPlayer()

    def printStationList(self):
        '''Prints list of station in two column format'''
        printtwocols(self.stationlist)

    def playStation(self, stationchoicenum):
        try:
            self.currentstationid = stationchoicenum
            self.client.play(stationchoicenum)
        except musicpd.CommandError:
            print("Error playing stream!")
            print("Please choose a different station")
        except musicpd.ConnectionError:
            self.client.connect()
            try:
                self.client.play(stationchoicenum)
            except musicpd.CommandError:
                print("Error playing stream!")
                print("Please choose a different station")

    def playStationWithLCD(self, stationchoicenum):
        '''Run this when LCD is attached
        Has multithreaded code to update track info on LCD continuosly
        Need to check if existing thread is still running to avoid 
        writing garbage to LCD'''
        isDone = False
        while (not isDone):
            try:
                self.currentstationid = stationchoicenum
                trackkey = self.stationlist[self.currentstationid]['mpdtracknamekey']
                self.client.play(stationchoicenum)
                # Display station on LCD, start to update track info if available, every 5s
                if trackkey != None: # track info IS available
                    self.playingstationwithtitle = False # Stop continuousTitleUpdates, if running
                    try:
                        self.x.join() # Wait to stop whatever is running
                    except:
                        pass
                    self.playingstationwithtitle = True
                    self.x = threading.Thread(target=self.continuousTitleUpdates)
                    self.x.start()
                else: # track info is NOT available
                    self.playingstationwithtitle = False # Stop continuousTitleUpdates, if running
                    try:
                        self.x.join() # Wait to stop whatever is running
                    except:
                        pass
                    self.display.refreshIPaddress()
                    self.display.displayStationLCD(self.stationlist, self.currentstationid, False)
                isDone = True # set to true and exit while loop

            except musicpd.CommandError:
                print("Error playing stream!")
                print("Please choose a different station")
                self.playingstationwithtitle = False # Stop continuousTitleUpdates, if running
                try:
                    self.x.join() # Wait to stop whatever is running
                except:
                    pass
                self.display.displayStationLCD(self.stationlist, self.currentstationid, True)
                isDone = True # set to true and exit while loop

            except musicpd.ConnectionError:
                self.client.connect() # Then loop back to start of while loop and try again. Do away with repeated code

            
    def printTrackInfo(self):
        try:
            statusoutput = self.client.status()
        except musicpd.ConnectionError:
            self.client.connect()
            statusoutput = self.client.status()
        if (statusoutput['state'] == 'play'):
            print("Station: " + self.stationlist[self.currentstationid]['shortname'])
            trackoutput = self.client.currentsong()
            trackkey = self.stationlist[self.currentstationid]['mpdtracknamekey']
            if (trackkey != None) and (trackkey in trackoutput):
                print("Now playing: " + trackoutput[trackkey])
            else:
                print("Track or programme information not available")
        elif (statusoutput['state'] == 'stop'):
            print("Please play a station")

    def continuousTitleUpdates(self):
        '''Meant to run in a separate thread
        Updates track information on the LCD display every 5s
        Runs only when self.playingstationwithtitle is True'''
        while self.playingstationwithtitle:
            try:
                trackoutput = self.client.currentsong()
                fulltitle = trackoutput['title'] # Sometimes this key does not exist momentarily
                fulltitle = unidecode(fulltitle)
            except:
                fulltitle = ""
            # self.display.displayStationTitleLCD(self.stationlist, self.currentstationid, trackoutput['title'])
            self.display.displayStationTitleLCD(self.stationlist, self.currentstationid, fulltitle)

            time.sleep(5)

    def stopPlayer(self):
        if self.withLCD: # using LCD
            self.playingstationwithtitle = False
            isDoneStopping = False
            while (not isDoneStopping):
                try:
                    self.client.stop()
                    try:
                        self.x.join()
                    except:
                        pass
                    self.display.clearLCD() # Clear LCD
                    isDoneStopping = True
                except musicpd.ConnectionError:
                    self.client.connect()
                
        else: # Not using LCD
            try:
                self.client.stop()
            except musicpd.ConnectionError:
                self.client.connect()
                self.client.stop()

    def exitPlayer(self):
        if self.withLCD:
            self.playingstationwithtitle = False # Stop continuousTitleUpdates, if running
            try:
                self.x.join() # Wait to stop whatever is running
            except:
                pass
            self.display.clearLCD() # Clear LCD
        try:
            self.client.clear()
        except musicpd.ConnectionError:
            self.client.connect()
            self.client.clear()
        self.client.close()
        self.client.disconnect()
        exit()

class Display:
    def __init__(self, LCDtype: str):
        if LCDtype == "2004":
            self.lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1, cols=20, rows=4, dotsize=8)
        self.IPaddress = getIPaddresslist()[0]
        self.fb = ["", "", "", ""] # Newly introduced to keep state of display

    def refreshIPaddress(self):
        '''Can be called from outside the class or from within'''
        self.IPaddress = getIPaddresslist()[0]
        
    def clearLCD(self):
        self.refreshIPaddress()
        IPaddress = self.IPaddress
        # self.fb = ["", "", "", ""]
        self.fb[0] = IPaddress.ljust(20)[:20]
        self.fb[1] = "".ljust(20)
        self.fb[2] = "".ljust(20)
        self.fb[3] = "".ljust(20)

        self.lcd.display_enabled = True
        self.lcd.backlight_enabled = True

        self.lcd.cursor_pos = (0,0)
        self.lcd.write_string(self.fb[0])
        self.lcd.cursor_pos = (1,0)
        self.lcd.write_string(self.fb[1])
        self.lcd.cursor_pos = (2,0)
        self.lcd.write_string(self.fb[2])
        self.lcd.cursor_pos = (3,0)
        self.lcd.write_string(self.fb[3])

    def displayStationLCD(self, stationlist, currentstationid, errorflag):
        '''This function displays only the station name and IP address
        on the LCD display.
        This is for stations that do not provide track information'''
        IPaddress = self.IPaddress
        # fb = ["", "", "", ""]
        stationinfotext = str(currentstationid) + ": "
        stationinfotext = stationinfotext + stationlist[currentstationid]['shortname']
        self.fb[0] = stationinfotext.ljust(20)[:20]
        if errorflag:
            self.fb[1] = "Error playing stream"
            self.fb[2] = IPaddress.ljust(20)[:20]
            self.fb[3] = "".ljust(20)
        else:
            self.fb[1] = IPaddress.ljust(20)[:20]
            self.fb[2] = "".ljust(20)
            self.fb[3] = "".ljust(20)

        self.lcd.display_enabled = True
        self.lcd.backlight_enabled = True

        self.lcd.cursor_pos = (0,0)
        self.lcd.write_string(self.fb[0])
        self.lcd.cursor_pos = (1,0)
        self.lcd.write_string(self.fb[1])
        self.lcd.cursor_pos = (2,0)
        self.lcd.write_string(self.fb[2])
        self.lcd.cursor_pos = (3,0)
        self.lcd.write_string(self.fb[3])
        
    def displayStationTitleLCD(self, stationlist, currentstationid, trackname):
        '''This function displays the station, track information and IP address
        on the LCD display.
        This is for stations that provide track information.
        The Player class is responsible for regular updates of track information every 5s
        It should try to prevent garbage from getting written to the display'''
        IPaddress = self.IPaddress
        self.fb = ["", "", "", ""]
        stationinfotext = str(currentstationid) + ": "
        stationinfotext = stationinfotext + stationlist[currentstationid]['shortname']
        # Decoding was already done outside this function
        # But do it again to be doubly sure
        try:
            fulltitle = trackname
            fulltitle = unidecode(fulltitle)
        except:
            fulltitle = ""

        # Try not to update if nothing changed because it might cause blinking
        # self.fb[0] = stationinfotext.ljust(20)
        # self.fb[1] = " " * 20
        # self.fb[2] = " " * 20
        # self.fb[3] = IPaddress.ljust(20)

        if self.fb[0] != stationinfotext.ljust(20):
            self.fb[0] = stationinfotext.ljust(20)
            self.lcd.cursor_pos = (0,0)
            self.lcd.write_string(self.fb[0])
            
        if fulltitle[:20].ljust(20) != self.fb[1]:
            self.fb[1] = fulltitle[:20].ljust(20)
            self.lcd.cursor_pos = (1,0)
            self.lcd.write_string(self.fb[1])

        if fulltitle[20:40].ljust(20) != self.fb[2]:
            self.fb[2] = fulltitle[20:40].ljust(20)
            self.lcd.cursor_pos = (2,0)
            self.lcd.write_string(self.fb[2])

        if self.fb[3] != IPaddress.ljust(20):
            self.fb[3] = IPaddress.ljust(20)
            self.lcd.cursor_pos = (3,0)
            self.lcd.write_string(self.fb[3])

        # OLD CODE ----
        #self.lcd.cursor_pos = (0,0)
        #self.lcd.write_string(fb[0])
        #self.lcd.cursor_pos = (1,0)
        #self.lcd.write_string(fb[1])
        #self.lcd.cursor_pos = (2,0)
        #self.lcd.write_string(fb[2])
        #self.lcd.cursor_pos = (3,0)
        #self.lcd.write_string(fb[3])

        # OLD CODE ----
        #if fulltitle[:20].ljust(20) != fb[1]:
        #    self.fb[1] = fulltitle[:20].ljust(20)
        #    self.lcd.cursor_pos = (1,0)
        #    self.lcd.write_string(fb[1])

        # OLD CODE ----
        #if fulltitle[20:40].ljust(20) != fb[2]:
        #    self.fb[2] = fulltitle[20:40].ljust(20)
        #    self.lcd.cursor_pos = (2,0)
        #    self.lcd.write_string(fb[2])
