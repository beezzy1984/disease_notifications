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
                                       CONTEXT)
                                      # doctest_setup, doctest_teardown)
import trytond.tests.test_tryton
from trytond.transaction import Transaction
from trytond.exceptions import UserError #, UserWarning
# from trytond.pool import Pool
from psycopg2 import ProgrammingError
# from .test_utils import (create_party, create_health_professional,
#                          create_user)
from .database_config import set_up_datebase

# from proteus import Model



DIR = os.path.abspath(os.path.normpath(os.path.join(__file__,
                                                    '..', '..', 
                                                    '..', '..',
                                                    '..', 'trytond')))
if os.path.isdir(DIR):
    sys.path.insert(0, os.path.dirname(DIR))

COV = coverage.Coverage()

CONFIG = set_up_datebase(database_name='test_memory')

CONFIG.pool.test = True

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
        self.pathology = pool.get('gnuhealth.pathology')
        self.notification = pool.get('gnuhealth.disease_notification')
        self.healthprof = pool.get('gnuhealth.healthprofessional')
        self.symptom = pool.get('gnuhealth.disease_notification.symptom')
        self.encounter = pool.get('gnuhealth.encounter')
        self.specimens = pool.get('gnuhealth.disease_notification.specimen')
        self.hospital = pool.get('gnuhealth.institution')
        self.risk_factors = pool.get('gnuhealth.disease_notification.risk_disease')
        self.hx_locations = pool.get('gnuhealth.disease_notification.travel')
        self.state_changes = pool.get('gnuhealth.disease_notification.statechange')
        self.appointment = pool.get('gnuhealth.appointment')
        self.specialty = pool.get('gnuhealth.specialty')
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
            
            healthprof, = self.healthprof.search([('id', '=', '1')])

            patient, = self.patient.search([('id', '=', '1')])

            notification, = self.notification.create([{'date_notified':datetime.now(),
                                                       'name':'Code',
                                                       'patient':patient.id,
                                                       'status':'waiting',
                                                       'healthprof':healthprof.id}])

            self.assertFalse(notification.get_patient_age is None)
            COV.stop()
            COV.save()
            COV.html_report()

    def test_new_notification_is_active(self):
        """Tests if an new notification is always active"""
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            COV.start()
            
            healthprof, = self.healthprof.search([('id', '=', '1')])

            patient, = self.patient.search([('id', '=', '1')])

            notification, = self.notification.create([{'date_notified':datetime.now(),
                                                       'name':'Code',
                                                       'patient':patient.id,
                                                       'status':'waiting',
                                                       'healthprof':healthprof.id}])

            self.assertEqual(notification.active, True)
            COV.stop()
            COV.save()
            COV.html_report()

    def test_after_state_changed_notification_is_active(self):
        """Tests if after state has been changed notification.active=True"""
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            COV.start()
            
            healthprof, = self.healthprof.search([('id', '=', '1')])

            patient, = self.patient.search([('id', '=', '1')])

            notification, = self.notification.create([{'date_notified':datetime.now(),
                                                       'name':'Code',
                                                       'patient':patient.id,
                                                       'status':'waiting',
                                                       'healthprof':healthprof.id}])

            notification.state = 'suspected'

            self.assertEqual(notification.active, True)
            COV.stop()
            COV.save()
            COV.html_report()

    def test_notification_age_not_none(self):
        """Tests if get_patient_age returns a value for age"""

        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            COV.start()
            
            healthprof, = self.healthprof.search([('id', '=', '1')])

            patient, = self.patient.search([('id', '=', '1')])

            party_patient, = self.party.search([('code', '=', 'PATIENT-TEST')])

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
            
            healthprof, = self.healthprof.search([('id', '=', '1')])
            party_patient, = self.party.search([('code', '=', 'PATIENT-TEST')])
            patient, = self.patient.search([('id', '=', '1')])

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

    def test_patient_is_required(self):
        """
           Tests to make sure patient always has to be attached to a 
           new disease notification
        """

        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            COV.start()
            
            healthprof, = self.healthprof.search([('id', '=', '1')])

            try:
                self.notification.create(
                    [{'date_notified':datetime.now(),
                      'name':'Code',
                      'status':'waiting',
                      'healthprof':healthprof}])
            except UserError:
                pass
            else:
                msg = 'Did not see UserError for patient required in notification'
                self.fail(msg)
            COV.stop()
            COV.save()
            COV.html_report()

    def test_health_prof_is_required(self):
        """
           Tests to make sure health professional always has to be attached to a 
           new disease notification
        """

        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            COV.start()

            patient, = self.patient.search([('id', '=', '1')])

            try:
                self.notification.create(
                    [{'date_notified':datetime.now(),
                      'name':'Code',
                      'patient':patient,
                      'status':'waiting'}])
            except KeyError:
                pass
            except UserError:
                pass
            else:
                msg = ['Did not see UserError or KeyError for health', 
                       'professional required in notification']

                self.fail(' '.join(msg))
            COV.stop()
            COV.save()
            COV.html_report()

    def test_status_is_required(self):
        """
           Tests to make sure a status always has to be attached to a 
           new disease notification
        """

        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            COV.start()

            healthprof, = self.healthprof.search([('id', '=', '1')])

            patient, = self.patient.search([('id', '=', '1')])

            try:
                self.notification.create(
                    [{'date_notified':datetime.now(),
                      'name':'Code',
                      'patient':patient,
                      'healthprof': healthprof}])
            except KeyError:
                pass
            except UserError:
                pass
            else:
                msg = ['Did not see UserError or KeyError for status', 
                       'required in notification']
                self.fail(' '.join(msg))
            COV.stop()
            COV.save()
            COV.html_report()

    def test_date_notified_is_required(self):
        """
           Tests to make sure a date_notified always has to be attached to a 
           new disease notification
        """

        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            COV.start()
            healthprof, = self.healthprof.search([('id', '=', '1')])

            patient, = self.patient.search([('id', '=', '1')])

            try:
                self.notification.create(
                    [{'name':'Code',
                      'patient':patient,
                      'healthprof': healthprof,
                      'status':'waiting'}])
            except KeyError:
                pass
            except UserError:
                pass
            except ProgrammingError:
                pass
            else:
                msg = ['Did not see UserError, KeyError or ProgrammingError for',
                       'status required in notification']
                self.fail(' '.join(msg))
            COV.stop()
            COV.save()
            COV.html_report()

    def test_data_required_notification(self):
        """
           Tests to make sure a data always has to be attached to a 
           new disease notification
        """

        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            COV.start()
            try:
                self.notification.create([{}])
            except KeyError:
                pass
            except UserError:
                pass
            except ProgrammingError:
                pass
            else:
                msg = ['Did not see UserError, KeyError or ProgrammingError for',
                       'status required in notification']
                self.fail(' '.join(msg))
            COV.stop()
            COV.save()
            COV.html_report()

    def test_status_display_is_in_list(self):
        """Tests if value in status_display is in NOTIFICATION_STATES list"""
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            COV.start()

            healthprof, = self.healthprof.search([('id', '=', '1')])

            patient, = self.patient.search([('id', '=', '1')])


            notification, = self.notification.create([{'date_notified':datetime.now(),
                                                       'name':'Code',
                                                       'patient':patient.id,
                                                       'status':'waiting',
                                                       'healthprof':healthprof.id}])

            notification.state = 'suspected'
            from .. models import NOTIFICATION_STATES
            def check_list():
                """
                   Check for notification status_display in 
                   NOTIFICATION_STATES list
                """
                for state in NOTIFICATION_STATES:
                    if notification.status_display in state:
                        return True

                return False

            self.assertTrue(check_list())

            COV.stop()
            COV.save()
            COV.html_report()

    def test_diagnosis_type(self):
        """Tests if notification diagnosis is type gnuhealth.pathology"""
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            COV.start()
            
            healthprof, = self.healthprof.search([('id', '=', '1')])

            patient, = self.patient.search([('id', '=', '1')])


            diagnosis, = self.pathology.search([('code', '=', 'A00')])

            self.assertTrue(self.notification.create([{'date_notified':datetime.now(),
                                                       'name':'Code',
                                                       'patient':patient.id,
                                                       'status':'waiting',
                                                       'healthprof':healthprof.id,
                                                       'diagnosis': diagnosis}]))
            COV.stop()
            COV.save()
            COV.html_report()

    def test_diagnosis_with_wrong_type(self):
        """Tests if notification diagnosis is type gnuhealth.pathology"""
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            COV.start()
            
            healthprof, = self.healthprof.search([('id', '=', '1')])

            patient, = self.patient.search([('id', '=', '1')])

            diagnosis = "self.pathology.search([('code', '=', 'A00')])"

            try:
                self.notification.create(
                    [{'date_notified':datetime.now(),
                      'name':'Code',
                      'patient':patient.id,
                      'status':'waiting',
                      'healthprof':healthprof.id,
                      'diagnosis': diagnosis}])
            except ValueError:
                pass
            except UserError:
                pass
            except ProgrammingError:
                pass
            else: 
                msg = ['Did not see UserError, KeyError or ProgrammingError for',
                       'status required in notification']
                self.fail(' '.join(msg))
            COV.stop()
            COV.save()
            COV.html_report()

    def test_diagnosis_confirmed_type(self):
        """Tests if notification diagnosis_confirmed is type gnuhealth.pathology"""
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            COV.start()
            
            healthprof, = self.healthprof.search([('id', '=', '1')])

            patient, = self.patient.search([('id', '=', '1')])

            diagnosis, = self.pathology.search([('code', '=', 'A00')])

            self.assertTrue(self.notification.create([{'date_notified':datetime.now(),
                                                       'name':'Code',
                                                       'patient':patient.id,
                                                       'status':'waiting',
                                                       'healthprof':healthprof.id,
                                                       'diagnosis_confirmed': diagnosis}]))
            COV.stop()
            COV.save()
            COV.html_report()

    def test_diagnosis_confirmed_with_wrong_type(self):
        """Tests if notification diagnosis_confirmed is type gnuhealth.pathology"""
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            COV.start()
            
            healthprof, = self.healthprof.search([('id', '=', '1')])

            patient, = self.patient.search([('id', '=', '1')])

            diagnosis = "self.pathology.search([('code', '=', 'A00')])"

            try:
                self.notification.create(
                    [{'date_notified':datetime.now(),
                      'name':'Code',
                      'patient':patient.id,
                      'status':'waiting',
                      'healthprof':healthprof.id,
                      'diagnosis_confirmed': diagnosis}])
            except ValueError:
                pass
            except UserError:
                pass
            except ProgrammingError:
                pass
            else: 
                msg = ['Did not see UserError, KeyError or ProgrammingError for',
                       'status required in notification']
                self.fail(' '.join(msg))
            COV.stop()
            COV.save()
            COV.html_report()

    def test_symptoms_with_wrong_type(self):
        """
           Tests if notification symptom is type 
           gnuhealth.disease_notification.symptom
        """
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            COV.start()
            
            healthprof, = self.healthprof.search([('id', '=', '1')])

            patient, = self.patient.search([('id', '=', '1')])

            diagnosis, = self.pathology.search([('code', '=', 'R46')])

            notification, = self.notification.create([{'date_notified':datetime.now(),
                                                       'name':'Code',
                                                       'patient':patient.id,
                                                       'status':'waiting',
                                                       'healthprof':healthprof.id,
                                                       'diagnosis_confirmed': diagnosis}])

            symptom = self.symptom.create([{'pathology':diagnosis.id,
                                            'name': notification.id}])
            try:
                self.notification.create([{'date_notified':datetime.now(),
                                           'name':'Cod',
                                           'patient':patient.id,
                                           'status':'waiting',
                                           'healthprof':healthprof.id,
                                           'diagnosis_confirmed': diagnosis.id,
                                           'symptoms': symptom}])
            except ValueError:
                pass
            except UserError:
                pass
            except KeyError:
                pass
            else:
                msg = ['Did not see UserError, KeyError or ProgrammingError for',
                       'status required in notification']
                self.fail(' '.join(msg))
            COV.stop()
            COV.save()
            COV.html_report()

    def test_symptoms_with_wrong_type(self):
        """
           Tests if notification diagnosis_confirmed is type 
           gnuhealth.disease_notification.symptom
        """
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            COV.start()
            
            healthprof, = self.healthprof.search([('id', '=', '1')])

            patient, = self.patient.search([('id', '=', '1')])

            diagnosis = "self.pathology.search([('code', '=', 'A00')])"

            try:
                self.notification.create(
                    [{'date_notified':datetime.now(),
                      'name':'Code',
                      'patient':patient.id,
                      'status':'waiting',
                      'healthprof':healthprof.id,
                      'diagnosis_confirmed': diagnosis,
                      'symptoms':diagnosis}])
            except ValueError:
                pass
            except UserError:
                pass
            except ProgrammingError:
                pass
            else: 
                msg = ['Did not see UserError, KeyError or ProgrammingError for',
                       'status required in notification']
                self.fail(' '.join(msg))
            COV.stop()
            COV.save()
            COV.html_report()

    def test_encounter_with_wrong_type(self):
        """Tests if notification encounter is type gnuhealth.encounter"""
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            COV.start()

            healthprof, = self.healthprof.search([('id', '=', '1')])

            patient, = self.patient.search([('id', '=', '1')])

            diagnosis = "self.pathology.search([('code', '=', 'A00')])"

            try:
                self.notification.create(
                    [{'date_notified':datetime.now(),
                      'name':'Code',
                      'patient':patient.id,
                      'status':'waiting',
                      'healthprof':healthprof.id,
                      'diagnosis_confirmed': diagnosis,
                      'encounter':diagnosis}])
            except ValueError:
                pass
            except UserError:
                pass
            except ProgrammingError:
                pass
            else: 
                msg = ['Did not see UserError, KeyError or ProgrammingError for',
                       'status required in notification']
                self.fail(' '.join(msg))
            COV.stop()
            COV.save()
            COV.html_report()

class NotificationStateChangeTestCase(unittest.TestCase):
    """docstring for NotificationStateChangeTest"unittest.TestCase"""

    def setUp(self):
        pool = POOL
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
            
            healthprof, = self.healthprof.search([('id', '=', '1')])

            patient, = self.patient.search([('id', '=', '1')])

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
            
            healthprof, = self.healthprof.search([('id', '=', '1')])

            patient, = self.patient.search([('id', '=', '1')])

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
            
            healthprof, = self.healthprof.search([('id', '=', '1')])

            patient, = self.patient.search([('id', '=', '1')])

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
            
            healthprof, = self.healthprof.search([('id', '=', '1')])

            patient, = self.patient.search([('id', '=', '1')])

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

class GnuHealthSequencesTestCase(unittest.TestCase):
    """Test class for """
    def setUp(self):
        pool = POOL
        self.health_sequence = pool.get('gnuhealth.sequences')
        self.notification = pool.get('gnuhealth.disease_notification')

    def test_type(self):
        """Testing if pool works"""
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            COV.start()
            health_sequence, = self.health_sequence.create([{}])
            self.assertTrue(health_sequence, type(self.health_sequence))
            COV.stop()
            COV.save()
            COV.html_report()

    def test_notification_sequence_type(self):
        """
            Testinf to make sure sequence notification type is of
            disease notification object
        """
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            COV.start()
            health_sequence, = self.health_sequence.create([{}])
            self.assertTrue(health_sequence.notification_sequence, 
                            type(self.notification))
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

    suite.addTests(doctest.DocFileSuite('test_models.rst',
                                        setUp=None, tearDown=None, 
                                        encoding='utf-8', 
                                        optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
                                        checker=None))
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
