# Station configuration file

This yaml file (`stations.yaml`) will be read by the client in order to initialize the MPD playlist. It stores basic information about the station, such as its name and the streaming URL, and is meant to be edited by the user to his preferences. A sample `stations.yaml` has been provided in this repo. The yaml file is human readable and the fields should be self-explanatory. Here is a snippet of the file.

```
- shortname: WSKG Jazz
  URL: https://wskg.streamguys1.com/wskg-classic-jazz
  mpdtracknamekey: title
  mpdstationnamekey: name
- shortname: BBC WS
  URL: http://stream.live.vc.bbcmedia.co.uk/bbc_world_service
  mpdtracknamekey: title
  mpdstationnamekey: name
- shortname: NPR
  URL: https://npr-ice.streamguys1.com/live.mp3
  mpdtracknamekey: null
  mpdstationnamekey: name
```

The field `shortname` is the name of the station. It is recommended to keep this field short, since this information will be shown on the LCD display on a single line and they are usually limited in the number of characters that can be shown. For this project, we are using a 20x4 LCD display, which has 20 characters per line, and hence the length of this field should be kept under around 20 characters to avoid truncation.

The `URL` field is for the streaming URL and they require some manual effort to uncover in most cases since streaming sites usually do not provide this link upfront. Some sites provide lists of URLs of more well known streaming stations. Sometimes, they can be found in the HTML source of streaming sites. In other cases, one may have to examine the network log to discover the actual URL. Based on recent experiences, these URLs can have a variety of extensions, e.g. `.aac`, `.mp3`, `m3u8`, `m3u`, or no extension at all.

The last two fields `mpdtracknamekey` and `mpdstationnamekey` are used in displaying the programme or title of the music currently playing, if the streaming site provides this information. Further explanation will be provided in the documentation for `checkstreaminfo.py` script. If in doubt, set both of these fields to the value `null`.
