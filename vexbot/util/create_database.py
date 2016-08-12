from sqlalchemy import create_engine as _create_engine

import vexbot.robot_settings as _robot
import vexbot.adapters.shell as _shell
import vexbot.adapters.irc as _irc
import vexbot.adapters.xmpp as _xmpp
import vexbot.adapters.youtube_api as _youtube
import vexbot.adapters.socket_io as _socket
import vexbot.robot_settings

from vexbot.sql_helper import Base


from vexbot.util.get_settings_database_filepath import get_settings_database_filepath


def create_database():
    database_filepath = get_settings_database_filepath()
    engine = _create_engine('sqlite:///{}'.format(database_filepath))

    Base.metadata.create_all(engine)
