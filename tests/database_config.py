"""Defines database configuration for testing"""
from trytond.modules.health_jamaica.tryton_utils import test_database_config


def set_up_datebase(config_file=None, institution_name=None, database_name=None):
    """Set up the testing databae"""
    return test_database_config(config_file, institution_name, database_name=database_name)
