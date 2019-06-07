#!/usr/bin/env python
# coding=utf-8
from __future__ import unicode_literals

__author__ = "Ondřej Dušek"
__date__ = "2012"

import sys
import codecs
import logging


LOG_NAME = 'PyTreex'
LOGFORMAT = '%(asctime)-15s %(message)s'

logger = logging.getLogger(LOG_NAME)
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(logging.Formatter(LOGFORMAT))
logger.addHandler(handler)


def log_info(message):
    "Print an information message"
    logging.getLogger(LOG_NAME).info('PYTREEX-INFO: ' + message)


def log_warn(message):
    "Print a warning message"
    logging.getLogger(LOG_NAME).warn('PYTREEX-WARN: ' + message)

def log_fatal(message, exc=Exception()):
    "Print a fatal error message, then raise exception"
    logging.getLogger(LOG_NAME).warn('PYTREEX-FATAL: ' + message)
    raise exc
