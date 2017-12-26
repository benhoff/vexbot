======
vexbot
======


Pluggable bot

Under development. Very useable but currently not feature complete.

Requirements
------------

Requires python 3.5 for asyncio and only runs on linux.

 If you're a python developer, you can probably get this to run on not linux.

Installation
------------

Installing is a bit involved. You will need an active DBus user session bus. Depending on your distro, you might already have one (Arch linux, for example).

For Ubuntu:

.. code-block:: bash

  $ apt-get install dbus-user-session python3-gi python3-dev python3-pip build-essential

For everyone:

.. code-block:: bash
  $ python3 -m venv <DIR>

.. code-block:: bash

  $ source <DIR>/bin/activate

.. code-block:: bash

  $ ln -s /usr/lib/python3/dist-packages/gi <DIR>/lib/python3.5/site-packages/

.. code-block:: bash

  $ pip install vexbot[process_manager]

To use the command line interface:

.. code-block:: bash
	
  $ pip install git+https://github.com/jonathanslenders/python-prompt-toolkit@2.0

Configuring
-----------

Make sure your virtual environment is activated. Then run:

.. code-block:: bash

  $ vexbot_generate_certificates

.. code-block:: bash

 $ vexbot_generate_unit_file

.. code-block:: bash

 $ systemctl --user daemon-reload

Your bot is ready to run!

Running
-------

.. code-block:: bash

 $ systemctl --user start vexbot
 
Or

.. code-block:: bash

  $ vexbot_robot

Please note that vexbot has a client/server architecture. The above commands will launch the server. To launch the command line client:

.. code-block:: bash

  $ vexbot

I realize that calling the client and the server by the same name might seem confusing, but in practice I haven't found it to be an issue.

Exit the command line client by typing `!exit` or using `ctl+D`.

Configuring Adapters
--------------------

Vexbot currently has working Irc, XMPP, Socket IO, and Youtube Live adapters. Unfortunately, you'll have to manually configure them yourself. See the [config directory](https://github.com/benhoff/vexbot/tree/dev/config) for examples. The corresponding `.ini` file can go anywhere (recommend `~/.config/vexbot/`) and the `.service` file should go somewhere where systemd can find it (recommend `~/.config/systemd/user/`). Recommend you name the .service file after the name of the service you are using. For example, rename `irc.service` to `freenode.service` to capture the fact that it provides the an interface to freenode irc.

Create A New Adapter
--------------------

Create a messaging instance and past in a unique service name that will identify it.

.. code-block:: python

  from vexbot.adapters.messaging import Messaging

  messaging = Messaging('unique_service_name', run_control_loop=True)
  messaging.run(blocking=False)
  # Your code here.

  # Some sort of loop, using a `while` loop for illustration purposes
  while True:
      author = ''
      message = ''
      # optional
      # channel = ''

      messaging.send_chatter(author=author,
                             message=message)

      # NOTE: Alternate implementation
      """
      messaging.send_chatter(author=author,
                             message=message,
                             channel=channel)
      """

Dope. But what about something that sends commands to the robot?

.. code-block:: python

  from vexbot.adapters.messaging import Messaging

  messaging = Messaging('unique_service_name', run_control_loop=True)
  messaging.run(blocking=False)

  # Your code here. You would probably want this in a loop as well.
  command = ''
  args = []
  kwargs = {}

  messaging.send_command(command, *args, **kwargs)

You probably want a response back out of that command, huh?

.. code-block:: python

  from vexbot.observer import Observer
  from vexbot.adapters.messaging import Messaging

  class MyObserver(Observer):
      def on_next(self, request):
          result = request.kwargs.get('result')
          # your code here

      def on_error(self, *args, **kwargs):
          pass

      def on_completed(*args, **kwargs):
          pass

  messaging = Messaging('unique_service_name', run_control_loop=True)
  messaging.run(blocking=False)

  my_observer = MyObserver()

  messaging.command.subscribe(my_observer)
  # You can also pass in methods to the `subscribe` method
  messaging.command.subscribe(your_custom_method_here)

Actually you probably want the ability to dynamically load commands, persist your dynamic commands, and see all the installed commands available.

.. code-block:: python

  import shelve
  from os import path
  from vexbot.observer import Observer
  from vexbot.extensions import extensions

  from vexbot.util.get_cache_filepath import get_cache 
  from vexbot.util.get_cache_filepath import get_cache_filepath as get_cache_dir

  class MyObserver(Observer):
      extensions = (extensions.add_extensions,
                    extensions.remove_extension,
                    # NOTE: you can pass in dict's here to change the behavior
                    {'method': your_method_here,
                     'hidden': True,
                     'name': 'some_alternate_method_name',
                     'alias': ['method_name2',
                               'method_name3']},

                    extensions.get_extensions,
                    extensions.get_installed_extensions)

      def __init__(self):
          super().__init__()
          self._commands = {}
          cache_dir = get_cache_dir()
          mkdir = not path.isdir(cache_dir)
          if mkdir:
              os.makedirs(cache_dir, exist_ok=True)

          filepath = get_cache(__name__ + '.pickle')
          init = not path.isfile(filepath)

          self._config = shelve.open(filepath, flag='c', writeback=True)

          if init:
              self._config['extensions'] = {}
              self._config['disabled'] = {}
              self._config['modules'] = {}

      # NOTE: Here's our command handeling
      def handle_command(self, command: str, *args, **kwargs):
          callback = self._commands.get(command)
          if callback is None:
              return

          # Wrap our callback to catch errors
          try:
               result = callback(*args, **kwargs)
          except Exception as e:
               self.on_error(command, e, args, kwargs)

          print(result)

      def on_next(self, request):
          # NOTE: Here's our responses back from the bot
          result = request.kwargs.get('result')
          # your code here

      def on_error(self, *args, **kwargs):
          pass

      def on_completed(*args, **kwargs):
          pass

    >> observer = MyObserver()
    >> observer.handle_command('get_extensions')
    >> []
    >> observer.handle_command('add_extensions', 'log_level')
    >> observer.handle_command('get_extensions')
    >> ['log_level']

That should be enough to get you started.

Configuring ZMQ Addresses
---------------------

Addresses can be configured for the adapters and the bot itself in the .ini files. This is a bit more advanced and probably not recommended.

 The address expected is in the format of `tcp://[ADDRESS]:[PORT_NUMBER]`. 
 For example `tcp://127.0.0.1:5617` is a valid address. 127.0.0.1 is the ADDRESS and 5617 is the PORT_NUMBER. 

 127.0.0.1 was chosen specifially as an example because for IPV4 it is the "localhost". Localhost is the computer the program is being run on. So if you want the program to connect to a socket on your local computer (you probably do), use 127.0.0.1.
 
 Port numbers range from 0-65536, and can be mostly aribratry chosen. For linux ports 0-1024 are reserved, so best to stay away from those. Port 5555 is usually used as an example port for coding examples, so probably best to stay away from that as well.
 
 The value of the `publish_address` and `subscribe_address` at the top of the settings file are likely what you want to copy for the `publish_address` and `subscribe_address` under shell, irc, xmpp, youtube, and socket_io if you're running everything locally on one computer. But you don't have to. You could run all the services on one computer and the main robot on a different computer. You would just need to configure the address and ports correctly, as well as work through any networking/port issues going across the local area network (LAN).

Packages
--------

+===================+=========+
| required packages | License |
+===================+=========+
| vexmessage        | GPL3    |
+-------------------+---------+
| pyzmq             | BSD     |
+-------------------+---------+
| rx                | Apache  |
+-------------------+---------+
| tblib             | BSD     |
+-------------------+---------+
| tornado           | Apache  |
+-------------------+---------+

Optional Packages
-----------------

+==================+=========+
| nlp              | License |
+==================+=========+
| spacy            |         |
+------------------+---------+
| sklearn          |         |
+------------------+---------+
| sklearn_crfsuite |         |
+------------------+---------+
| wheel            |         |
+------------------+---------+

+==================+=========+
| socket_io        | License |
+==================+=========+
| requests         |         |
+------------------+---------+
| websocket-client |         |
+------------------+---------+

+===============+=========+
| summarization | License |
+===============+=========+
| gensim        |         |
+---------------+---------+
| newspaper3k   |         |
+---------------+---------+

+==========================+=========+
| youtube                  | License |
+==========================+=========+
| google-api-python-client |         |
+--------------------------+---------+

+========+=========+
| dev    | License |
+========+=========+
| flake8 |         |
+--------+---------+
| twine  |         |
+--------+---------+
| wheel  |         |
+--------+---------+

+===========+=========+
| xmpp      | License |
+===========+=========+
| sleekxmpp |         |
+-----------+---------+
| dnspython |         |
+-----------+---------+


+==============+=========+
| process_name | License |
+==============+=========+
| setproctitle |         |
+--------------+---------+


+==============+=========+
| speechtotext | License |
+==============+=========+
| speechtotext |         |
+--------------+---------+


+=================+=========+
| process_manager | License |
+=================+=========+
| pydus           |         |
+-----------------+---------+


+=================+=========+
| gui             | License |
+=================+=========+
| chatimusmaximus |         |
+-----------------+---------+


+======+=========+
| irc  | License |
+======+=========+
| irc3 |         |
+------+---------+


+============+=========+
| microphone | License |
+============+=========+
| microphone |         |
+------------+---------+


+==============+=========+
| speechtotext | License |
+==============+=========+
| speechtotext |         |
+--------------+---------+
