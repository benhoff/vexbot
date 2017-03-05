from sqlalchemy import Integer, Column, ForeignKey, String
from sqlalchemy.orm import relationship


from vexbot.models import Adapter


class YoutubeSettings(Adapter):
    __tablename__ = 'youtube_settings'
    id = Column(Integer, primary_key=True)
    adapter_id = Column(Integer,
                        ForeignKey('adapters.id'),
                        nullable=False)

    adapter = relationship("Adapter")
    client_secret_filepath = Column(String(length=4096))
    __mapper_args__ = {'concrete': True}


class IrcSettings(Adapter):
    __tablename__ = 'irc_settings'
    id = Column(Integer, primary_key=True)
    adapter_id = Column(Integer,
                        ForeignKey('adapters.id'),
                        nullable=False)

    adapter = relationship("Adapter")
    password = Column(String(length=100))
    channel = Column(String(length=30))
    nick = Column(String(length=30))
    host = Column(String(length=50))
    __mapper_args__ = {'concrete': True}


class XMPPSettings(Adapter):
    __tablename__ = 'xmpp_settings'
    id = Column(Integer, primary_key=True)
    adapter_id = Column(Integer,
                        ForeignKey('adapters.id'),
                        nullable=False)

    adapter = relationship("Adapter")
    password = Column(String(length=100))
    local = Column(String(length=30))
    bot_nick = Column(String(length=30))
    room = Column(String(length=30))
    domain = Column(String(length=50))

    __mapper_args__ = {'concrete': True}


class SocketIOSettings(Adapter):
    __tablename__ = 'socket_io_settings'
    id = Column(Integer, primary_key=True)
    adapter_id = Column(Integer,
                        ForeignKey('adapters.id'),
                        nullable=False)

    adapter = relationship("Adapter")
    service_name = Column(String(length=50))
    streamer_name = Column(String(length=50))
    namespace = Column(String(length=20))
    website_url = Column(String(length=200))
    __mapper_args__ = {'concrete': True}


class ShellSettings(Adapter):
    __tablename__ = 'shell_settings'
    id = Column(Integer, primary_key=True)
    history_filepath = Column(String(length=4096))
    adapter = relationship("Adapter")
    adapter_id = Column(Integer,
                        ForeignKey('adapters.id'),
                        nullable=False)

    __mapper_args__ = {'concrete': True}
