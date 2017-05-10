import sys as _sys
import logging as _logging
import textwrap as _textwrap

from os import path as _path

import sqlalchemy.orm as _orm
from sqlalchemy import create_engine as _create_engine

from vexbot.models import Base, Adapter, Profile
from vexbot.util.get_settings_database_filepath import get_settings_database_filepath


def _create_session(filepath: str):
    engine = _create_engine('sqlite:///{}'.format(filepath))
    Base.metadata.bind = engine
    # TODO: decide if this is the best place to do this?
    Base.metadata.create_all(engine)
    DBSession = _orm.sessionmaker(bind=engine)
    return DBSession()


# NOTE: might need to create a database manager if this class gets too busy
class SettingsManager:
    def __init__(self,
                 database_filepath: str=None,
                 configuration: dict=None,
                 settings: dict=None):
        database_filepath = self._database_filepath_helper(database_filepath)
        self.db_session = _create_session(database_filepath)

        if configuration is None:
            configuration = {}

        self._configuration = configuration
        # error logger 
        self._logger = _logging.getLogger(__name__)
        if settings is None:
            settings = {}
        self.settings = settings

    def get_adapter_settings(self, name: str, profile: str='default'):
        return self.db_session.query(Adapter).filter(Adapter.profile == profile).all()

    def _database_filepath_helper(self, database_filepath: str=None):
        if database_filepath is None:
            database_filepath = get_settings_database_filepath()
            default_filepath = True
        else:
            default_filepath = False

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

        return database_filepath
