import sys
import atexit
import signal
from vexbot._version import __version__ as version

from vexbot.adapters.irc import IrcInterface

"""
try:
    pkg_resources.get_distribution('irc3')
except pkg_resources.DistributionNotFound:
    _IRC3_INSTALLED = False

if _IRC3_INSTALLED:
    import irc3

else:
    pass
"""

import irc3
from irc3 import utils


def main(**kwargs):
    """
    if not _IRC3_INSTALLED:
        logging.error('vexbot_irc requires `irc3` to be installed. Please install '
                      'using `pip install irc3`')

        sys.exit(1)
    """

    config = _from_argv(irc3.IrcBot, kwargs=kwargs)
    if not 'includes' in config:
        config['includes'] = []

    message_plug = 'vexbot.adapters.irc.echo_to_message'
    if not message_plug in config['includes']:
        config['includes'].append(message_plug)
    service_name = config.get('service_name', 'irc')
    connection = config.get('connection', {})
    interface = IrcInterface(service_name, irc_config=config, connection=connection)

    interface.run()
    sys.exit()


# NOTE: This code is from `irc3`
def _from_argv(cls, argv=None, **kwargs) -> dict:
    prog = cls.server and 'irc3d' or 'irc3'
    # TODO: Add in publish ports and all that jazz.
    doc = """
    Run an __main__.py instance from a config file

    Usage: __main__.py [options] <config>...

    Options:
    -h, --help          Display this help and exit
    --version           Output version information and exit
    --logdir DIRECTORY  Log directory to use instead of stderr
    --logdate           Show datetimes in console output
    --host HOST         Server name or ip
    --port PORT         Server port
    -v,--verbose        Increase verbosity
    -r,--raw            Show raw irc log on the console
    -d,--debug          Add some debug commands/utils
    """
    import os
    import docopt
    import textwrap
    args = argv or sys.argv[1:]
    args = docopt.docopt(doc, args, version=version)
    cfg = utils.parse_config(
        cls.server and 'server' or 'bot', *args['<config>'])
    cfg.update(
        verbose=args['--verbose'],
        debug=args['--debug'],
    )
    cfg.update(kwargs)
    if args['--host']:  # pragma: no cover
        host = args['--host']
        cfg['host'] = host
        if host in ('127.0.0.1', 'localhost'):
            cfg['ssl'] = False
    if args['--port']:  # pragma: no cover
        cfg['port'] = args['--port']
    if args['--logdir'] or 'logdir' in cfg:
        logdir = os.path.expanduser(args['--logdir'] or cfg.get('logdir'))
        cls.logging_config = config.get_file_config(logdir)
    if args['--logdate']:  # pragma: no cover
        fmt = cls.logging_config['formatters']['console']
        fmt['format'] = config.TIMESTAMPED_FMT
    if args.get('--help-page'):  # pragma: no cover
        for v in cls.logging_config['handlers'].values():
            v['level'] = 'ERROR'
    if args['--raw']:
        cfg['raw'] = True

    return cfg

if __name__ == '__main__':
    main()
