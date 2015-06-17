# -*- coding: utf-8 -*-

import os
import sys
import logging
from datetime import datetime
from . import CliError

logging.VERBOSE = 5
logging.addLevelName(logging.VERBOSE, 'VERBOSE')
logging.Logger.verbose = (lambda inst, msg, *args, **kwargs:
                          inst.log(logging.VERBOSE, msg, *args, **kwargs))

FORMATTER = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')


def init(name, logdir, loglevel):
    if not os.path.exists(logdir):
        try:
            os.makedirs(logdir)
        except OSError:
            raise CliError('unable to create log directory: %s' % err)

    logger = logging.getLogger(name)
    logger.setLevel('VERBOSE') # log level is overloader by each handlers.
    logfile = os.path.abspath(os.path.join(logdir, name))

    # Add file handler.
    filename =  '%s.log' % datetime.now().strftime('%Y%m%d%H%M')
    file_handler = logging.FileHandler(os.path.join(logdir, filename))
    file_handler.setFormatter(FORMATTER)
    file_handler.setLevel('INFO')
    logger.addHandler(file_handler)

    # Add cli handler.
    if loglevel != 'none':
        cli_handler = logging.StreamHandler()
        cli_handler.setFormatter(FORMATTER)
        cli_handler.setLevel(loglevel.upper())
        logger.addHandler(cli_handler)

    setattr(sys.modules[__name__], 'logger', logger)


def log(msg, loglevel, **kwargs):
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
    log(msg,
        'verbose',
        quit=kwargs.get('quit', False),
        return_code=kwargs.get('return_code', 0),
        confidential=kwargs.get('confidential', False))


def debug(msg, **kwargs):
    log(msg,
        'debug',
        quit=kwargs.get('quit', False),
        return_code=kwargs.get('return_code', 0),
        confidential=kwargs.get('confidential', False))


def info(msg, **kwargs):
    log(msg,
        'info',
        quit=kwargs.get('quit', False),
        return_code=kwargs.get('return_code', 0),
        confidential=kwargs.get('confidential', False))


def warn(msg, **kwargs):
    log(msg,
        'warn',
        quit=kwargs.get('quit', False),
        return_code=kwargs.get('return_code', 0),
        confidential=kwargs.get('confidential', False))


def error(msg, **kwargs):
    log(msg,
        'error',
        quit=kwargs.get('quit', False),
        return_code=kwargs.get('return_code', 1),
        confidential=kwargs.get('confidential', False))
