# coding: utf-8

"""Create a logger based on command-line arguments.

This logger will log to a file with INFO level and to the console with the
level passed with the 'loglevel' command-line argument. 'logdir' command-line
argument define where logs will be stored.

There's an additionnal parameter indicating whether a log file will be created
per execution.
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

FORMATTER = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')

def init(args):
    logging.VERBOSE = 5
    logging.addLevelName(logging.VERBOSE, 'VERBOSE')
    logging.Logger.verbose = (lambda inst, msg, *args, **kwargs:
                              inst.log(logging.VERBOSE, msg, *args, **kwargs))


    logdir = args['logdir'] or os.path.join(sys.path[0], 'logs')
    loglevel = args['loglevel'] or 'info'
    logfile_per_exec = args['logfile_per_exec'] or False

    # Get log directory and file.
    commands = [value for (arg, value) in sorted(args) if arg.startswith('command')]
    if logfile_per_exec:
        logdir = os.path.join(args.logdir, *commands)
        logfile = os.path.join(logdir, '%s.log' % datetime.now().strftime('%Y%m%d%H%M'))
    else:
        logdir = os.path.join(args.logdir, *commands[:-1])
        logfile = os.path.join(logdir, commands[-1])
    loglevel = args.loglevel or 'info'

    # If directory for storing logs does not exists, create it with group permissions.
    umask = os.umask(0)
    if not os.path.exists(logdir):
        try:
            os.makedirs(logdir, mode=0o770)
        except OSError as err:
            raise IOError('unable to create log directory: %s' % err)

    # Initialize logger;
    logger = logging.getLogger('-'.join(commands))
    logger.setLevel('VERBOSE') # log level is overloaded by each handlers.

    # Add file handler.
    file_handler = handlers.WatchedFileHandler(logfile)
    file_handler.setFormatter(FORMATTER)
    file_handler.setLevel('INFO')
    logger.addHandler(file_handler)
    os.chmod(logfile, 0o770)
    # Add cli handler.
    if loglevel != 'none':
        cli_handler = logging.StreamHandler()
        cli_handler.setFormatter(FORMATTER)
        cli_handler.setLevel(loglevel.upper())
        logger.addHandler(cli_handler)

    os.umask(umask)
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
        logger.handlers[0].setLevel(100)
        getattr(logger, loglevel)(msg)
        logger.handlers[0].setLevel('INFO')
    else:
        getattr(logger, loglevel)(msg)

    if quit:
        sys.exit(return_code)

def verbose(msg, **kwargs):
    """Verbose messages."""
    log(
        msg,
        'verbose',
        quit=kwargs.get('quit', False),
        return_code=kwargs.get('return_code', 0),
        confidential=kwargs.get('confidential', False))

def debug(msg, **kwargs):
    """Debug messages."""
    log(
        msg,
        'debug',
        quit=kwargs.get('quit', False),
        return_code=kwargs.get('return_code', 0),
        confidential=kwargs.get('confidential', False))

def info(msg, **kwargs):
    """Info messages."""
    log(
        msg,
        'info',
        quit=kwargs.get('quit', False),
        return_code=kwargs.get('return_code', 0),
        confidential=kwargs.get('confidential', False))

def warn(msg, **kwargs):
    """Warning messages."""
    log(
        msg,
        'warn',
        quit=kwargs.get('quit', False),
        return_code=kwargs.get('return_code', 0),
        confidential=kwargs.get('confidential', False))

def error(msg, **kwargs):
    """Error message."""
    log(
        msg,
        'error',
        quit=kwargs.get('quit', False),
        return_code=kwargs.get('return_code', 1),
        confidential=kwargs.get('confidential', False))
