from sqlalchemy import create_engine as _create_engine

import vexbot.robot_settings as _robot
import vexbot.adapters.shell as _shell
import vexbot.adapters.irc as _irc
import vexbot.adapters.xmpp as _xmpp
import vexbot.adapters.youtube_api as _youtube
import vexbot.adapters.socket_io as _socket


from vexbot.util.get_settings_database_filepath import get_settings_database_filepath


def create_database():
    database_filepath = get_settings_database_filepath()
    engine = _create_engine('sqlite:///{}'.format(database_filepath))
    for file in [_robot, _shell, _socket, _irc, _xmpp, _youtube]:
        file.Base.metadata.create_all(engine)
