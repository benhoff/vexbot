import os
from setuptools import find_packages, setup


# directory = os.path.abspath(os.path.dirname(__file__))
"""
with open(os.path.join(directory, 'README.rst')) as f:
    long_description = f.read()
"""

setup(
    name="vexbot",
    version='0.0.5',
    description='Python personal assistant',
    # long_description=long_description,
    url='https://github.com/benhoff/vexbot',
    license='GPL3',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Operating System :: OS Independent'],
    author='Ben Hoff',
    author_email='beohoff@gmail.com',
    entry_points={'vexbot.adapters': ['shell=vexbot.adapters.shell',
                                      'irc = vexbot.adapters.irc',
                                      'xmpp = vexbot.adapters.xmpp',
                                      'socket_io = vexbot.adapters.socket_io',
                                      'youtube_api = vexbot.adapters.youtube_api'],

                  'console_scripts': ['vexbot=vexbot.__main__:main']},

    packages= find_packages(), # exclude=['docs', 'tests']
    install_requires=[
        'pluginmanager',
        'pyzmq',
        ],

    extras_require={
        'dev': ['flake8', 'twine'],
        'speechtotext': ['speechtotext'],
        'gui': ['chatimusmaximus'],
        'javascript_webscrapper': ['selenium'],
        'irc': ['irc'],
        'socket_io': ['requests', 'websocket-client'],
        'xmpp': ['sleekxmpp', 'dnspython3'],
        'youtube': ['google-api-python-client'],
    }
)
