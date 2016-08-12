import sqlalchemy as _alchy
import sqlalchemy.orm as _orm

from sqlalchemy import create_engine as _create_engine

from vexbot.sql_helper import Base
from vexbot.robot_settings import RobotSettings, Adapters
from vexbot.subprocess_manager import SubprocessDefaultSettings
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
        self.context = context
        if filepath is None:
            filepath = get_settings_database_filepath()

        self.session = _create_session(filepath)

    def get_robot_settings(self, context=None) -> RobotSettings:
        if context is None:
            context = self.context
        settings = self.session.query(RobotSettings).\
                filter(RobotSettings.context == context).first()

        return settings

    def get_subprocess_settings(self, context=None):
        if context is None:
            context = self.context
        robot_id = self.session.query(RobotSettings).\
                filter(RobotSettings.context == context).first().id

        settings = self.session.query(SubprocessDefaultSettings).\
                filter(SubprocessSettings.robot_id == robot_id).all()

        return settings

    def create_robot_settings(self, settings: dict):
        # TODO: Validate settings here instead of passing in directly
        new_robot = RobotSettings(**settings)
        self.session.add(new_robot)
        self.session.commit()
        # TODO: return validation errors, if any

    def get_settings_dict(self, settings):
        pass

    def get_startup_adapters(self, context=None):
        if context is None:
            context = self.context

        settings = self.get_robot_settings(context)

        adapters = self.session.query(Adapters).\
                filter(Adapters.contexts.any(context=settings)).all()

        return adapters
