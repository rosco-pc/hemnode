# hemnode
My home automation project to control lights and equipment in my house based
on node-red and a few additional nodes. It allows to control lights and 
equipment based on solar events (for the moment this is fixed in the flow) or
based on a schedule.

This is running on a raspberry pi and will not run on windows without changes. 
It might run on a Mac.

Control unit is a [Tellstick duo](http://telldus.com/produkt/tellstick-duo/) 
(sorry only in Swedish and an outgoing product, I'm late in the game and 
everybody is moving to wifi/IoT, although god 
[only](https://arstechnica.com/information-technology/2017/10/assessing-the-threat-the-reaper-botnet-poses-to-the-internet-what-we-know-now/)
[knows](http://www.businessinsider.com/internet-of-things-security-privacy-2016-8?r=US&IR=T&IR=T) 
[why](https://www.networkworld.com/article/3217664/internet-of-things/how-to-improve-iot-security.html)) 



![mobile UI](screenshots/ui.png) ![scheduler](screenshots/scheduler.png) ![sun event](screenshots/sunonoff.png)

The scheduler is based on: [Hourly ON/OFF Week Scheduler Dashboard - DEHN.IO v0.1](https://gist.github.com/3b031629c8450d2098dd3183ccf84be4)

It has been extended to allow setting a random time (Rnd) with the following 
logic:
* A random start section will turn on the device within the first 30 minutes
of the indicated hour
* A random end section will turn off the device in the last 30 minutes of 
the indicated hour
* A stand-alone random section will behave like a random start section, that
is it will only turn on randomly and turn off at the end of the hour

In the screenshot shown above the lights will turn on between 17:01 and 17:30 
and turn off between 19:30 and 19:59

The scheduler allows to make chnages to most fields by selecting the field, \
which will then be indicated by a blue background.
pressing the buttons on the screen will tehn do the following:
![down](screenshots/down.png) select previous
![up](screenshots/up.png) select next
![copy](screenshots/copy.png) copy action(s) to next item
![save](screenshots/save.png) save schedule
![cancel](screenshots/cancel.png) cancel changes up till last save

![sun](screenshots/sun.png) switch to sun event schedule (any setting here will overwrite the hour based setting)
![schedule](screenshots/schedule.png) switch to hour based schedule
# Installation

1. Install [tellstick](http://telldus.com/resources/)
   - OPTIONAL: configure your devices 
1. Install [node-red](https://nodered.org/docs/getting-started/)
1. Install the following nodes:
   - [dashboard](https://github.com/node-red/node-red-dashboard)
   - [sunevents](https://github.com/freakent/node-red-contrib-sunevents)
   - [tellstick](https://github.com/emiloberg/node-red-contrib-tellstick)
1. Import the flows
1. Adjust flows to your devices, need to adjust 
   - the dashboard nodes (siwtch and button), 
   - the _process schedule_ node: 
change number of ports and make sure that the port number corresponds to the 
_deviceid&nbsp;-&nbsp;1_
   - Change the special handling for some of the lights
   - Make sure you learn all you input devices

Device hanlding 
- initialization should put all configured devices (from step 1a) in the 
debug tab (copied from tellstick configuration in /etc/tellstick.conf)
- Alternativley you can use the tellstick_out node to 
[add additional devices](https://github.com/emiloberg/node-red-contrib-tellstick#configure-devices) 
If you do change your flow to add the new device aswell+-
  
# License

Copyright (c) 2017 Robert Schmersel (roscopc666@gmail.com)

Permission to use, copy, modify, and distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.


