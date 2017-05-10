from sqlalchemy import Integer, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from vexbot.models import Adapter


class IrcSettings(Adapter):
    __tablename__ = 'irc_settings'
    adapter = relationship("Adapter")
    adapter_id = Column(Integer,
                        ForeignKey('adapters.id'),
                        primary_key=True)

    password = Column(String(length=100))
    channel = Column(String(length=30))
    nick = Column(String(length=30))
    host = Column(String(length=50))
    module_name = 'irc'

    __mapper_args__ = {'polymorphic_identity': module_name}


class XMPPSettings(Adapter):
    __tablename__ = 'xmpp_settings'
    adapter = relationship("Adapter")
    adapter_id = Column(Integer,
                        ForeignKey('adapters.id'),
                        primary_key=True)

    password = Column(String(length=100))
    local = Column(String(length=30))
    bot_nick = Column(String(length=30))
    room = Column(String(length=30))
    domain = Column(String(length=50))
    module_name = 'xmpp'

    __mapper_args__ = {'polymorphic_identity': module_name}


class SocketIOSettings(Adapter):
    __tablename__ = 'socket_io_settings'
    adapter = relationship("Adapter")
    adapter_id = Column(Integer,
                        ForeignKey('adapters.id'),
                        primary_key=True)

    streamer_name = Column(String(length=50))
    namespace = Column(String(length=20))
    website_url = Column(String(length=200))
    module_name = 'socket_io'

    __mapper_args__ = {'polymorphic_identity': module_name}
