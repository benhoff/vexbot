# vexbot

[![Build Status](https://travis-ci.org/benhoff/vexbot.svg?branch=master)](https://travis-ci.org/benhoff/vexbot)[![Code Climate](https://codeclimate.com/github/benhoff/vexbot/badges/gpa.svg)](https://codeclimate.com/github/benhoff/vexbot)[![Coverage Status](https://coveralls.io/repos/github/benhoff/vexbot/badge.svg?branch=master)](https://coveralls.io/github/benhoff/vexbot?branch=master)

Pluggable bot

Under development. Very useable but currently not feature complete.

## Requirements
Requires python 3.5 for asyncio.

## Installation
Installing is a bit involved. You will need an active DBus user session bus. Depending on your distro, you might already have one (Arch linux, for example). For Ubuntu:

`$ apt-get install dbus-user-session python3-gi python3-dev python3-pip build-essential`

`$ python3 -m venv <DIR>`

`$ source <DIR>/bin/activate`

`$ pip install git+https://github.com/benhoff/vexmessage@dev`

`$ ln -s /usr/lib/python3/dist-packages/gi* <DIR>/lib/python3.5/site-packages/`

`$ pip install vexbot[process_manager]`

To use `vexshell`:

`$ pip install git+https://github.com/jonathanslenders/python-prompt-toolkit@2.0`

## Configuring

Make sure your virtual environment is activated. Then run:

`$ vexbot_generate_certificates`

`$ vexbot_generate_unit_file`

`$ systemctl --user daemon-reload`

Your bot is ready to run!

## Running

`$ systemctl --user start vexbot`
 
Or

`$ vexbot_robot`

Please note that vexbot has a client/server architecture. The above commands will launch the server. To launch the command line client:

`$ vexbot`

I realize that calling the client and the server by the same name might seem confusing, but in practice I haven't found it to be an issue.

Exit the command line client by typing `!exit` or using `ctl+D`.

## Configuring Adapters

Vexbot currently has working Irc, XMPP, Socket IO, and Youtube Live adapters. Unfortunately, you'll have to manually configure them yourself. See the [config directory](https://github.com/benhoff/vexbot/tree/dev/config) for examples. The corresponding `.ini` file can go anywhere (recommend `~/.config/vexbot/`) and the `.service` file should go somewhere where systemd can find it (recommend `~/.config/systemd/user/`). Recommend you name the .service file after the name of the service you are using. For example, rename `irc.service` to `freenode.service` to capture the fact that it provides the an interface to freenode irc.


### Configuring Addresses
Addresses can be configured for the adapters and the bot itself in the .ini files. This is a bit more advanced and probably not recommended.

 The address expected is in the format of `tcp://[ADDRESS]:[PORT_NUMBER]`. 
 For example `tcp://127.0.0.1:5617` is a valid address. 127.0.0.1 is the ADDRESS and 5617 is the PORT_NUMBER. 

 127.0.0.1 was chosen specifially as an example because for IPV4 it is the "localhost". Localhost is the computer the program is being run on. So if you want the program to connect to a socket on your local computer (you probably do), use 127.0.0.1.
 
 Port numbers range from 0-65536, and can be mostly aribratry chosen. For linux ports 0-1024 are reserved, so best to stay away from those. Port 5555 is usually used as an example port for coding examples, so probably best to stay away from that as well.
 
 The value of the `publish_address` and `subscribe_address` at the top of the settings file are likely what you want to copy for the `publish_address` and `subscribe_address` under shell, irc, xmpp, youtube, and socket_io if you're running everything locally on one computer. But you don't have to. You could run all the services on one computer and the main robot on a different computer. You would just need to configure the address and ports correctly, as well as work through any networking/port issues going across the local area network (LAN).

## Packages

 | required packages | License |
 |-------------------|---------|
 | vexmessage        | GPL3    |
 | pyzmq             | BSD     |
 | rx                | Apache  |
 | tblib             | BSD     |
 | tornado           | Apache  |

### Optional Packages

 | nlp              | License |
 |------------------|---------|
 | spacy            |         |
 | sklearn          |         |
 | sklearn_crfsuite |         |
 | wheel            |         |


 | socket_io        | License |
 |------------------|---------|
 | requests         |         |
 | websocket-client |         |


 | summarization | License |
 |---------------|---------|
 | gensim        |         |
 | newspaper3k   |         |


 | youtube                  | License |
 |--------------------------|---------|
 | google-api-python-client |         |


 | dev    | License |
 |--------|---------|
 | flake8 |         |
 | twine  |         |
 | wheel  |         |


 | xmpp      | License |
 |-----------|---------|
 | sleekxmpp |         |
 | dnspython |         |


 | process_name | License |
 |--------------|---------|
 | setproctitle |         |


 | speechtotext | License |
 |--------------|---------|
 | speechtotext |         |


 | process_manager | License |
 |-----------------|---------|
 | pydus           |         |


 | gui             | License |
 |-----------------|---------|
 | chatimusmaximus |         |


 | irc  | License |
 |------|---------|
 | irc3 |         |


 | microphone | License |
 |------------|---------|
 | microphone |         |


 | speechtotext | License |
 |--------------|---------|
 | speechtotext |         |
