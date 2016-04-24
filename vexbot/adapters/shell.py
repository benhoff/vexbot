import cmd
import argparse

import zmq

from vexbot.adapters.communication_messaging import ZmqMessaging


class Shell(cmd.Cmd):
    def __init__(self,
                 context=None,
                 prompt_name='vexbot',
                 pub_address='tcp://127.0.0.1:5555'):

        super().__init__()
        self.messaging = ZmqMessaging('shell', pub_address)
        self.prompt = prompt_name + ': '

    def default(self, arg):
        self.messaging.send_message(arg)

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
    parser.add_argument('--pub_address', default='tcp://127.0.0.1:5555')
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
