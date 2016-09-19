import os
import sys
import textwrap
import logging

import sqlalchemy as _alchy
import sqlalchemy.orm as _orm

from sqlalchemy import create_engine as _create_engine

from vexbot.sql_helper import Base
from vexbot.robot_models import RobotModel, Adapter
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

    def add_adapters(self, adapters: list):
        # FIXME
        self.update_adapters(adapters)

    def add_adapter(self, adapter: str):
        new_adapter = Adapter(name=adapter)
        self.session.add(new_adapter)
        self.session.commit()

    def get_robot_model(self, context=None):
        """
        Can return `None`
        """
        if context is None:
            return self._context_settings

        try:
            settings = self.session.query(RobotModel).\
                    filter(RobotModel.context == context).first()
        except _alchy.exc.OperationalError:
            return None

        return settings

    def get_shell_settings(self, context=None):
        if context is None:
            settings = self._context_settings
        else:
            settings = self.get_robot_model(context)
        settings = self.session.query('shell_settings').\
                filter(robot=settings.id).first()

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

    def create_robot_model(self, settings: dict):
        adapters = settings.pop('startup_adapters', [])
        # TODO: Validate settings here instead of passing in directly
        new_robot = RobotModel(**settings)
        self._handle_startup_adapters(new_robot, adapters)


        self.session.add(new_robot)
        self.session.commit()
        # TODO: return validation errors, if any

    def update_robot_model(self, settings: dict):
        adapters = settings.pop('startup_adapters', [])
        model = self.session.query(RobotModel).\
                filter(RobotModel.id == settings.pop('id')).first()
        self._handle_startup_adapters(model, adapters)
        for k, v in settings.items():
            setattr(model, k, v)

        self.session.commit()

    def get_startup_adapters(self, context=None):
        if context is None:
            settings = self._context_settings
        else:
            settings = self.get_robot_model(context)

        return [x.name for x in settings.startup_adapters]

    def get_robot_contexts(self):
        result = self.session.query(RobotModel.context).all()[0]
        return result

    def get_adapter_settings(self, kls, context=None):
        pass

    def update_adapters(self, adapters: list):
        for adapter in adapters:
            instance = self.session.query(Adapter).\
                    filter(Adapter.name==adapter).first()
            if instance:
                continue
            else:
                instance = Adapter(name=adapter)
                self.session.add(instance)

        self.session.commit()
