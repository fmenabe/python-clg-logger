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

def init(args, colors=None, **kwargs):
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
    logdir_per_exec = args._get('logdir_per_exec', None) or kwargs.pop('logdir_per_exec', False)
    logdir_level = ((args._get('logdir_level', None) or kwargs.pop('logdir_level', LOGLEVEL))
                    .upper())
    logdir_format = args._get('logdir_format', None) or kwargs.pop('logdir_format', LOGFORMAT)

    # Get commands
    commands = [value for (arg, value) in sorted(args) if arg.startswith('command')]

    # Initialize logger
    logger = logging.getLogger('-'.join(commands))
    logger.setLevel(1) # log level is overloaded by each handlers.

    # Console handler
    cli_handler = logging.StreamHandler()
    if isinstance(colors, dict):
        import coloredlogs
        cli_handler.setFormatter(coloredlogs.ColoredFormatter(logformat, **colors))
    else:
        cli_handler.setFormatter(logging.Formatter(logformat))
    cli_handler.setLevel(loglevel.upper())
    logger.addHandler(cli_handler)

    # File handler
    if logfile is not None:
        file_handler = handlers.WatchedFileHandler(logfile)
        file_handler.setFormatter(logging.Formatter(logfile_format))
        file_handler.setLevel(logfile_level)
        logger.addHandler(file_handler)

    # Per command handler
    if logdir is not None:
        if not commands:
            import clg
            clg.cmd.parser.error(
                "program has no subcommands and can't use clg-logger logdir configuration!")

        if logdir_per_exec:
            dirpath = os.path.join(logdir, *commands)
            filepath = os.path.join(dirpath, '%s.log' % datetime.now().strftime('%Y%m%d%H%M'))
        else:
            dirpath = os.path.join(logdir, *commands[:-1])
            filepath = os.path.join(dirpath, '%s.log' % commands[-1])

        # If directory for storing logs does not exists, create it with group permissions.
        umask = os.umask(0)
        if not os.path.exists(dirpath):
            try:
                os.makedirs(dirpath, mode=0o770)
            except OSError as err:
                raise IOError('unable to create log directory: %s' % err)
        os.umask(umask)

        cmd_handler = handlers.WatchedFileHandler(filepath)
        cmd_handler.setFormatter(logging.Formatter(logdir_format))
        cmd_handler.setLevel(logdir_level)
        logger.addHandler(cmd_handler)

    setattr(sys.modules[__name__], 'logger', logger)

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
    if confidential:
        handlers_loglevel = {}
        for handler in logger.handlers[1:]:
            handlers_loglevel[handler] = handler.level
            handler.setLevel('NONE')
        getattr(logger, loglevel)(msg)
        for handler, level in handlers_loglevel.items():
            handler.setLevel(level)
    else:
        getattr(logger, loglevel)(msg)

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

def error(msg, **kwargs):
    """Error messages."""
    log(msg, 'error', **kwargs)

def exception(msg, **kwargs):
    """Exception messages."""
    log(msg, 'exception', **kwargs)
