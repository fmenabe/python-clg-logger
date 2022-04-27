# coding: utf-8

"""
Create a logger with multiple handlers based on CLI arguments or initialisation
parameters.

By default a console handler is set that can be disabled using the *none*
loglevel. Others options/parameters allows to defined a handler logging to
a given file or a handler that will log to a file based on the command used.
"""

import os
import sys
import logging
import logging.handlers as handlers
from datetime import datetime

# Add a VERBOSE level before DEBUG.
logging.VERBOSE = 5
logging.addLevelName(logging.VERBOSE, 'VERBOSE')
logging.Logger.verbose = (lambda inst, msg, *args, **kwargs:
                          inst.log(logging.VERBOSE, msg, *args, **kwargs))

# Add a OK level between WARNING and ERROR
logging.OK = 35
logging.addLevelName(logging.OK, 'OK')
logging.Logger.ok = (lambda inst, msg, *args, **kwargs:
                        inst.log(logging.OK, msg, *args, **kwargs))

# Dummy log level for disabling logging (ie: logger.none should never be used)
logging.NONE = 99
logging.addLevelName(logging.NONE, 'NONE')
logging.Logger.none = (lambda inst, msg, *args, **kwargs:
                       inst.log(logging.NONE, msg, *args, **kwargs))

# For having the real caller (ie: the calling module instead of this module) for
# some formatter parameters (pathname, filename and lineno), we need to set
# logging._srcfile, which is used in logging.findCaller function, to the path
# of this module. We use inspect.getfile as __file__ in python 2.7 return the
# pyc file instead of the py file!
import inspect
logging._srcfile = os.path.normcase(inspect.getfile(inspect.currentframe()))

# Default log level and format.
LOGLEVEL = 'info'
LOGFORMAT = '%(asctime)s %(levelname)s: %(message)s'

def init(args, **kwargs):
    """Initialize logger from CLI arguments (``args``) or this function parameters
    (``kwargs``). Arguments from the CLI have precedence.

    Available options/parameters:

    * ``loglevel``: Log level for the CLI handler (use *none* to disable logging).
    * ``logformat``: Log format for the CLI handler.
    * ``logfile``: If defined, a `WatchedFileHandler` handler for the given path will be set.
    * ``logfile_level``: Log level when a file is defined.
    * ``logfile_format``: Log level when a file is defined
    * ``logdir``: Each command will have logs in this directory
    * ``logdir_per_exec``: Use one log file by execution instead of a global file per command
    * ``logdir_level``: Log level for log files.
    * ``logdir_format``: Log format for log files.
    """
    # Get parameters from args (clg Namespace) and kwargs
    loglevel = (args._get('loglevel', None) or kwargs.pop('loglevel', LOGLEVEL)).upper()
    logformat = args._get('logformat', None) or kwargs.pop('logformat', LOGFORMAT)
    logfile = args._get('logfile', None) or kwargs.pop('logfile', None)
    logfile_level = ((args._get('logfile_level', None) or kwargs.pop('logfile_level', LOGLEVEL))
                     .upper())
    logfile_format = args._get('logfile_format', None) or kwargs.pop('logfile_format', LOGFORMAT)
    logdir = args._get('logdir', None) or kwargs.pop('logdir', None)
    logfile_per_exec = args._get('logdir_per_exec', None) or kwargs.pop('logdir_per_exec', False)
    colors = kwargs.pop('colors', None)

    # Get commands
    subcommands = [value for (arg, value) in sorted(args) if arg.startswith('command')]

    # Initialize logger
    loggers = list(getLoggers(kwargs.pop('loggers', []), subcommands))
    setattr(sys.modules[__name__], 'LOGGERS', kwargs.pop('loggers', []))

    init_loggers()
    add_cli_handler(loglevel, logformat, colors)
    if logfile is not None:
        add_file_handler(logfile_level, logfile, logfile_format)
    if logdir is not None:
        add_cmd_handler(subcommands, logdir, logfile_level, logfile_format, logfile_per_exec)

def getLoggers(loggers, subcommands):
    yield logging.getLogger('-'.join(subcommands))

    for l in loggers:
        yield logger.getLogger(l)

def set_loglevel(loglevel):
    for l in LOGGERS:
        for h in l.handlers:
            h.setLevel(l)

def init_loggers():
    set_loglevel(1)

def add_handler(handler):
    for l in LOGGERS:
        l.addHandler(handler)

def add_cli_handler(loglevel, logformat, colors):
    h = logging.StreamHandler()
    if colors is not None:
        import coloredlogs
        f = coloredlogs.ColoredFormatter(logformat, **colors)
    else:
        f = logging.Formatter(logformat)
    h.setFormatter(f)
    h.setLevel(loglevel.upper())
    add_handler(h)

def add_file_handler(loglevel, logfile, logformat):
    h = handlers.WatchedFileHandler(logfile)
    h.setFormatter(logging.Formatter(logformat))
    h.setLevel(loglevel)
    add_handler(h)

def add_cmd_handler(subcommands, logdir, loglevel, logformat, per_exec):
    if not per_exec and not subcommands:
        import clg
        clg.cmd.parser.error(
            "program has no subcommands and can't use clg-logger logdir configuration!")

    if per_exec:
        dirpath = os.path.join(logdir, *subcommands)
        filepath = os.path.join(dirpath, '%s.log' % datetime.now().strftime('%Y%m%d%H%M'))
    else:
        dirpath = os.path.join(logdir, *subcommands[:-1])
        filepath = os.path.join(dirpath, '%s.log' % subcommands[-1])

    # If directory for storing logs does not exists, create it with group permissions.
    umask = os.umask(0)
    if not os.path.exists(dirpath):
        try:
            os.makedirs(dirpath, mode=0o770)
        except OSError as err:
            raise IOError('unable to create log directory: %s' % err)
    os.umask(umask)

    h = handlers.WatchedFileHandler(filepath)
    h.setFormatter(logging.Formatter(logformat))
    h.setLevel(loglevel)
    add_handler(h)

def dispatch(loglevel, msg):
    for l in LOGGERS:
        getattr(l)(loglevel)(msg)

def log(msg, loglevel, **kwargs):
    """Log ``msg`` message with ``loglevel`` verbosity.

    `**kwargs` can contains:

        * *quit*: force exit of the program,
        * *return_code*: return_code to use in case of exit,
        * *confidential*: don't log on the file logger (allows to log password
          on console)
    """
    quit = kwargs.get('quit', False)
    return_code = kwargs.get('return_code', 0)
    confidential = kwargs.get('confidential', False)
    stack = kwargs.get('stack', False)
    if confidential:
        cur_loglevel = _loggers[0].handlers[0].level
        set_loglevel(logging.NONE)
        dispatch(loglevel, msg)
        set_loglevel(cur_loglevel)
    else:
        dispatch(loglevel, msg)

    if stack:
        import traceback
        traceback.print_exc()

    if quit:
        sys.exit(return_code)

def verbose(msg, **kwargs):
    """Verbose messages."""
    log(msg, 'verbose', **kwargs)

def debug(msg, **kwargs):
    """Debug messages."""
    log(msg, 'debug', **kwargs)

def info(msg, **kwargs):
    """Info messages."""
    log(msg, 'info', **kwargs)

def warn(msg, **kwargs):
    """Warning messages."""
    log(msg, 'warn', **kwargs)

def ok(msg, **kwargs):
    """Warning messages."""
    log(msg, 'ok', **kwargs)

def error(msg, **kwargs):
    """Error messages."""
    log(msg, 'error', **kwargs)

def critical(msg, **kwargs):
    """Error messages."""
    log(msg, 'critical', **kwargs)

def exception(msg, **kwargs):
    """Exception messages."""
    log(msg, 'exception', **kwargs)
