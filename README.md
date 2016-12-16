# Garage Door Relay controlled with IFTTT
Code to control a simple relay connected to a Garage Door from a Raspberry PI, using [IFTTT](http://www.ifttt.com/) 'Do' app. 

# Setup

Make sure you add a `secret.php` to the same folder as the `index.php`, and include the following:

    <?php
    
    $secret = '';
    $home_lat = '';
    $home_long = '';
    $openCommand = 'sudo <path-to-this-code>/GarageDoorRelayIFTTT/script/openDoor.py';
    
    ?>

Make sure you grant sudo access to the Apache/Web host user to the script above. On Raspbian this is usually `www-data`. Do this with `visudo` command. 

I have my setup as such:

1. Create 'Do' recipe in [IFTTT](http://www.ifttt.com/). 
2. Setup DNS redirect to my home IP.  (I'm using OpenWRT to update my DNS with a DynDNS provider)
3. Add this DNS entry to IFTTT 'do' recipe as the URL. 
4. Configure it to be 'POST' 
5. Content type = `application/x-www-form-urlencoded`
6. Body = `secret=SEKRETHASH&long={{Longitude}}&lat={{Latitude}}`

# Hardware

I largely copied the steps described [here](http://www.instructables.com/id/Arduino-WiFi-Garage-Door-Opener/), after many attempts at trying to hack the rolling codes on my garage door (don't try). The parts, and my setup are:

* [Merlin MT100EVO Garage Door](http://www.gomerlin.com.au/products/garage-door-opener/sectional-garage-door/Tiltmaster)
* Rasperry Pi v1
* 5V -> 30VDC Relay (I bought this one from [Jaycar](https://www.jaycar.com.au/arduino-compatible-5v-relay-board/p/XC4419))
* 2x aligator clips 

# Discovery

Following the [Merlin hardware instructions for my opener](http://www.gomerlin.com.au/getattachment/e5b51def-90c6-488a-b2e5-939ca5bc196d/MT100EVO-installation-manual) I noticed at the back of the opener were two ports suitable for wiring up to what Merlin referred to as a 'builders button'. In other words, if you short (i.e. connect) a cable between ports 1 & 2, the door will activate. 

Since I'm renting, I had no say over the opener, but the person who installed it left the wires exposed as they were connected to an wired button on the wall some 10 metres away, which meant it was easy for me to attach alligator clips to. 

After following the guide listed [above](http://www.instructables.com/id/Arduino-WiFi-Garage-Door-Opener/), I cracked out my multimeter (note this was the first time I ever used one) and measured the voltage of the pins I needed to short using my clips. Unlike the other guy, I was seeing 25V DC between the cables, so it was fairly high - but not in the danger zone, and I was still able to use the cheap Arduino compatible relays (see above). Rather than set it up using a standard relay and transistor, I was lazy and bought the prebuilt one. 









