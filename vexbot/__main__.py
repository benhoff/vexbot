import atexit
import textwrap
from os import path

import yaml

from vexbot.commands.start_vexbot import start_vexbot
from vexbot.adapters.shell import main as shell_main


def _kill_vexbot(process):
    def inner():
        process.terminate()

    return inner


def _get_settings(filepath=None):
    """
    if not filepath is passed in, gets default settings
    """
    if filepath is None:
        file_dir = path.abspath(path.dirname(__file__))
        filepath = path.join(file_dir, 'default_settings.yml')
    with open(filepath) as f:
        settings = yaml.load(f)

    return settings

def _handle_filepath(responses):
    # NOTE: might need to move this up a scope level?
    response_str = ','.join(responses)
    filepath = None
    default = 'Using an absolute filepath please input desired filepath: '
    while not filepath:
        filepath = input(default)

        if filepath in responses:
            return _handle_file_not_found(filepath)
        elif not path.isfile(filepath):
            string = textwrap.fill("filepath '{}' not found. Either try again"
                                   " or choose a different method from "
                                   "[{}]".format(filepath, response_str))

            nl = '\n'
            # Textwrap and I disagree about how this should be displayed
            print(nl + string + nl)

            filepath = None

    return _get_settings(filepath)

def _handle_create():
    # TODO: decide if this is needed or not
    # default = _get_default_config()

    word_default = (['kill vexbot on exit from shell', 'kill_on_exit',
                     False],

                    ['Subscription address', 'subscribe_address',
                     'tcp://127.0.0.1:4001'],

                    ['Publish address', 'publish_address',
                     'tcp://127.0.0.1:4002'],

                    ['Monitor address', 'monitor_address',
                     'tcp://127.0.0.1: 4003'])

    generate_settings = {}
    input_value = ''

    # NOTE: method declared so we can recurse for case of re-entering
    # previous key
    def get_input(word, default, key=None, previous=None):
        if key is None:
            key = word

        input_value = input('{} [{}]: '.format(word, default))
        # TODO
        if previous:
            if input_value == previous[0]:
                get_input(previous[0], previous[1])
        if input_value == '':
            input_value = default
        generate_settings[key] = input_value
        print("{{'{}': '{}'}}\n".format(key, input_value))

    for word, key, default in word_default:
        get_input(word, default, key)

    return generate_settings


def _handle_file_not_found(response=None):
    responses = ('filepath', 'create')

    while response not in responses:
        response = input(textwrap.fill('Settings filepath not found. Would you'
                                       ' like to create one or supply a '
                                       'filepath? [create, filepath]:') + ' ')

    if response == 'filepath':
        return _handle_filepath(responses)
    elif response == 'create':
        return _handle_create()


def main():
    file_found = True
    try:
        settings, process = start_vexbot()
    except FileNotFoundError:
        file_found = False

    if not file_found:
        settings = _handle_file_not_found()
        _, process = start_vexbot(settings)

    if process and settings.get('kill_on_exit', False):
        atexit.register(_kill_vexbot(process))

    shell_settings = settings.get('shell', {})
    if process is None:
        already_running = True
    else:
        already_running = False
    shell_settings['--already_running'] = already_running
    for key in set(shell_settings.keys()):
        value = shell_settings.pop(key)
        shell_settings[key[2:]] = value

    # Launch the shell interface
    shell_main(**shell_settings)


if __name__ == "__main__":
    main()
