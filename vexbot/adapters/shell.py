import cmd
import argparse

import zmq

from vexbot.util import start_vexbot
from vexbot.adapters.communication_messaging import ZmqMessaging

"""
classifier_data = []

self.callback_manager = CallbackManager()

for intent, intent_data in data['adapters'].items():
    intent_data_for_classifier = [(d, intent)
                                  for d
                                  in intent_data['training_data']]

    classifier_data.extend(intent_data_for_classifier)
    c = self.adapter_starter.track_adapter(intent, intent_data)
    self.callback_manager.associate_key_with_callback(intent, c)

self.parser = ClassifyParser(classifier_data)
self.parser.add_callback_manager(self.callback_manager)

# adapters are inputs into the bot. Like a mic or shell input
adapter_manager = pluginmanager.PluginInterface()
adapter_manager.set_entry_points('vexbot.adapters')
plugins = adapter_manager.collect_entry_point_plugins()
pub_address = 'tcp://127.0.0.1:5555'
self.messaging.subscribe_to_address(pub_address)
"""


class Shell(cmd.Cmd):
    def __init__(self,
                 context=None,
                 prompt_name='vexbot',
                 publish_address=None,
                 subscribe_address=None):

        super().__init__()
        self.messaging = ZmqMessaging('shell',
                                      publish_address,
                                      subscribe_address)

        self.messaging.register_command('start vexbot',
                                        start_vexbot)

        # self.messaging.set_socket_identity('shell')
        self.messaging.set_socket_filter('')
        self.messaging.start_messaging()

        self.prompt = prompt_name + ': '

    def default(self, arg):
        if not self.messaging.is_command(arg):
            self.messaging.send_message('CMD', arg)
            if self.messaging.sub_socket.getsockopt(zmq.IDENTITY):
                frame = self.messaging.sub_socket.recv_pyobj()
                print(frame)

    def _create_command_function(self, command):
        def resulting_function(arg):
            self.default(' '.join((command, arg)))
        return resulting_function

    def do_EOF(self, arg):
        print()
        return True

    def get_names(self):
        return dir(self)

    def add_completion(self, command):
        setattr(self,
                'do_{}'.format(command),
                self._create_command_function(command))


def _get_kwargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('--publish_address', default=None)
    parser.add_argument('--prompt_name', default='vexbot')

    args = parser.parse_args()
    return vars(args)


def main(**kwargs):
    if not kwargs:
        kwargs = _get_kwargs()
    shell = Shell(**kwargs)
    shell.cmdloop()

if __name__ == '__main__':
    main()
