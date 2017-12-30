===================
Adapter Development
===================

Create A New Adapter
--------------------

Create a messaging instance and pass in a service name that will uniquely identify it.

.. code-block:: python

  from vexbot.adapters.messaging import Messaging

  messaging = Messaging('unique_service_name', run_control_loop=True)
  messaging.run(blocking=False)
  # Your messaging code here

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
