For the most part it's assumed that you are running in the command line program for this documentation.

.. code-block:: bash

  $ vexbot

  vexbot:


See Current Commands
--------------------
.. code-block:: bash

  vexbot: !commands

See bot commands

.. code-block:: bash

  vexbot: !commands --remote


.. TODO I'm not sure how you get commands for a service right now? Think I might have regressed that functionality during development

See Extensions In Use
---------------------

.. code-block:: bash

  vexbot: !extensions

From bot:

.. code-block:: bash

  vexbot: !extensions --remote

Remove Extensions In Use
------------------------
Let's say you've the `get_cache` (shows you your configuration cache) and the `cpu_count` extensions in use and you'd like to remove them.


.. code-block:: bash

  vexbot: !remove_extension get_cache cpu_count

Alternatively just removing one:

.. code-block:: bash

  vexbot: !remove_extension get_cache

See Installed Extensions
------------------------

Installed extensions are on your path, but not neccesairly attached to anything running currently

.. code-block:: bash

  vexbot: !get_installed_extensions

This command displays a list of every extension installed with a short doc string on what it does.

For example, the command `power_off` will be displayed as

'power_off: Power off a digital ocean droplet'

You can also use a module name to see all the extensions that are provided by that module. `vexbot.extensions.subprocess` is an installed module for vexbot. To see all the extensions that are provided by that module:

.. code-block:: bash

  vexbot: !get_installed_modules vexbot.extensions.subprocess



See Installed Modules
---------------------

There are a lot of installed extensions and it's hard to figure out what each one does.
You can break them up into modules

.. code-block:: bash

  vexbot: !get_installed_modules

This is helpful because the installed modules can be used with the `get_installed_extensions` to narrow down what is shown. For example, the every extensions in the module `vexbot.extensions.digitalocean` can be shown by using the following command:

.. code-block:: bash

  vexbot: !get_installed_modules vexbot.extensions.digitalocean


Add Extensions
--------------

.. code-block:: bash

  vexbot: !add_extensions get_code delete_cache

To add commands to the robot instance:

.. code-block:: bash

  vexbot: !add_extensions get_code delete_cache --remote
