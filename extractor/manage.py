#!/usr/bin/python2
# -*- coding: utf-8 -*-
import logging
import logging.config

from exposm.settings import settings
# setup logging, has to be after osmext.settings
logging.config.dictConfig(settings.get('logging'))
LOG = logging.getLogger(__file__)

from POSMmanagement.db import DBManagement
from POSMmanagement.settings import POSMSettings


if __name__ == '__main__':
    proj_settings = POSMSettings('settings.yaml')
    # proj_settings.updateDB('host', 'localhost')
    # proj_settings.writeSettings()
    db_man = DBManagement(proj_settings.db_params)
    db_man.dropDatabase()
    db_man.createDatabase()
