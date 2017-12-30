=====================
Adapter Configuration
=====================

There are two things that need to be configured for most adapters. The `.service` file which systemd uses to launch the service, and an option configuration file, which can be used to pass in configurations that need to be persisted.

See `this link`_ for example configurations for the packaged adapters. And the below for a primer on ZMQ addresses, if you desire to change the configuration of anything from running locally on the loopback address.

.. _`this link`: https://github.com/benhoff/vexbot/tree/master/config

Please note that the `.service` files should be put in `~/.config/systemd/user/*`. The `.ini` files may be placed almost anywhere, as long as they are referred to properly in the `.service` file, but recommend they be placed in `!/.config/vexbot/*` for consistency.


Configuring ZMQ Addresses
-------------------------

Addresses can be configured for the adapters and the bot itself in the .ini files. This is a bit more advanced and probably not recommended.

The address expected is in the format of `tcp://[ADDRESS]:[PORT_NUMBER]`. 

For example `tcp://127.0.0.1:5617` is a valid address. 127.0.0.1 is the ADDRESS and 5617 is the PORT_NUMBER. 

127.0.0.1 was chosen specifially as an example because for IPV4 it is the "localhost". Localhost is the computer the program is being run on. So if you want the program to connect to a socket on your local computer (you probably do), use 127.0.0.1.
 
Port numbers range from 0-65536, and can be mostly aribratry chosen. For linux ports 0-1024 are reserved, so best to stay away from those. Port 5555 is usually used as an example port for coding examples, so probably best to stay away from that as well.
 
The value of the `publish_address` and `subscribe_address` at the top of the settings file are likely what you want to copy for the `publish_address` and `subscribe_address` under shell, irc, xmpp, youtube, and socket_io if you're running everything locally on one computer. But you don't have to. You could run all the services on one computer and the main robot on a different computer. You would just need to configure the address and ports correctly, as well as work through any networking/port issues going across the local area network (LAN).
