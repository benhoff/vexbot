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
                                      'vexbot_generate_certificates=vexbot.util.generate_certificates:main']},

    packages=find_packages(), # exclude=['docs', 'tests']
    dependency_links=[
        'git+https://github.com/jonathanslenders/python-prompt-toolkit@2.0',
        ],

    install_requires=[
        # 'pluginmanager>=0.4.1',
        'pyzmq',
        'vexmessage>=0.4.0',
        'rx',
        'tblib',
        ],

    extras_require={
        'dev': ['flake8', 'twine'],
        'process_manager': ['pydbus'],
        'speechtotext': ['speechtotext'],
        'gui': ['chatimusmaximus'],
        'irc': ['irc3'],
        'socket_io': ['requests', 'websocket-client'],
        'xmpp': ['sleekxmpp', 'dnspython'],
        'youtube': ['google-api-python-client'],
        'microphone': ['microphone'],
        'process_name': ['setproctitle'],
        'database': ['vexstorage'],
    }
)
