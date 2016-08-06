import sqlalchemy as _alchy
from sqlalchemy.ext.declarative import declarative_base as _declarative_base

_Base = _declarative_base()


class RobotSettings(_Base):
    __tablename__ = 'robot_settings'
    id = _alchy.Column(_alchy.Integer, primary_key=True)
    # Robot context
    context = _alchy.Column(_alchy.String(length=50), unique=True)
    name = _alchy.Column(_alchy.String(length=100), default='vexbot')

    subscribe_address = _alchy.Column(_alchy.String(length=100),
                                      default='tcp://127.0.0.1:4001')

    publish_address = _alchy.Column(_alchy.String(length=100),
                                    default='tcp://127.0.0.1:4002')

    monitor_address = _alchy.Column(_alchy.String(length=100),
                                    default='tcp://127.0.0.1:4003')
