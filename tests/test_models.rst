=====================================

Health Disease Notification Scenario

=====================================


=====================================

General Setup

=====================================


Imports::

    >>> from random import randrange

    >>> from datetime import datetime, timedelta

    >>> from dateutil.relativedelta import relativedelta

    >>> from decimal import Decimal

    >>> from proteus import config, Model, Wizard

    >>> from trytond.modules.health_disease_notification.tests.database_config import set_up_datebase



Create database::



    >>> CONFIG = set_up_datebase()

    >>> CONFIG.pool.test = True



Install health_disease_notification, health_disease_notification_history::



    >>> Module = Model.get('ir.module.module')

    >>> modules = Module.find([('name', 'in', [
    ...                         'health_disease_notification', 
    ...                         'health_disease_notification_history'
    ...                       ]),])

    >>> Module.install([x.id for x in modules], CONFIG.context)

    >>> Wizard('ir.module.module.install_upgrade').execute('upgrade')



Create Disease Notification::



    >>> Patient = Model.get('gnuhealth.patient')

    >>> HealthProfessional = Model.get('gnuhealth.healthprofessional')

    >>> Notification = Model.get('gnuhealth.disease_notification')

    >>> Institution = Model.get('gnuhealth.institution')

    >>> institution, = Institution.find([('id', '=', '1')])

    >>> patient, = Patient.find([('id', '=', '1')])

    >>> healthprof, = HealthProfessional.find([('id', '=', '1')])

    >>> Notification = Notification()

    >>> Notification.date_notified = datetime.now()

    >>> Notification.name = ' '.join(['Code', str(datetime.now())])

    >>> Notification.patient = patient

    >>> Notification.status = 'waiting'

    >>> Notification.healthprof = healthprof

    >>> Notification.save()


Reload the context::



    >>> User = Model.get('res.user')

    >>> CONFIG._context = User.get_preferences(True, CONFIG.context)



Create Risk Factor Condition::



    >>> RiskFactor = Model.get('gnuhealth.disease_notification.risk_disease')

    >>> risk_factor_0 = RiskFactor()

    >>> risk_factor_1 = RiskFactor()

    >>> risk_factor_2 = RiskFactor()

    >>> risk_factor_3 = RiskFactor()

    >>> Pathology = Model.get('gnuhealth.pathology')

    >>> pathology = Pathology.find([('id', 'in', ['1', '2', '3', '4'])])

    >>> risk_factor_0.pathology = pathology[0]

    >>> risk_factor_0.notification = Notification

    >>> risk_factor_0.comment = 'Just a few lines of comments'

    >>> risk_factor_0.save()

    >>> risk_factor_1.pathology = pathology[1]

    >>> risk_factor_1.notification = Notification

    >>> risk_factor_1.comment = 'Just a few lines of comments'

    >>> risk_factor_1.save()

    >>> risk_factor_2.pathology = pathology[2]

    >>> risk_factor_2.notification = Notification

    >>> risk_factor_2.comment = 'Just a few lines of comments'

    >>> risk_factor_2.save()

    >>> risk_factor_3.pathology = pathology[3]

    >>> risk_factor_3.notification = Notification

    >>> risk_factor_3.comment = 'Just a few lines of comments'

    >>> risk_factor_3.save()



Put Risk Factor Condition in Disease Notification::


    >>> Notification.risk_factor = [risk_factor_0, risk_factor_1, 
    ...                             risk_factor_2, risk_factor_3]

    >>> Notification.save()



Create Lab Results Types::



    >>> LabResults = Model.get('gnuhealth.disease_notification.labresulttype')

    >>> lab_result = LabResults()

    >>> lab_result.name = 'Result -'.join(['Code', str(datetime.now())])

    >>> Code = 'R-' + str(datetime.now())

    >>> if len(Code) > 20:
    ...     Code = ''.join([Code[0:20]])

    >>> lab_result.code = Code

    >>> lab_result.save()



Create Notified Specimen::



    >>> NotifiedSpecimen = Model.get('gnuhealth.disease_notification.specimen')

    >>> Code = ''.join([Code[0:5], str(datetime.now())[18:]])

    >>> specimen_0 = NotifiedSpecimen()

    >>> specimen_0.notification = Notification

    >>> specimen_0.name = Code + '0'

    >>> specimen_0.specimen_type = 'urine'

    >>> specimen_0.date_taken = datetime.now()

    >>> specimen_0.lab_sent_to = 'Generation A Lab'

    >>> specimen_0.lab_test_type = 'microscopy'

    >>> specimen_0.date_tested = datetime.now()

    >>> specimen_0.save()

    >>> specimen_1 = NotifiedSpecimen()

    >>> specimen_1.notification = Notification

    >>> specimen_1.name = Code + '1'

    >>> specimen_1.specimen_type = 'blood'

    >>> specimen_1.date_taken = datetime.now()

    >>> specimen_1.lab_sent_to = 'Generation A Lab'

    >>> specimen_1.lab_test_type = 'microscopy'

    >>> specimen_1.date_tested = datetime.now()

    >>> specimen_1.save()

    >>> specimen_2 = NotifiedSpecimen()

    >>> specimen_2.notification = Notification

    >>> specimen_2.name = Code + '2'

    >>> specimen_2.specimen_type = 'stool'

    >>> specimen_2.date_taken = datetime.now()

    >>> specimen_2.lab_sent_to = 'Generation A Lab'

    >>> specimen_2.lab_test_type = 'other'

    >>> specimen_2.date_tested = datetime.now()

    >>> specimen_2.save()

    >>> specimen_3 = NotifiedSpecimen()

    >>> specimen_3.notification = Notification

    >>> specimen_3.name = Code + '3'

    >>> specimen_3.specimen_type = 'eye swab'

    >>> specimen_3.date_taken = datetime.now()

    >>> specimen_3.lab_sent_to = 'Generation A Lab'

    >>> specimen_3.lab_test_type = 'cs'

    >>> specimen_3.date_tested = datetime.now()

    >>> specimen_3.save()



Put Lab Results in Disease Notification::



    >>> Notification.specimen_taken = True

    >>> len(Notification.specimens) == 4
    True

    >>> Notification.save()



Creating Notification Symptom::



    >>> Symptom = Model.get('gnuhealth.disease_notification.symptom')

    >>> symptom = Symptom()

    >>> symptom.name = Notification

    >>> symptom.pathology, = Pathology.find([('code', '=', 'R00')])

    >>> symptom.date_onset = datetime.now()

    >>> symptom.comment = 'Just some comments'

    >>> symptom.save()

    >>> symptom_1 = Symptom()

    >>> symptom_1.name = Notification

    >>> symptom_1.pathology, = Pathology.find([('code', '=', 'R00.2')])

    >>> symptom_1.date_onset = datetime.now()

    >>> symptom_1.comment = 'Just some comments'

    >>> symptom_1.save()

    >>> len(Notification.symptoms) == 2
    True



Make Symptom a part of Notification::



    >>> Notification.save()

    >>> len(Notification.symptoms) == 2
    True



Create Travel History::



    >>> TravelsHistory = Model.get('gnuhealth.disease_notification.travel')

    >>> travel = TravelsHistory()

    >>> travel.notification = Notification

    >>> Country = Model.get('country.country')

    >>> travel.country, = Country.find([('code', '=', 'DK')])

    >>> Subdiv = Model.get('country.subdivision')

    >>> travel.subdiv, = Subdiv.find([('code', '=', 'DK-81')])

    >>> travel.departure_date = datetime.now() - timedelta(days=-30)

    >>> travel.arrival_date = datetime.now() - timedelta(days=-40)

    >>> travel.comment = 'Spent quite a bit of time near epidemic'

    >>> travel.save()

    >>> travel_1 = TravelsHistory()

    >>> travel_1.notification = Notification

    >>> Country = Model.get('country.country')

    >>> travel_1.country, = Country.find([('code', '=', 'DK')])

    >>> Subdiv = Model.get('country.subdivision')

    >>> travel_1.subdiv, = Subdiv.find([('code', '=', 'DK-81')])

    >>> travel_1.departure_date = datetime.now() - timedelta(days=-40)

    >>> travel_1.arrival_date = datetime.now() - timedelta(days=-60)

    >>> travel_1.comment = 'Spent quite a bit of time near epidemic'

    >>> travel_1.save()

    >>> len(Notification.hx_locations) == 2
    True



Notification Travel History::



    >>> Notification.hx_travel = True

    >>> Notification.save()

    >>> len(Notification.hx_locations) == 2
    True



Create Appointment::



    >>> Appointment = Model.get('gnuhealth.appointment')

    >>> appointment = Appointment()

    >>> appointment.patient = patient

    >>> appointment.type = 'ambulatory'

    >>> Specialty = Model.get('gnuhealth.specialty')

    >>> specialty, = Specialty.find([('code', '=', 'BIOCHEM')])

    >>> appointment.speciality = specialty

    >>> appointment.save()



Create Encounter::



    >>> appointment.state
    u'confirmed'

    >>> appointment.click('client_arrived')

    >>> appointment.state
    u'arrived'

    >>> encounter_num = appointment.click('start_encounter')

    >>> Encounter = Model.get('gnuhealth.encounter')

    >>> encounter = Encounter()

    >>> encounter.appointment = appointment

    >>> encounter.patient = appointment.patient

    >>> encounter.start_time = datetime.now()

    >>> encounter.save()

    >>> Encounter_Component = Model.get('gnuhealth.encounter.component')

    >>> Encounter_Ambulatory = Model.get('gnuhealth.encounter.ambulatory')

    >>> #dir(Encounter_Component)

    >>> component = Encounter_Ambulatory()

    >>> component.systolic = 180

    >>> component.diastolic = 88

    >>> component.encounter = encounter

    >>> component.save()

    >>> component.sign_time = datetime.now()

    >>> encounter.save()

    >>> #component.click('sign_x')

    >>> #encounter.click('sign_finish')

    >>> #Notification.encounter = encounter

    >>> Notification.save()

    >>> appointment.save()

    >>> len(appointment.state_changes) == 2
    True

    >>> appointment.state_changes[0].target_state
    u'processing'



Test Depends::



    >>> Notification.reporting_facility_other

    >>> Notification.reporting_facility = institution

    >>> Notification.reporting_facility_other
    ''

    >>> Notification.diagnosis_confirmed = risk_factor_0

    >>> Notification.status
    u'waiting'

    >>> Notification.status = 'confirmed'

    >>> Notification.save()

    >>> Notification.status
    u'confirmed'

