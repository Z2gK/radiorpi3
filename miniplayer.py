import yaml
import musicpd
import os

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


# Read playlist from ~/.radiorpi3/stations.yaml into dictionary
with open(os.environ['HOME'] + "/.radiorpi3/stations.yaml", 'r') as fp:
    stationlist = yaml.safe_load(fp) # need to define loader here?

# print(type(stationlist))
# print(stationlist)

# WARNING - this will initialize the client and clear out any existing playlist
client = musicpd.MPDClient()
client.connect()
client.clear()

# This combination of settings ensures that mpd would not go on to the next item in the stationlist in cases where the chosen URL is not accesssible for any reason
client.single(1)
client.repeat(1)
client.consume(0)
client.random(0)

# Take a different approach now - streams will not be added to mpd playlist at the start
for listitem in stationlist:
    client.add(listitem['URL'])

# Print this to see if initialization is done properly
# print(client.playlistinfo())

print("Mini internet radio player")
print("MPD version = " + client.mpd_version)

currentstationid = 0

while True:
    # TODO - include choice to show current program, i.e. display the value of the field tagged to 'title' from .playlistinfo(). But first there needs to be a mechanism to check if something is currently playing? Maybe usingn .status()?
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
        # request for station number - UC
        stationchoice = input("Enter id of station (0-" + str(len(stationlist)-1) + ") to play: ")
        if (stationchoice.isnumeric() and
            (int(stationchoice) >= 0) and
            (int(stationchoice) < len(stationlist) ) ):
            stationchoicenum = int(stationchoice)
            print("Playing " + stationlist[stationchoicenum]['shortname'])
            try:
                currentstationid = stationchoicenum
                client.play(stationchoicenum)
            except musicpd.CommandError:
                print("Error playing stream!")
                print("Please choose a different station")
            except musicpd.ConnectionError:
                client.connect()
                try:
                    client.play(stationchoicenum)
                except musicpd.CommandError:
                    print("Error playing stream!")
                    print("Please choose a different station")
        else:
            print("Please enter a valid id")
    elif choice.upper().strip() == "T":
        # print(client.status())
        try:
            statusoutput = client.status()
        except musicpd.ConnectionError:
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
        # Stop playing - UC
        print("Stopping...")
        try:
            client.stop()
        except musicpd.ConnectionError:
            client.connect()
            client.stop()
    elif choice.upper().strip() == "X":
        # Exit program
        try:
            client.clear()
        except musicpd.ConnectionError:
            client.connect()
            client.clear()
        # print(client.playlistinfo())
        client.close()
        client.disconnect()
        exit()
