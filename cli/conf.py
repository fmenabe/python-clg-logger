# -*- coding: utf-8 -*-

import os
import sys
import yaml
import cli.logger as logger
from . import CliError, hooks
from pprint import pformat

_SELF = sys.modules[__name__]


def init(args):
    if 'conf_file' not in args:
        raise CliError('no configuration file')

    try:
        config = yaml.load(open(args.conf_file)) or {}
    except Exception as err:
        raise CliError('unable to read the main configuration file: %s' % err)

    for param, value in config.items():
        setattr(_SELF, param.upper(), replace_paths(value))

    # Init logs.
    commands = [value
                for (arg, value) in sorted(args)
                if arg.startswith('command')]
    logger.init('-'.join(commands),
                os.path.join(args.logdir, *commands),
                args.loglevel)
    load_commands_conf(commands)

    logger.debug('configuration parameters:\n%s' %
                 pformat({attr: getattr(_SELF, attr)
                          for attr in vars(_SELF)
                          if attr.isupper() and not attr.startswith('_')}))

    for hook in hooks:
        hook()
#        setattr(_SELF, hook.__name__, hook)
#        getattr(_SELF, hook.__name__)()


def replace_paths(value):
    return {str: lambda: value.replace('__FILE__', sys.path[0]),
            list: lambda: [replace_paths(elt) for elt in value],
            dict: lambda: {key: replace_paths(val) for key, val in value.items()}
           }.get(type(value), lambda: value)()


def load_commands_conf(commands):
    # Load intermediary configuration files.
    cmd_path = os.path.join(sys.path[0], 'conf')
    for cmd in commands:
        cmd_path = os.path.join(cmd_path, cmd)
        cmd_file = '%s.yml' % cmd_path
        if os.path.exists(cmd_file):
            load_file(cmd_file)

    # Load every file in the directory of the command (if exits).
    if os.path.exists(cmd_path):
        for filename in os.listdir(cmd_path):
            if filename.startswith('.'):
                continue
            filepath = os.path.join(cmd_path, filename)
            if os.path.isfile(filepath):
                load_file(filepath, False)


def load_file(filepath, root=True):
    logger.debug("loading configuration file '%s'" % filepath)
    filename, fileext = os.path.splitext(os.path.basename(filepath))
    try:
        if fileext == '.yml':
            conf = yaml.load(open(filepath))
            if root:
                for attr, value in conf.items():
                    setattr(_SELF, attr.replace('-', '_').upper(), value)
            else:
                setattr(_SELF, filename.upper(), conf)
        else:
            with open(filepath) as fhandler:
                setattr(_SELF, filename.upper(), fhandler.read())
    except Exception as err:
        logger.error("unable to load configuration file '%s': %s"
                      % (filepath, err),
                     quit=True)
