# pylint: disable-all
from packs.server import Server, Logger as ServerLogger

server = Server(('127.0.0.1', 2000), 1)
ServerLogger.debug(server)
server.main_loop()
