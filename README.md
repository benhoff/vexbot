# vexbot

[![Build Status](https://travis-ci.org/benhoff/vexbot.svg?branch=master)](https://travis-ci.org/benhoff/vexbot)[![Code Climate](https://codeclimate.com/github/benhoff/vexbot/badges/gpa.svg)](https://codeclimate.com/github/benhoff/vexbot)[![Coverage Status](https://coveralls.io/repos/github/benhoff/vexbot/badge.svg?branch=master)](https://coveralls.io/github/benhoff/vexbot?branch=master)

Pluggable bot

Under development. Very useable but currently not feature complete.

## Requirements
Requires python 3.5 for asyncio.

See [pydbus](https://github.com/LEW21/pydbus) for requirements. Currently requires:

[PyGI](https://wiki.gnome.org/Projects/PyGObject) which needs to be installed from your distribution's repoistory,

[GLib](https://developer.gnome.org/glib/) 2.46+

[girepository](https://wiki.gnome.org/Projects/GObjectIntrospection) 1.46+

These requirements allow the use of systemd for subprocess management. You will also need an active DBus session bus. Depending on your distro, you might already have one (Arch linux, for example). For Ubuntu:

`$ apt-get install dbus-user-session`

## Installation
`$ python3 -m venv <DIR>`

`$ source <DIR>/bin/activate`

If you don't plan to use the process manager functions (start services from the bot):

`$ pip install vexbot`

if you want to use the process manager functions and have the above requirements met, run this command instead:

`pip install vexbot[process_manager]`

if you intend to use `vexshell`:

`$ pip install git+https://github.com/jonathanslenders/python-prompt-toolkit@2.0`

## Configuring

Make sure your virtual environment is activated. Then run:

`$ vexbot_generate_certificates`

`$ vexbot_generate_unit_file`

`$ systemctl --user daemon-reload`

Your bot is ready to run!

## Running

`systemctl --user start vexbot`

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
