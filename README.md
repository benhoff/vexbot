# vexbot
Pluggable bot

Under heavy development. 
Not ready for general use outside of driving [chatimusmaximus](https://github.com/benhoof/chatimusmaximus)

Requires python 3.5

## Installation
recommend running out of a virutalenv

So activate your virual environment and run:

`pip3 install vexbot`

## Configuring
Base your configuration on the [default settings](https://github.com/benhoff/vexbot/blob/master/vexbot/default_settings.yml). The configuration handeling hasn't been user proofed the configuration handeling so if you're getting errors, that's a good place to start.

### Configuring Addresses
 Vexbot uses messaging and subprocesses for different services. This has some advantages/disadvantages of this approach, but the reason it's staying is it allows the developer some decreased congnitive load while developing this project.
 
 The address expected is in the format of `tcp://[ADDRESS]:[PORT_NUMBER]`. 
 For example `tcp://127.0.0.1:5617` is a valid address. 127.0.0.1 is the ADDRESS and 5617 is the PORT_NUMBER. 

 127.0.0.1 was chosen specifially as an example because for IPV4 it is the "localhost". Localhost is the computer the program is being run on. So if you want the program to connect to a socket on your local computer (you probably do), use 127.0.0.1.
 
 Port numbers range from 0-65536, and can be mostly aribratry chosen. For linux ports 0-1024 are reserved, so best to stay away from those. Port 5555 is usually used as an example port for coding examples, so probably best to stay away from that as well.
 
 The value of the `publish_address` and `subscribe_address` at the top of the settings file are likely what you want to copy for the `publish_address` and `subscribe_address` under shell, irc, xmpp, youtube, and socket_io if you're running everything locally on one computer. But you don't have to. You could run all the services on one computer and the main robot on a different computer. You would just need to configure the address and ports correctly, as well as work through any networking/port issues going across the local area network (LAN).

## Running
if everything is in your path correctly, open a console and run

`vexbot --settings_path /path/to/your/settings/here`

as a short hand

`vexbot --s /path/to/your/settings/here`

or you can set the environmental variable `VEXBOT_SETTINGS` to be the absolute path to your settings file
