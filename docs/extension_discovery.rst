===================
Extension Discovery
===================

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

.. TODO See extension code would be helpful. Also implementing typing information. Also seeing the documentation. Also seeing some sort of use documentation
