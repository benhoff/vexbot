import types
import logging

import pluginmanager

from vexbot.messaging import Messaging
from vexbot.subprocess_manager import SubprocessManager
from vexbot.argenvconfig import ArgEnvConfig


class Robot:
    def __init__(self, configuration, bot_name="vex"):
        self.name = bot_name
        self._logger = logging.getLogger(__name__)
        self.messaging = Messaging()
        self.plugin_manager = pluginmanager.PluginInterface()
        self.plugin_manager.add_entry_points(('vexbot.plugins',
                                              'vexbot.adapters'))

        self.subprocess_manager = SubprocessManager()

        collect_ep = self.plugin_manager.collect_entry_point_plugins
        plugins, plugin_names = collect_ep()
        plugins = [plugin.__file__ for plugin in plugins]
        self.subprocess_manager.register(plugin_names, plugins)
        settings_path = config.get('settings_path')
        settings = config.load_settings(settings_path)
        self.messaging.pub_socket.bind(settings['robot_address'])

        for name in plugin_names:
            try:
                plugin_settings = settings[name]
                values = []
                for k_v in plugin_settings.items():
                    values.extend(k_v)
            except KeyError:
                values = []
            self.subprocess_manager.update(name, setting=values)

        self.subprocess_manager.start(settings['startup_plugins'])
        self.subprocess_manager.start(settings['startup_adapters'])

        self.listeners = []
        self.commands = []

        self.catch_all = None

    def run(self):
        while True:
            pass
        """
            frame = self.messaging.sub_socket.recv_pyobj()
            # I.E. Shell adapter
            source = frame[0]
            msg = frame[1]
            results = self.parser.parse(msg)

            # check to see if go into a context mode here?
            with self.parser.parse(msg):
                pass
        """

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
