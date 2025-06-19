# ~/clientfactory/src/clientfactory/logs.py
from __future__ import annotations
import os, sys, inspect, logging, typing as t
from logging import StreamHandler, FileHandler, Formatter
from pathlib import Path
from dataclasses import dataclass, field, asdict
from colorama import Fore, Style, init



init(autoreset=True) # initialize colorama, auto-reset colors after each print

class FMT(Formatter):
    COLORS = {
        "DEBUG": Fore.CYAN,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.MAGENTA

    }

    def _resolveclassname(self, outer, funcname: str) -> str:
        classname = ""
        if ("self" in outer.frame.f_locals):
            return f"{outer.frame.f_locals['self'].__class__.__name__}."
        elif ("cls" in outer.frame.f_locals):
            return f"{outer.frame.f_locals['cls'].__class__.__name__}."
        else:
            try:
                qualname = outer.frame.f_globals[funcname].__qualname__
                if ('.' in qualname):
                    return f"{qualname.split('.')[-2]}."
            except Exception as e:
                pass
        return classname

    def format(self, record) -> str:

        # retrieve caller details
        frame = inspect.currentframe()
        outerframes = inspect.getouterframes(frame)

        # frame index to capture original caller
        frameidx = min(8, (len(outerframes) - 1))
        outer = outerframes[frameidx]
        funcname = outer.function

        classname = self._resolveclassname(outer, funcname)

        color = self.COLORS.get(record.levelname, Fore.WHITE)

        caller = f"{classname}{funcname}".ljust(21)
        level = record.levelname.ljust(min(8, len(record.levelname)))
        coloredlevel = f"{color}{level}{Style.RESET_ALL}"

        msg = f"{caller} | {coloredlevel} | {record.getMessage()}"

        return msg



class CFLogger(logging.Logger):
    def __init__(self, name: str, level: logging._Level = logging.NOTSET) -> None:
        super().__init__(name, level)
        self.ENABLED: t.Union[bool, str] = self._checkenv()
        self._logpath: t.Optional[Path] = self.setpath(os.getenv('CFLOGSPATH'))

    def _checkenv(self) -> t.Union[bool, str]:
        val = os.getenv('CFLOGS', '')
        if val.upper() in logging._nameToLevel:
            return val.upper()
        elif val.lower() in ('1', 'true', 'yes', 'y', 'on'):
            return True
        else:
            return False

    def _enabledfor(self, level: int) -> bool:
        if self.ENABLED is True:
            return True
        if self.ENABLED is False:
            return False
        if isinstance(self.ENABLED, str):
            try:
                minlevel = logging._nameToLevel[self.ENABLED.upper()]
                return level >= minlevel
            except KeyError:
                return False
        return False

    def _log(self, level: int, msg: object, args: logging._ArgsType, exc_info: logging._ExcInfoType | None = None, extra: t.Mapping[str, object] | None = None, stack_info: bool = False, stacklevel: int = 1) -> None:
        if not self._enabledfor(level):
            return
        return super()._log(level, msg, args, exc_info, extra, stack_info, stacklevel)

    def setpath(
        self,
        path: t.Optional[t.Union[str, Path]],
        level: t.Optional[int] = None,
        formatter: t.Optional[logging.Formatter] = None
    ) -> None:
        if not path:
            return

        path = Path(path).expanduser().resolve()

        # If it's a directory, append a default filename
        if path.is_dir() or str(path).endswith("/"):
            path = path / f"{self.name}.log"

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        self._logpath = path
        level = level if level is not None else self.level
        formatter = formatter if formatter is not None else FMT()

        # Remove existing file handlers
        self.handlers = [h for h in self.handlers if not isinstance(h, FileHandler)]

        fh = FileHandler(path)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        self.addHandler(fh)


    @property
    def logpath(self) -> t.Optional[Path]:
        return self._logpath

logging.setLoggerClass(CFLogger)

def logger(name: str, level: int = logging.DEBUG, console: bool = True, path: t.Optional[str] = None, propagate: bool = False) -> logging.Logger:
    """
    Configures and returns a logger with the specified name.
    This logger can output to console and/or a file with colored formatting.

    Parameters:
      - name (str): Logger name.
      - level (int): Logging level (e.g., logging.DEBUG, logging.INFO).
      - console (bool): Whether to output logs to the console (stdout).
      - path (str): Path to a log file. If None, no file handler is added.
      - propagate (bool): Whether to propagate logs to ancestor loggers.

    Returns:
      - logging.Logger: Configured logger instance.
    """

    log = logging.getLogger(name)
    log.setLevel(level)
    log.propagate = propagate

    log.handlers = [] # clear handlers

    if console:
        consolehandler = StreamHandler(sys.stdout)
        consolehandler.setLevel(level)
        consolehandler.setFormatter(FMT())
        log.addHandler(consolehandler)

    if path:
        filehandler = FileHandler(path)
        filehandler.setLevel(level)
        filehandler.setFormatter(FMT())
        log.addHandler(filehandler)

    return log


log = logger('clientfactory')
