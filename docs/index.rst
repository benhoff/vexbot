Vexbot Documentation
====================

Vexbot currently serves as a chatbot/chat aggrgator. Connect many different chat services into one!
It's being developed as a personal assistant bot. The idea is to provide computing services across any medium.

.. getting started
.. link to user documentation
.. link to developer documentation
.. reference documentation

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
