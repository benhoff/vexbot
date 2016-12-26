import os
import sys
import textwrap
import logging

import sqlalchemy as _alchy
import sqlalchemy.orm as _orm

from sqlalchemy import create_engine as _create_engine

from vexbot.models import Base, RobotModel, Adapter, Module, ZmqAddress
import vexbot.adapters.models
from vexbot.util.get_settings_database_filepath import get_settings_database_filepath


def _create_session(filepath):
    engine = _create_engine('sqlite:///{}'.format(filepath))
    Base.metadata.bind = engine
    # TODO: decide if this is the best place to do this?
    Base.metadata.create_all(engine)
    DBSession = _orm.sessionmaker(bind=engine)
    return DBSession()


class SettingsManager:
    def __init__(self, filepath=None, context='default'):
        self._logger = logging.getLogger(__name__)
        default_filepath = False
        if filepath is None:
            filepath = get_settings_database_filepath()
            default_filepath = True

        if not os.path.isfile(filepath):
            s = 'Database filepath: {} not found.'.format(filepath)
            if default_filepath:
                s = s + (' Please run `$ vexbot_create_database` from the cmd line to create settings database. '
                         'Then run `create_robot_models` from the shell adapter. '
                         'Alternatively run `$ vexbot_quickstart`')

            s = textwrap.fill(s, initial_indent='', subsequent_indent='    ')
            self._logger.error(s)
            sys.exit(1)

        self.session = _create_session(filepath)
        self._context = context
        try:
            self._context_settings = self.get_robot_model(context)
        except _alchy.exc.OperationalError:
            self._context_settings = None

    @property
    def context(self):
        return self._context

    @context.setter
    def context(self, context):
        settings = self.get_robot_model(context)
        self._context_settings = settings

    def get_all_contexts(self):
        return self.session.query(RobotModel.context)[0]

    def get_all_addresses(self):
        return self.session.query(ZmqAddress.address)[0]

    def get_startup_adapters(self, context=None):
        model = self.get_robot_model(context)
        adapters = model.startup_adapters
        return adapters

    def create_default(self):
        pub = self.get_or_create_address('127.0.0.1:4001')
        heartbeat = self.get_or_create_address('127.0.0.1:4002')

        model = RobotModel(context='default',
                           name='vexbot',
                           publish_address=pub,
                           heartbeat_address=heartbeat)

        sub = self.get_or_create_address('127.0.0.1:4000')
        model.subscribe_addresses.append(sub)
        self.session.add(model)
        self.session.commit()

        return True


    def get_or_create_address(self, address):
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

    def get_robot_model(self, context=None):
        """
        Can return `None`
        """
        if context is None:
            return self._context_settings

        settings = self.session.query(RobotModel).\
                filter(RobotModel.context == context).first()

        return settings

    def _handle_startup_adapters(self,
                                 model: RobotModel,
                                 startup_adapters: list):

        for adapter in startup_adapters:
            if isinstance(adapter, Adapter):
                model.startup_adapters.append(adapter)
            else:
                adapter = self.session.query(Adapter).\
                        filter(Adapter.name==adapter).first()

                print(adapter, bool(adapter))

                if adapter:
                    model.startup_adapters.append(adapter)

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
