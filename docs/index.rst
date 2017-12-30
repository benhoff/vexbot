Welcome to vexbot's documentation!
==================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   extension_development
   extension_management
   extension_discovery
   adapter_development
   adapter_configuration
   packages


.. TODO role_management
.. Should commands be called extensions?


Installation
------------

You will need an active DBus user session bus. Depending on your distro, you might already have one (Arch linux, for example).

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

Exit the command line client by typing `!exit` or using `ctl+D`.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
