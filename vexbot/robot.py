import sys
import types
import logging
import pickle

import zmq
import zmq.devices
import pluginmanager

from vexbot.subprocess_manager import SubprocessManager
from vexbot.argenvconfig import ArgEnvConfig


class Robot:
    def __init__(self, configuration, bot_name="vex"):
        # get the settings path and then load the settings from file
        settings_path = configuration.get('settings_path')
        settings = configuration.load_settings(settings_path)

        # create the plugin manager
        self.plugin_manager = pluginmanager.PluginInterface()
        # add the entry points of interest
        self.plugin_manager.add_entry_points(('vexbot.plugins',
                                              'vexbot.adapters'))

        # create the subprocess manager and add in the plugins
        self.subprocess_manager = SubprocessManager()
        self._update_plugins(settings,
                             self.subprocess_manager,
                             self.plugin_manager)

        subprocesses_to_start = settings.get('startup_adapters', [])
        subprocesses_to_start.extend(settings.get('startup_plugins', []))
        self.subprocess_manager.start(subprocesses_to_start)

        self.name = bot_name
        self._logger = logging.getLogger(__name__)
        context = zmq.Context()

        self._proxy = zmq.devices.ThreadProxy(zmq.XSUB, zmq.XPUB)
        proxy_address = 'tcp://127.0.0.1:4002'
        subscribe_address = settings.get('subscribe_address',
                                         'tcp://127.0.0.1:4000')

        publish_address = settings.get('publish_address',
                                       'tcp://127.0.0.1:4001')

        self._proxy.bind_in(subscribe_address)
        self._proxy.bind_out(publish_address)

        self._proxy.bind_mon(proxy_address)
        name = b'vexbot'

        self._monitor_socket = context.socket(zmq.SUB)
        # self._monitor_socket.setsockopt(zmq.SUBSCRIBE, name)
        self._monitor_socket.setsockopt(zmq.SUBSCRIBE, b'')
        self._monitor_socket.connect(proxy_address)

        self._publish_socket = context.socket(zmq.PUB)
        # self._publish_socket.setsockopt(zmq.IDENTITY, name)
        self._publish_socket.connect(publish_address)

        self._proxy.start()

        self.listeners = []
        self.commands = []

        self.catch_all = None

    def _run_command(self, command):
        commands = command.split()
        command = commands.pop(0)
        if command == 'start':
            self.subprocess_manager.start(commands)
        elif command == 'restart':
            self.subprocess_manager.restart(commands)
        elif command == 'kill':
            self.subprocess_manager.kill(commands)
        elif command == 'killall':
            self.subprocess_manager.killall()
            sys.exit()
        elif command == 'list':
            # how do I send information back?
            pass

    def run(self):
        while True:
            frame = self._monitor_socket.recv()
            try:
                frame = pickle.loads(frame)
            except (pickle.UnpicklingError, EOFError):
                frame = None
            if frame:
                frame_len = len(frame)
                if frame[1] == 'CMD':
                    self._run_command(frame[2])

    def _update_plugins(self,
                        settings,
                        subprocess_manager=None,
                        plugin_manager=None):
        """
        Helper process which loads the plugins from the entry points
        """
        if subprocess_manager is None:
            subprocess_manager = self.subprocess_manager
        if plugin_manager is None:
            plugin_manager = self.plugin_manager

        collect_ep = plugin_manager.collect_entry_point_plugins
        plugins, plugin_names = collect_ep()
        plugins = [plugin.__file__ for plugin in plugins]
        subprocess_manager.register(plugin_names, plugins)

        for name in plugin_names:
            try:
                plugin_settings = settings[name]
                values = []
                for k_v in plugin_settings.items():
                    values.extend(k_v)
            except KeyError:
                values = []
            self.subprocess_manager.update(name, setting=values)

    def listener_middleware(self, middleware):
        self.listener_middleware.stack.append(middleware)

    def _process_listeners(self, response, done=None):
        for listener in self.listeners:
            result, done = listener.call(response.message.command,
                                         response.message.argument,
                                         done)

            # self.listener_middleware.execute(result, done=done)

            if isinstance(done, bool) and done:
                # TODO: pass back to the appropriate adapter?
                print(result)
                return
            elif isinstance(done, types.FunctionType) and result:
                done()
                print(result)
                return

        if self.catch_all is not None:
            self.catch_all()

    def recieve(self, message, callback=None):
        """
        response = Response(self, message)
        done = self.receive_middleware.execute(response,
                                               self._process_listeners,
                                               callback)

        if isinstance(done, bool) and done:
            return
        self._process_listeners(response, done)
        """
        pass

    def shutdown(self):
        pass


def _get_config():
    config = ArgEnvConfig()
    config.add_argument('--settings_path',
                        default='settings.yml',
                        action='store')

    return config


if __name__ == '__main__':
    config = _get_config()
    robot = Robot(config)
    robot.run()
