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
from POSMmanagement.osmdata import OSMmanagement


if __name__ == '__main__':
    # proj_settings = POSMSettings('settings.yaml')
    # proj_settings.updateDB('host', 'localhost')
    # proj_settings.writeSettings()
    # db_man = DBManagement(proj_settings.db_params)
    # db_man.dropDatabase()
    # db_man.createDatabase()
    osm_man = OSMmanagement()
    # osm_man.downloadOSM()
    # osm_man.convertOSMtoO5M()
    osm_man.updateOSM('./poly_files/croatia.poly')
    osm_man.extractAdminLevels()
    osm_man.convertO5MtoPBF('admin_levels')
