"""Threading utility"""
# pylint: disable=unused-argument,too-many-arguments
from threading import Thread as BaseThread
from sys import settrace
from typing import Any, Callable, Iterable, Mapping


class Thread(BaseThread):
    """Extended thread, hopefully it can kill the thread."""

    def __init__(self,
                 group: None = None,
                 target: Callable[..., object] | None = None,
                 name: str | None = None,
                 args: Iterable[Any] | None = None,
                 kwargs: Mapping[str, Any] | None = None,
                 *,
                 daemon: bool | None = None) -> None:
        super().__init__(group, target, name, () if not args else args,
                         {} if not kwargs else kwargs, daemon=daemon)
        self._killed = False
        self._run_backup = lambda: None

    def start(self) -> None:
        """Start thread"""
        self._run_backup = self.run
        self.run = self._run
        return super().start()

    def _run(self):
        settrace(self._globaltrace)
        self._run_backup()

    def _globaltrace(self, frame, event, arg):
        if event == "call":
            return self._localtrace
        return None

    def _localtrace(self, frame, event, arg):
        if self._killed:
            if event == "line":
                raise SystemExit()
        return self._localtrace

    def kill(self):
        """Kill thread"""
        self._killed = True
