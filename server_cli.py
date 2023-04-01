"""Server CLI"""
# pylint: disable=unused-argument
from cmd import Cmd
from time import sleep
from typing import IO
from packs.server import Server, Logger as ServerLogger, Console
from packs.client import Client


class ServerCLI(Cmd):
    """Server CLI"""
    intro = "Welcome to PyPong Server CLI. Type run to start the server"
    prompt = ">>> "
    file = None

    def __init__(self, completekey: str = "tab",
                 stdin: IO[str] | None = None,
                 stdout: IO[str] | None = None) -> None:
        super().__init__(completekey, stdin, stdout)
        self.server = None
        self._addr = (None, None)
        self._console = False
        self._noadd = True
        ServerLogger.info("ServerCLI has been started.")
        ServerLogger.removeHandler(Console)  # type: ignore
        ServerLogger.info("Console Hanlder has been removed.")

    def do_enable_console(self, arg):
        """Enable console logging"""
        self._console = True
        self._noadd = True
        ServerLogger.addHandler(Console)  # type: ignore

    def do_disable_console(self, arg):
        """Disable console logging"""
        self._console = False
        ServerLogger.removeHandler(Console)  # type: ignore

    def do_no_console(self, arg):
        """Keep disable adding console log after cli ends.
        This removes console log from the session."""
        self.do_disable_console(arg)
        self._noadd = True

    def do_keep_console(self, arg):
        """Keep enable adding console after cli ends.
        This also adds the console log to the session."""
        self.do_enable_console(arg)
        self._noadd = False

    def do_run(self, arg: str):
        """Run the server"""
        try:
            host, port = arg.split(' ', 1)
            int(port)
        except ValueError:
            print("Port is not a number")
            return
        print(f"Server run at {host}:{port}")
        self._addr = (host, int(port))
        self.server = Server(self._addr)
        self.server.start_as_thread()

    def do_runpeer(self, arg: str):
        """Run server as peer"""
        try:
            host, port = arg.split(' ', 1)
            int(port)
        except ValueError:
            print("Port is not a number")
            return
        print(f"Server run at {host}:{port}")
        self._addr = (host, int(port))
        self.server = Server(self._addr, True)
        self.server.start_as_thread()

    def do_runtest(self, arg):
        """Test run"""
        self.do_run("127.0.0.1 2000")
        self.do_test(arg)

    def do_runtest2(self, arg):
        """Test Server connection 2"""
        self._addr = ('127.0.0.1', 2000)
        # self.do_enable_console("")
        self.server = Server(self._addr, True)
        self.server.start_as_thread()
        sleep(1)
        self.do_test("")
        self.server.stop_thread()
        self._addr = (None, None)
        self.server = None
        # self.do_disable_console("")

    def do_test(self, arg: str):
        """Test Server connection"""
        if self._addr == (None, None):
            print("Server was not started.")
            return
        client = Client(self._addr)  # type: ignore
        client.start()
        client.push("Hello, World!")
        print(client.json())
        client.stop()

    def do_stop(self, arg):
        """Stop the server"""
        if not self.server:
            print("Server was not started yet.")
            return
        if self.server.running is False:
            print("Server was stopped.")
            return
        self.server.stop_thread()
        print("Server stopped")

    def do_exit(self, arg):
        """Stop server session"""
        if self.server is None:
            return True
        if self.server.running:
            self.server.stop_thread()
        ServerLogger.info("ServerCLI has exited, attempt to readd console")
        if not self._console and self._noadd is False:
            ServerLogger.addHandler(Console)  # type: ignore
        return True

# server = Server(("127.0.0.1", 2000))

# thread = server.start_as_thread()

# server.stop_thread()

# while server.running:
#     client = socket(AF_INET, SOCK_STREAM)
#     client.connect(("127.0.0.1", 2000))
#     client.send(pack("Hello, World!"))
#     print(unpack(client.recv(1024)))
#     sleep(1)
#     client.send(b"Hello, World")
#     print(unpack(client.recv(1024)))
#     client.close()
#     server.stop_thread()

# thread.join()
#


if __name__ == "__main__":
    ServerCLI().cmdloop()
