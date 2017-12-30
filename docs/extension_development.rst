=====================
Extension Development
=====================

Foreword
--------

Currently extensions are tied very closely to python's packaging ecosystem. This is unlikely to change, honestly.


Setup a Packging Environment
----------------------------

.. code-block:: bash

  $ # Note that the directory these commands are run from is `~/my_vexbot_extensions`!

  $ mkdir my_vexbot_extenstions
  $ cd my_vexbot_extensions

Create a `setup.py` file.

.. code-block:: python

  # filepath: my_vexbot_extensions/setup.py
  from setuptools import setup

  setup(name='my_vexbot_extensions')

Now take a breather. Python packaging is hard, and we're almost done!

Extensions Development
----------------------

Done with your breather? Good. Now let's say we've got a `hello_world` function that we want to use such as the below.

.. code-block:: python

  # filepath: my_vexbot_extensions/hello_world.py

  def hello(*args, **kwargs):
      print('Hello World!')

Dope. Let's add this as an extension in our `setup.py` file.

.. code-block:: python

  # filepath: my_vexbot_extensions/setup.py
  from setuptools import setup

  setup(name='my_vexbot_extensions',
        entry_points={'vexbot_extensions':['hello=hello_world:hello'])

That's it. Let's make sure the package is installed on our path. Make sure you're in the directory `my_vexbot_extensions` (or whatever you named your folder).

.. code-block:: bash

  $ # Note that the directory these commands are run from is `~/my_vexbot_extensions`!

  $ ls
  setup.py    hello_world.py

  $ python setup.py develop

You might say, wait, that's not a normal python packaging structure! And you'd be right, so let's look at how it'll change for that. We'll make a directory called `my_src` and create a file in there known as `goodbye_world.py`

.. code-block:: python

  # filepath: my_vexbot_extensions/my_src/goodbye_world.py

  def angsty(*args, **kwargs):
      print('Goodbye, cruel world!')

Note how I'm taking an arbitrary amount of arguments and key word arguments using `*args and **kwargs`_? You should do that for every extension, or your program will error out at somepoint when it gets called with metadata that it's not ready for.

.. code-block:: python

  # filepath: my_vexbot_extensions/my_src/goodbye_world.py

  def angsty(*args, **kwargs):
      print('Goodbye, cruel world!')

  # Note: Do NOT make extensions without using `*args, **kwargs`
  def function_that_will_fail_on_metadata():
      print('Please notice the lack of flexibility in this function for taking arguments')
      print('This type of extension will inevitabley throw `TypeError` exceptions if put in a codebase')


But back to registering our extension in our `setup.py` file. Remember that the filepath for this is `my_vexbot_extensions/my_src/goodbye_world.py`.

.. code-block:: python

  # filepath: my_vexbot_extensions/setup.py
  from setuptools import setup

  setup(name='my_vexbot_extensions',
        entry_points={'vexbot_extensions':['hello=hello_world:hello',
                                           'angsty=my_src.goodbye_world:angsty'])

Notice how we use the `.` operator to represent the folder directory, and the `:` to specify the method name? That's important.

We can have multiple methods in a file that way.

.. code-block:: python

  # filepath: my_vexbot_extensions/my_src/goodbye_world.py

  def angsty(*args, **kwargs):
      print('Goodbye, cruel world!')

  def crocodile(*args, **kwargs):
      print('Goodbye, crocodile!')

.. code-block:: python

  # filepath: my_vexbot_extensions/setup.py
  from setuptools import setup

  setup(name='my_vexbot_extensions',
        entry_points={'vexbot_extensions':['hello=hello_world:hello',
                                           'angsty=my_src.goodbye_world:angsty',
                                           'crocodile=my_src.goodbye_world:crocodile'])

If you have a deeply python nested file, such as one in `my_vexbot_extensions/my_src/how/deep/we/go.py`...
.. code-block:: python

  # filepath: my_vexbot_extensions/setup.py
  from setuptools import setup

  setup(name='my_vexbot_extensions',
        entry_points={'vexbot_extensions':['hello=hello_world:hello',
                                           'angsty=my_src.goodbye_world:angsty',
                                           'crocodile=my_src.goodbye_world:crocodile',
                                           'nested_func=my_src.how.deep.we.go:waay_to_much'])

Note that each folder is separated by the `.` operator, and the function name in the above example is `waay_to_much`, which is how deeply I feel that function is nested for a simple example such as this.

Remember, remember the 5th of November.
And also to re-run `python setup.py develop` once you've added an entry point/extension to your `setup.py` file.

.. code-block:: bash

  $ # Note that the directory these commands are run from is `~/my_vexbot_extensions`!

  $ ls
  setup.py    hello_world.py    my_src

  $ python setup.py develop

The string used before the path decleration, I.e the `nested_func` in the string `nested_func=my_src.how.deep.we.go:waay_to_much` is the name you will use in vexbot itself or the `hello` in `hello=hellow_world:hello`.

Let's add our hello world greeting to our command line interface.


.. code-block:: bash

  $ vexbot

  vexbot: !add_extensions hello
  vexbot: !hello
  Hello World!

You can also add the hello world to the robot instance as well.

.. code-block:: bash

  $ vexbot
  
  vexbot: !add_extensions hello --remote


Last, but not least, you can specify command name alias's, specify if the command should be hidden, and give a short description for what the command does by using the `command` decorator.

.. code-block:: python

  # filepath: my_vexbot_extensions/hello_world.py
  from vexbot.commands import command


  @command(alias=['hello_world', 'world_hello'],
           hidden=True, # default is `False`
           short='Prints `Hello World`!')
  def hello(*args, **kwargs):
      print('Hello World!')

.. _`*args and **kwargs`: https://stackoverflow.com/questions/3394835/args-and-kwargs
