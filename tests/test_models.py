"""Used for testing models.py in health_disease_notification"""
#!/usr/bin/env python

import os
import sys
import doctest
import unittest
import coverage
from datetime import (datetime, timedelta)
from trytond.tests.test_tryton import (test_view, test_depends, install_module,
                                       POOL, DB_NAME, USER,
                                       CONTEXT, test_view, test_depends,
                                       doctest_setup, doctest_teardown)
# from trytond.pool import Pool
import trytond.tests.test_tryton
from trytond.transaction import Transaction
from .test_utils import (create_party, create_health_professional,
                         create_user)
from .database_config import set_up_datebase
from proteus import Model



DIR = os.path.abspath(os.path.normpath(os.path.join(__file__,
                                                    '..', '..', 
                                                    '..', '..',
                                                    '..', 'trytond')))
if os.path.isdir(DIR):
    sys.path.insert(0, os.path.dirname(DIR))

COV = coverage.Coverage()

CONFIG = set_up_datebase(database_name='test_memory')

CONFIG.pool.test = True

class GnuHealthSequencesTestCase(unittest.TestCase):
    """Test class for """

    def test_install(self):
        """Testing if pool works"""

        COV.start()
        model = POOL.get('ir.module.module')
        self.assertTrue(model, type(object))
        COV.stop()
        COV.save()
        COV.html_report()

class HealthDiseaseNotificationTestCase(unittest.TestCase):
    """Test HealthDiseaseNotification module."""

    def setUp(self):
        COV.start()
        pool = POOL
        install_module('health_disease_notification')
        self.user = pool.get('res.user')
        self.account = pool.get('account.account')
        self.company = pool.get('company.company')
        self.party = pool.get('party.party')
        self.acc_type = pool.get('account.account.type')
        self.patient = pool.get('gnuhealth.patient')
        self.notification = pool.get('gnuhealth.disease_notification')
        self.healthprof = pool.get('gnuhealth.healthprofessional')
        COV.stop()
        COV.save()
        COV.html_report()

    def test_views(self):
        """Test views."""
        COV.start()
        test_view('health_disease_notification')
        COV.stop()
        COV.save()
        COV.html_report()

    def test_depends(self):
        """Test depends."""
        COV.start()
        test_depends()
        COV.stop()
        COV.save()
        COV.html_report()

    def test_notification_get_patient_age(self):
        """Tests if get_patient_age returns a value for age"""
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            COV.start()
            party, = self.party.search([('code', '=', 'HEALTH-PERSON-TEST')])

            party_patient, = self.party.search([('code', '=', 'PATIENT-TEST')])

            healthprof, = self.healthprof.create([{'name':party.id, 
                                                   'active':True
                                                  }])

            patient, = self.patient.create([{'name':party_patient.id
                                            }])

            notification = self.notification.create([{'date_notified':datetime.now(),
                                                      'name':'Code',
                                                      'patient':patient.id,
                                                      'status':'waiting',
                                                      'healthprof':healthprof.id}])

            self.assertFalse(notification[0].get_patient_age is None)
            COV.stop()
            COV.save()
            COV.html_report()

    def test_notification_age_not_none(self):
        """Tests if get_patient_age returns a value for age"""

        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            COV.start()
            party, = self.party.search([('code', '=', 'HEALTH-PERSON-TEST')])

            party_patient, = self.party.search([('code', '=', 'PATIENT-TEST')])

            healthprof, = self.healthprof.create([{'name':party.id, 
                                                   'active':True
                                                  }])

            patient, = self.patient.create([{'name':party_patient.id
                                            }])

            notification, = self.notification.create([{'date_notified':datetime.now(),
                                                       'name':'Code',
                                                       'patient':patient.id,
                                                       'status':'waiting',
                                                       'healthprof':healthprof.id}])

            age = notification.get_patient_age([notification.id], party_patient.lastname)

            self.assertFalse(age is None)
            COV.stop()
            COV.save()
            COV.html_report()

    def test_notification_age_none(self):
        """Tests if get_patient_age returns a value for age"""

        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            COV.start()
            party, = self.party.search([('code', '=', 'HEALTH-PERSON-TEST')])

            party_patient, = self.party.search([('code', '=', 'PATIENT-TEST')])

            healthprof, = self.healthprof.create([{'name':party, 
                                                   'active':True
                                                  }])

            patient, = self.patient.create([{'name':party_patient
                                            }])

            notification, = self.notification.create([{'date_notified':datetime.now(),
                                                       'name':'Code',
                                                       'patient':patient,
                                                       'status':'waiting',
                                                       'healthprof':healthprof}])

            age = notification.get_patient_age([notification], party_patient.lastname)
            # import pdb; pdb.set_trace()
            for value in age.values():
                self.assertFalse(value is not None)
            COV.stop()
            COV.save()
            COV.html_report()

class NotificationStateChangeTestCase(unittest.TestCase):
    """docstring for NotificationStateChangeTest"unittest.TestCase"""

    def setUp(self):
        pool = POOL
        self.party = pool.get('party.party')
        self.account = pool.get('account.account')
        self.patient = pool.get('gnuhealth.patient')
        self.notification = pool.get('gnuhealth.disease_notification')
        self.healthprof = pool.get('gnuhealth.healthprofessional')
        self.notification_state = pool.get('gnuhealth.disease_notification.statechange')

    def test_default_change_date_now(self):
        """
           Test to make sure default_date in 
           gnuhealth.disease_notification.statechange
           is always the current date
        """
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            COV.start()
            party, = self.party.search([('code', '=', 'HEALTH-PERSON-TEST')])

            party_patient, = self.party.search([('code', '=', 'PATIENT-TEST')])

            healthprof, = self.healthprof.create([{'name':party, 
                                                   'active':True
                                                  }])

            patient, = self.patient.create([{'name':party_patient}])

            notification, = self.notification.create([{'date_notified':datetime.now(),
                                                       'name':'Code',
                                                       'patient':patient,
                                                       'status':'waiting',
                                                       'healthprof':healthprof}])

            change_date = str(self.notification_state.create([{'orig_state':'waiting',
                                                               'target_state':'suspected',
                                                               'notification':notification
                                                              }])[0].change_date)
            now = str(datetime.now())

            cd_deltas = change_date.split(' ')
            cd_deltas[1] = cd_deltas[1].split('.')[0]
            nd_deltas = now.split(' ')
            nd_deltas[1] = nd_deltas[1].split('.')[0]

            for (cd_delta, nd_delta) in zip(cd_deltas, nd_deltas):
                self.assertEqual(cd_delta, nd_delta)
            COV.stop()
            COV.save()
            COV.html_report()

    def test_default_change_date_less(self):
        """
           Test to make sure gnuhealth.disease_notification.statechange
           change_date is never passed the current time
        """
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            COV.start()
            party, = self.party.search([('code', '=', 'HEALTH-PERSON-TEST')])

            party_patient, = self.party.search([('code', '=', 'PATIENT-TEST')])

            healthprof, = self.healthprof.create([{'name':party, 
                                                   'active':True
                                                  }])

            patient, = self.patient.create([{'name':party_patient}])

            notification, = self.notification.create([{'date_notified':datetime.now(),
                                                       'name':'Code',
                                                       'patient':patient,
                                                       'status':'waiting',
                                                       'healthprof':healthprof}])
            notification_state, = self.notification_state.create(
                [{'notification': notification,
                  'healthprof': healthprof,
                  'target_state':'waiting'
                 }])
            self.assertFalse(notification_state.change_date > 
                             datetime.now() + timedelta(seconds=1))
            COV.stop()
            COV.save()
            COV.html_report()

    def test_default_change_date_great(self):
        """
           Test to make sure gnuhealth.disease_notification.statechange
           change_date is never passed the current time
        """
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            COV.start()
            party, = self.party.search([('code', '=', 'HEALTH-PERSON-TEST')])

            party_patient, = self.party.search([('code', '=', 'PATIENT-TEST')])

            healthprof, = self.healthprof.create([{'name':party, 
                                                   'active':True
                                                  }])

            patient, = self.patient.create([{'name':party_patient}])

            notification, = self.notification.create([{'date_notified':datetime.now(),
                                                       'name':'Code',
                                                       'patient':patient,
                                                       'status':'waiting',
                                                       'healthprof':healthprof}])
            notification_state, = self.notification_state.create(
                [{'notification': notification,
                  'healthprof': healthprof,
                  'target_state':'waiting'
                 }])
            self.assertFalse(notification_state.change_date < 
                             datetime.now() + timedelta(seconds=-1))
            COV.stop()
            COV.save()
            COV.html_report()

    def test_health_prof_name_is_string(self):
        """
           Testing for string in gnuhealth.disease_notification.statechange
           health professional
        """
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            COV.start()
            party, = self.party.search([('code', '=', 'HEALTH-PERSON-TEST')])

            party_patient, = self.party.search([('code', '=', 'PATIENT-TEST')])

            healthprof, = self.healthprof.create([{'name':party, 
                                                   'active':True
                                                  }])

            patient, = self.patient.create([{'name':party_patient}])

            notification, = self.notification.create([{'date_notified':datetime.now(),
                                                       'name':'Code',
                                                       'patient':patient,
                                                       'status':'waiting',
                                                       'healthprof':healthprof}])
            notification_state, = self.notification_state.create(
                [{'notification': notification,
                  'healthprof': healthprof,
                  'target_state':'waiting'
                 }])
            self.assertTrue(notification_state.healthprof.name.name, type(str))
            COV.stop()
            COV.save()
            COV.html_report()


def suite():
    """Adding test cases to suite of tests in tryton"""

    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        HealthDiseaseNotificationTestCase))

    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        NotificationStateChangeTestCase))
    
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        GnuHealthSequencesTestCase))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
