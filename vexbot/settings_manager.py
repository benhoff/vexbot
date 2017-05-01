import sys as _sys
import logging as _logging
import textwrap as _textwrap

from os import path as _path
import sqlalchemy as _alchy
import sqlalchemy.orm as _orm

from sqlalchemy import create_engine as _create_engine

from vexbot.subprocess_manager import SubprocessManager
from vexbot.models import Base, RobotModel, Adapter, Module, ZmqAddress
from vexbot.util.get_settings_database_filepath import get_settings_database_filepath


def _create_session(filepath: str):
    engine = _create_engine('sqlite:///{}'.format(filepath))
    Base.metadata.bind = engine
    # TODO: decide if this is the best place to do this?
    Base.metadata.create_all(engine)
    DBSession = _orm.sessionmaker(bind=engine)
    return DBSession()


"""
plugin_manager = pluginmanager.PluginInterface()
collect = plugin_manager.collect_entry_point_plugins
plugin_settings = collect('vexbot.adapter_settings',
                          return_dict=True)

self._settings_manager.update_modules(subprocesses.keys())
try:
    # using convention to snag plugin settings.
    # expect that settings will be in the form of
    # `adapter_name` + `_settings`
    # I.E. `irc_settings` for adapter `irc`
    setting_name = name + '_settings'
    setting_class = plugin_settings[setting_name
except KeyError:
    setting_class = None
"""


class SettingsManager:
    def __init__(self, database_filepath: str=None)
        self._logger = _logging.getLogger(__name__)
        self.subprocess_manager = SubprocessManager()
        if database_filepath is None:
            database_filepath = get_settings_database_filepath()
            default_filepath = True
        else:
            default_filepath = False

        if config_settings is None:
            config_settings = dict()

        if not _path.isfile(database_filepath):
            s = 'Database filepath: {} not found.'.format(filepath)
            if default_filepath:
                s = s + (' Please run `$ vexbot_create_database` from the cmd '
                         'line to create settings database. Then run `create_r'
                         'obot_models` from the shell adapter. Alternatively r'
                         'un `$ vexbot_quickstart`')

            s = _textwrap.fill(s, initial_indent='', subsequent_indent='    ')
            self._logger.error(s)
            _sys.exit(1)

        self.session = _create_session(database_filepath)
        try:
            self._profile_settings = self.get_robot_model(profile)
        except _alchy.exc.OperationalError:
            self._profile_settings = None

    @property
    def profile(self):
        return self._profile

    @profile.setter
    def profile(self, profile: str):
        settings = self.get_robot_model(profile)
        self._profile_settings = settings

    def get_all_profiles(self):
        return self.session.query(RobotModel.profile)[0]

    def get_all_addresses(self):
        return self.session.query(ZmqAddress.address)[0]

    def get_adapter_settings(self, adapter_names: list, profile: str=None):
        raise NotImplemented('Fixme, please')

    def start_startup_adapters(self, profile: str=None):
        adapters = self.get_startup_adapters(profile)
        adapter_settings = self.get_adapter_settings(adapters, profile)
        self.subprocess_manager.start(adapters, adapter_settings)

    def create_default(self):
        pub = self.get_or_create_address('127.0.0.1:4001')
        heartbeat = self.get_or_create_address('127.0.0.1:4002')

        model = RobotModel(profile='default',
                           name='vexbot',
                           publish_address=pub,
                           heartbeat_address=heartbeat)

        sub = self.get_or_create_address('127.0.0.1:4000')
        model.subscribe_addresses.append(sub)
        self.session.add(model)
        try:
            self.session.commit()
        except _alchy.exc.IntegrityError:
            self._logger.warn('Default profile already created!')

        return True

    def get_or_create_address(self, address: str):
        if address.startswith('tcp://'):
            # TODO: CHECK that this works
            address = address[6:]

        address_obj = self.session.query(ZmqAddress).\
                filter(ZmqAddress.address == address).first()
        if address_obj:
            return address_obj

        address = ZmqAddress(address=address)
        self.session.add(address)
        return address

    def add_module(self, module: str):
        instance = Module(name=module)
        self.session.add(instance)
        self.session.commit()

    def get_robot_model(self, profile: str=None):
        """
        Can return `None`
        """
        if profile is None:
            return self._profile_settings

        settings = self.session.query(RobotModel).\
                filter(RobotModel.profile==profile).first()

        return settings

    def update_modules(self, modules: list):
        for module in modules:
            instance = self.session.query(Module).\
                    filter(Module.name==module).first()
            if instance:
                continue
            else:
                instance = Module(name=module)
                self.session.add(instance)

        self.session.commit()
