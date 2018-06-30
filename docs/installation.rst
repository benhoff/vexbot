Installation
------------

You will need an active DBus user session bus. Depending on your linux distribution, you might already have one (I.e, Arch linux).

For Ubuntu:

.. code-block:: bash

  $ apt-get install dbus-user-session python3-gi python3-dev python3-pip build-essential

For Arch Linux:

.. code-block:: bash

  $ pacman -S python-gobject

For everyone:

.. code-block:: bash

  $ python3 -m venv <DIR>

.. code-block:: bash

  $ source <DIR>/bin/activate

Linking Python-gi for Ubuntu:

.. code-block:: bash

  $ ln -s /usr/lib/python3/dist-packages/gi <DIR>/lib/python3.5/site-packages/

Linking Python-gi for Arch Linux:

.. code-block:: bash

  $ ln -s /usr/lib/python3.6/site-packages/gi <DIR>/lib/python3.6/site-packages/

For Everyone:

.. code-block:: bash

  $ pip install vexbot[process_manager]

Make sure your virtual environment is activated. Then run:

.. code-block:: bash

  $ vexbot_generate_certificates
