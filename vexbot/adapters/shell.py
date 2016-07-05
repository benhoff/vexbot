import cmd
import argparse
import inspect

from threading import Thread

import zmq
from vexmessage import decode_vex_message

from vexbot import __version__
from vexbot.adapters.messaging import ZmqMessaging
from vexbot.adapters.command_parser import CommandParser

from vexbot.commands.start_vexbot import start_vexbot
# from vexbot.commands.create_vexdir import create_vexdir
# from vexbot.commands.call_editor import call_editor


class Shell(cmd.Cmd):
    def __init__(self,
                 context=None,
                 prompt_name='vexbot',
                 publish_address=None,
                 subscribe_address=None,
                 **kwargs):

        super().__init__()
        self.messaging = ZmqMessaging('shell',
                                      publish_address,
                                      subscribe_address,
                                      'shell')

        self.command_parser = CommandParser(self.messaging)
        self.stdout.write('Vexbot {}\n'.format(__version__))
        self.stdout.write('Type \"help\" for command line help or \"commands\" for bot commands\n')
        if kwargs.get('already_running', False):
            self.stdout.write('vexbot already running\n')
        self.stdout.write('\n')

        self.command_parser.register_command('start vexbot',
                                             start_vexbot)

        self.messaging.start_messaging()

        self.prompt = prompt_name + ': '
        self.misc_header = "Commands"
        self._exit_loop = False

    def default(self, arg):
        if not self.command_parser.is_command(arg, call_command=True):
            self.messaging.send_command(arg)

    def run(self):
        frame = None
        while True and not self._exit_loop:
            try:
                # NOTE: not blocking here to check the _exit_loop condition
                frame = self.messaging.sub_socket.recv_multipart(zmq.NOBLOCK)
                self.stdout.write(str(self._exit_loop))
            except zmq.error.ZMQError:
                pass

            if frame:
                message = decode_vex_message(frame)
                if message.type == 'RSP':
                    self.stdout.write("\n{}\n".format(self.doc_leader))
                    # FIXME
                    if len(message.contents[0]) > 1:
                        for title, s in zip(message.contents[0],
                                            message.contents[1]):

                            self.print_topics(title, (s,), 15, 70)
                    else:
                        self.print_topics(message.contents[0][0],
                                          message.contents[1],
                                          15,
                                          70)

                    self.stdout.write("vexbot: ")
                    self.stdout.flush()

                else:
                    # FIXME
                    print(message.type,
                          message.contents,
                          'fix me in shell adapter, run function')
                frame = None

    def _create_command_function(self, command):
        def resulting_function(arg):
            self.default(' '.join((command, arg)))
        return resulting_function

    def do_EOF(self, arg):
        self.stdout.write('\n')
        # NOTE: This ensures we exit out of the `run` method on EOF
        self._exit_loop = True
        return True

    def get_names(self):
        return dir(self)

    def do_help(self, arg):
        if arg:
            if self.command_parser.is_command(arg):
                doc = self.command_parser._commands[arg].__doc__
                if doc:
                    self.stdout.write("{}\n".format(str(doc)))
            else:
                self.messaging.send_command('help ' + arg)

        else:
            self.stdout.write("{}\n".format(self.doc_leader))
            # TODO: get these from robot?
            self.print_topics(self.misc_header,
                              ['start vexbot\nhelp [foo]',],
                              15,
                              80)

    def add_completion(self, command):
        setattr(self,
                'do_{}'.format(command),
                self._create_command_function(command))

    """
    def _call_editor(self):
        vexdir = create_vexdir()
        code_output = call_editor(vexdir)
        try:
            code = compile(code_output, '<string>', 'exec')
        except Exception as e:
            print(e)

        local = {}
        exec(code, globals(), local)
        # need to add to commands?
        for k, v in local.items():
            if inspect.isfunction(v):
                self.command_parser.register_command(k, v)
    """


def _get_kwargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('--publish_address', default=None)
    parser.add_argument('--subscribe_address', default=None)
    parser.add_argument('--prompt_name', default='vexbot')

    args = parser.parse_args()
    return vars(args)


def main(**kwargs):
    if not kwargs:
        kwargs = _get_kwargs()
    shell = Shell(**kwargs)
    cmd_loop_thread = Thread(target=shell.run)
    cmd_loop_thread.daemon = True
    cmd_loop_thread.start()

    shell.cmdloop()


if __name__ == '__main__':
    main()
