"""Application CMD"""
# pylint: disable=unused-argument
from cmd import Cmd
from typing import IO

from packs._gui.config import AppConfig
from packs.client import AppClient
from packs.gui import Application as Game
from packs.server import Server
from packs.utils import mapped

app_config = AppConfig(
    (900, 600),
    False,
    30
)

# app = Application(app_config)
# app.init()
# app.title = "PyPong v0.0.1"
# app.main_loop()


class Application(Cmd):
    """Application Command Line"""
    intro = "Welcome to PyPong CLI. Type help for more information."
    file = None
    prompt = ">>> "

    def __init__(self,
                 completekey: str = "tab",
                 stdin: IO[str] | None = None,
                 stdout: IO[str] | None = None) -> None:
        super().__init__(completekey, stdin, stdout)
        self._server = Server(("", 0))
        self._client = AppClient(("", 0))
        self._addr = ("127.0.0.1", 2000)

    @mapped
    def do_sethost(self, host: str, port: int):
        """Set host"""
        if not isinstance(port, int):
            print("Port is not an integer")
        self._addr = (host, port)

    def do_runserver(self, arg):
        """Run server. Address is specified in sethost"""
        self._server = Server(self._addr, 2)
        self._server.start_as_thread()

    def do_stopserver(self, arg):
        """Stop running server"""
        if not self._server.running:
            print("Server isn't running yet.")
        self._server.stop_thread()

    def do_connect(self, arg):
        """Run client. Address is specified in sethost"""
        self._client = AppClient(self._addr)
        self._client.start()

    def do_stopclient(self, arg):
        """Stop client"""
        if not self._client.running:
            print("Client isn't running yet.")
        self._client.stop()

    def do_play1(self, arg):
        """Play singleplayer"""
        game = Game(app_config)
        game.main_loop()

    def do_exit(self, arg):
        """Exit from command line"""
        if self._client.running:
            self._client.stop()
        if self._server.running:
            self._server.stop_thread()
        return True


if __name__ == '__main__':
    Application().cmdloop()
