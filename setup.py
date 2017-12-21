import os
import re

from setuptools import find_packages, setup

VERSIONFILE = 'vexbot/_version.py'
verstrline = open(VERSIONFILE, 'rt').read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    verstr = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in {}".format(VERSIONFILE))


# directory = os.path.abspath(os.path.dirname(__file__))
"""
with open(os.path.join(directory, 'README.rst')) as f:
    long_description = f.read()
"""

extensions = {'pip_install': {'path': 'vexbot.extensions.admin.install',
                              'short': 'Install packages using pip',
                              'extras': ['pip',]},
              'pip_uninstall': {'path': 'vexbot.extensions.admin.uninstall',
                                'short': 'Uninstall packages using pip',
                                'extras': ['pip',]},
              'pip_update': {'path': 'vexbot.extensions.admin.update',
                             'short': 'Update packages using pip',
                                'extras': ['pip',]},
              'get_commands': {'path': 'vexbot.extensions.admin.get_commands',
                               'short': 'Get commands from command observer'},
              'get_disabeled': {'path': 'vexbot.extensions.admin.get_disabled',
                                'short': 'Get all disabled commands from command observer'},
              'get_code': {'path': 'vexbot.extensions.develop.get_code',
                           'short': 'Get the source code from a method using the inspect module'},
              'get_method_names': {'path': 'vexbot.extensions.develop.get_members',
                                   'short': 'Get all the method names from a class using inspect module'},
              'get_size': {'path': 'vexbot.extensions.digitalocean.get_size',
                           'short': 'Get the size of a digital ocean droplet',
                           'extras': ['digitalocean',]},
              'power_off': {'path': 'vexbot.extensions.digitalocean.power_off',
                            'short': 'Power off a digital ocean droplet',
                           'extras': ['digitalocean',]},
              'power_on': {'path': 'vexbot.extensions.digitalocean.power_on',
                           'short': 'Power on a digital ocean droplet',
                           'extras': ['digitalocean',]},
              'get_all_droplets': {'path': 'vexbot.extensions.digitalocean.get_all_droplets',
                                   'short': 'Get all droplets from digital ocean',
                                   'extras': ['digitalocean',]},
              'add_extension': {'path': 'vexbot.extensions.extensions.add_extension',
                                'short': 'Add an extension to a command observer'},
              'get_extensions': {'path': 'vexbot.extensions.extensions.get_extensions',
                                 'short': 'Get all the extensions from an observer instance'},
              'remove_extensions': {'path': 'vexbot.extensions.remove_extensions',
                                    'short': 'Remove an extension from an observer instance'},
              'help': {'path': 'vexbot.extensions.help.help',
                       'short': 'Get the help from a method'},
              'hidden': {'path': 'vexbot.extensions.hidden',
                         'short': 'Get all hidden method methods'},
              'bot_intents': {'path': 'vexbot.extensions.intents.get_intents',
                              'short': 'Get the intents from the bot'},
              'bot_intent': {'path': 'vexbot.extensions.intents.get_intent', 'short': ''},
              'get_google_trends': {'path': 'vexbot.extensions.news.get_hot_trends',
                                    'short': 'Get the google trends',
                                    'extras': ['gensim', 'newspaper']},
              'get_news_urls': {'path': 'vexbot.extensions.news.get_popular_urls',
                                'short': '',
                                'extras': ['gensim', 'newspaper']},
              'summarize_news_url': {'path': 'vexbot.extensions.news.summarize_article',
                                     'short': '',
                                     'extras': ['gensim', 'newspaper']},
              # extras -> pydbus
              'start_process': {'path': 'vexbot.extensions.subprocess.start', 'short': ''},
              'stop_process': {'path': 'vexbot.extensions.subprocess.stop', 'short': ''},
              'restart_process': {'path': 'vexbot.extensions.subprocess.restart', 'short': ''},
              'status_process': {'path': 'vexbot.extensions.subprocess.status', 'short': ''}}

_str_form = '{}={}{}'
_result = []
for name, extension in extensions.items():
    extras = extension.get('extras')
    if extras is None:
        extras = ''
    else:
        extras = ', '.join(extras)
        extras = ' [' + extras + ']'
    line = _str_form.format(name, extension['path'], extras)
    _result.append(line)

setup(
    name="vexbot",
    version=verstr,
    description='Python personal assistant',
    # long_description=long_description,
    url='https://github.com/benhoff/vexbot',
    license='GPL3',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Operating System :: OS Independent'],
    author='Ben Hoff',
    author_email='beohoff@gmail.com',
    entry_points={'console_scripts': ['vexbot=vexbot.adapters.shell.__main__:main',
                                      'vexbot_robot=vexbot.__main__:main',
                                      'vexbot_irc=vexbot.adapters.irc.__main__:main',
                                      'vexbot_xmpp=vexbot.adapters.xmpp:main',
                                      'vexbot_socket_io=vexbot.adapters.socket_io.__main__:main',
                                      'vexbot_youtube=vexbot.adapters.youtube:main',
                                      'vexbot_stackoverflow=vexbot.adapters.stackoverflow:main',
                                      'vexbot_generate_certificates=vexbot.util.generate_certificates:main'],
                    'vexbot_extensions': _result},
    packages=find_packages(), # exclude=['docs', 'tests']
    dependency_links=[
        'git+https://github.com/jonathanslenders/python-prompt-toolkit@2.0',
	'git+https://github.com/benhoff/vexmessage@dev'
        ],

    install_requires=[
        # 'pluginmanager>=0.4.1',
        'pyzmq',
        'vexmessage>=0.4.0',
        'rx',
        'tblib', # traceback serilization
        'tornado',
        ],

    extras_require={
        'nlp': ['spacy', 'sklearn', 'sklearn_crfsuite', 'wheel'],
        'socket_io': ['requests', 'websocket-client'],
        'summarization': ['gensim', 'newspaper3k'],
        'youtube': ['google-api-python-client'],
        'dev': ['flake8', 'twine', 'wheel'],
        'xmpp': ['sleekxmpp', 'dnspython'],
        'process_name': ['setproctitle'],
        'speechtotext': ['speechtotext'],
        'process_manager': ['pydbus'],
        'microphone': ['microphone'],
        'database': ['vexstorage'],
        'gui': ['chatimusmaximus'],
        'entity': ['duckling'],
        'irc': ['irc3'],
    }
)
