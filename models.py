
from trytond.model import ModelView, ModelSQL, fields, ModelSingleton
from trytond.pyson import Eval, In, And, Bool
from trytond.pool import Pool
from trytond.modules.health_jamaica.tryton_utils import (
    get_epi_week, replace_clause_column, epiweek_str
)

import re
from datetime import datetime, date

ONLY_IF_ADMITTED = {'invisible': ~Eval('hospitalized', False)}
ONLY_IF_LAB = {'invisible': ~Eval('specimen_taken', False)}
ONLY_IF_DEAD = {'invisible': ~Eval('deceased', False),
                'required': Eval('deceased', False)}

REQD_IF_LAB = dict([('required', Eval('specimen_taken', False))] +
                   ONLY_IF_LAB.items())
RO_SAVED = {'readonly': Eval('id', 0) > 0}  # readonly after saved
RO_NEW = {'readonly': Eval('id', 0) < 0}  # readonly when new

SEX_OPTIONS = [('m', 'Male'), ('f', 'Female'), ('u', 'Unknown')]
NOTIFICATION_STATES = [
    (None, ''),
    ('waiting', 'Awaiting Classification'),
    ('suspected', 'Suspected'),
    ('confirmed', 'Confirmed'),
    ('epiconfirm', 'Confirmed (epidemiologically linked)'),
    ('discarded', 'Discarded (confirmed negative)'),
    ('notsuspected', 'Not Suspected'),
    ('unclassified', 'Unclassified'),
    ('cannotclassify', 'Cannot Classify'),
    ('delete', 'Duplicate, Discard'),
    ('invalid', 'Invalid (will not classify)')
]
NOTIFICATION_END_STATES = ['discarded', 'delete', 'confirmed', 'epiconfirm',
                           'notsuspected', 'discarded']
RO_STATE_END = {'readonly': In(Eval('status', ''), NOTIFICATION_END_STATES)}
SPECIMEN_TYPES = [
    ('blood', 'Blood'),
    ('urine', 'Urine'),
    ('sputum', 'Sputum'),
    ('csf', 'Cerebrospinal Fluid (CSF)'),
    ('stool', 'Stool'),
    ('throat swab', 'Throat Swab'),
    ('eye swab', 'Eye Swab'),
    ('nasopharyngeal swab', 'Nasopharyngeal Swab'),
    ('rectal swab', 'Rectal Swab'),
    ('blood smear', 'Blood Smear'),
    ('unknown', 'Unknown')]

LAB_RESULT_STATES = [
    (None, ''),
    ('pos', 'Positive'),
    ('neg', 'Negative'),
    ('ind', 'Indeterminate')
]
LAB_TEST_TYPES = [
    (None, ''),
    ('igm', 'IgM'),
    ('igg', 'IgG'),
    ('pcr', 'PCR'),
    ('cs', 'C/S'),
    ('microscopy', 'Microscopy'),
    ('ovacystpara', 'Ova, Cysts & Parasites'),
    ('other', 'Other')
]


class GnuHealthSequences(ModelSingleton, ModelSQL, ModelView):
    'Standard Sequences for GNU Health'
    __name__ = 'gnuhealth.sequences'

    notification_sequence = fields.Property(fields.Many2One(
        'ir.sequence', 'Disease Notification Sequence', required=True,
        domain=[('code', '=', 'gnuhealth.disease_notification')]))


class DiseaseNotification(ModelView, ModelSQL):
    'Disease Notification'

    __name__ = 'gnuhealth.disease_notification'
    active = fields.Boolean('Active')
    patient = fields.Many2One('gnuhealth.patient', 'Patient', required=True,
                              states=RO_SAVED)
    status = fields.Selection(NOTIFICATION_STATES, 'Status', required=True,
                              sort=False)
    status_display = fields.Function(fields.Char('State'),
                                     'get_selection_display')
    name = fields.Char('Code', size=18, states={'readonly': True},
                       required=True)
    tracking_code = fields.Char('Case Tracking Code', select=True)
    date_notified = fields.DateTime('Date reported', required=True,
                                    states=RO_SAVED)
    date_received = fields.DateTime(
        'Date received', states=RO_NEW,
        help='Date received the National Surveillance Unit')
    diagnosis = fields.Many2One('gnuhealth.pathology', 'Suspected Diagnosis',
                                states=RO_STATE_END, required=False)
    diagnosis_confirmed = fields.Many2One(
        'gnuhealth.pathology', 'Confirmed Diagnosis', required=False,
        states={'invisible': Eval('id', 0) < 0})
    symptoms = fields.One2Many('gnuhealth.disease_notification.symptom',
                               'name', 'Symptoms', states=RO_STATE_END)
    date_onset = fields.Date('Date of Onset',
                             help='Date of onset of the illness')
    epi_week_onset = fields.Function(fields.Char('Epi. Week of onset', size=8,
                                     help='Week of onset (epidemiological)'),
                                     'epi_week')
    date_seen = fields.Date('Date Seen', help='Date seen by a medical officer')
    reporting_facility = fields.Many2One(
        'gnuhealth.institution', 'Reporting facility',
        states={'invisible': Bool(Eval('reporting_facility_other'))})
    reporting_facility_other = fields.Char(
        'Other Reporting location',
        help='Used when the report came from an institution not found above',
        states={'invisible': Bool(Eval('reporting_facility'))})
    encounter = fields.Many2One(
        'gnuhealth.encounter', 'Clinical Encounter',
        domain=[('patient', '=', Eval('patient')),
                ('start_time', '<', Eval('date_notified'))])
    specimen_taken = fields.Boolean('Samples Taken')
    specimens = fields.One2Many('gnuhealth.disease_notification.specimen',
                                'notification', 'Samples',
                                states=ONLY_IF_LAB)
    hospitalized = fields.Boolean('Admitted to hospital')
    admission_date = fields.Date('Date admitted', states=ONLY_IF_ADMITTED)
    hospital = fields.Many2One('gnuhealth.institution', 'Hospital',
                               states=ONLY_IF_ADMITTED)
    ward = fields.Char('Ward', states=ONLY_IF_ADMITTED)
    deceased = fields.Boolean('Deceased')
    date_of_death = fields.Date('Date of Death', states=ONLY_IF_DEAD)
    healthprof = fields.Many2One('gnuhealth.healthprofessional', 'Reported by')
    comments = fields.Text('Additional comments')
    comments_short = fields.Function(fields.Char('Comments'), 'short_comment')
    risk_factors = fields.One2Many(
        'gnuhealth.disease_notification.risk_disease', 'notification',
        'Risk Factors', help="Other conditions of merit")
    hx_travel = fields.Boolean('Recent Foreign Travels',
                               help="History of Overseas travel in the last"
                               " 4 - 6 weeks")
    hx_locations = fields.One2Many(
        'gnuhealth.disease_notification.travel', 'notification',
        'Places visited',
        states={'invisible': ~Eval('hx_travel', False)})
    age = fields.Function(fields.Char('Age', size=8), 'get_patient_field')
    sex = fields.Function(fields.Selection(SEX_OPTIONS, 'Sex'),
                          'get_patient_field',
                          searcher='search_patient_field')
    puid = fields.Function(fields.Char('UPI', size=12), 'get_patient_field',
                           searcher='search_patient_field')
    state_changes = fields.One2Many(
        'gnuhealth.disease_notification.statechange', 'notification',
        'Status Changes', order=[('create_date', 'DESC')], readonly=True)
    # medical_record_num = fields.Function(fields.Char('Medical Record Numbers'),
    #                                      'get_patient_field',
    #                                      searcher='search_patient_field')

    @classmethod
    def __setup__(cls):
        super(DiseaseNotification, cls).__setup__()
        cls._order = [('date_onset', 'DESC')]
        cls._sql_error_messages = {
            'unique_name': 'There is another notification with this code'
        }
        cls._sql_constraints = [
            ('name_uniq', 'UNIQUE(name)', 'The code must be unique.')]

    @classmethod
    def get_patient_field(cls, instances, name):
        return dict([(x.id, getattr(x.patient, name)) for x in instances])

    @classmethod
    def short_comment(cls, instances, name):
        return dict(map(lambda x: (x.id,
                    x.comments and ' '.join(x.comments.split('\n'))[:40] or ''),
                    instances))

    @classmethod
    def search_patient_field(cls, field_name, clause):
        return replace_clause_column(clause, 'patient.%s' % field_name)

    @classmethod
    def get_rec_name(cls, records, name):
        return dict([(x.id, x.name) for x in records])

    @classmethod
    def search_rec_name(cls, field_name, clause):
        _, operand, val = clause
        return ['OR', ('patient.puid', operand, val),
                ('name', operand, val)]

    @fields.depends('reporting_facility')
    def on_change_reporting_facility(self, *arg, **kwarg):
        return {'reporting_facility_other': ''}

    @fields.depends('diagnosis', 'name')
    def on_change_with_name(self):
        curname = self.name
        if self.diagnosis:
            newcode = '%s:' % self.diagnosis.code
            if curname:
                newcode = '%s:%s' % (self.diagnosis.code, curname)
            return newcode
        elif curname and ':' in curname:
            return curname[curname.index(':')+1:]

    @fields.depends('encounter')
    def on_change_with_date_seen(self):
        return self.encounter.start_time.date() if self.encounter else None

    @staticmethod
    def default_healthprof():
        healthprof_model = Pool().get('gnuhealth.healthprofessional')
        return healthprof_model.get_health_professional()

    @staticmethod
    def default_status():
        return 'waiting'

    @staticmethod
    def default_active():
        return True

    @classmethod
    def create(cls, vlist):
        pool = Pool()
        Sequence = pool.get('ir.sequence')
        Config = pool.get('gnuhealth.sequences')
        config = Config(1)
        vlist = [x.copy() for x in vlist]
        for values in vlist:
            val_name = values.get('name', '')
            if not val_name or val_name.endswith(':'):
                newcode = Sequence.get_id(config.notification_sequence.id)
                values['name'] = '%s%s' % (values['name'], newcode)
            elif ':' in val_name and not values.get('diagnosis', False):
                values['name'] = val_name[val_name.index(':')+1:]
            if values.get('state_changes', False):
                pass
            else:
                values['state_changes'] = [
                    ('create', [{
                        'orig_state': None,
                        'target_state': values['status'],
                        'healthprof': values['healthprof']
                     }])
                ]
        return super(DiseaseNotification, cls).create(vlist)

    @classmethod
    def write(cls, records, values, *args):
        '''create a NotificationStateChange when the status changes'''
        healthprof = DiseaseNotification.default_healthprof()
        irecs = iter((records, values) + args)
        for recs, vals in zip(irecs, irecs):
            newstate = vals.get('status', False)
            to_make = []
            if newstate:
                for rec in recs:
                    if rec.status != newstate:
                        to_make.append({'notification': rec.id,
                                        'orig_state': rec.status,
                                        'target_state': newstate,
                                        'healthprof': healthprof})
        return_val = super(DiseaseNotification, cls).write(records, values,
                                                           *args)
        nsc = Pool().get('gnuhealth.disease_notification.statechange')
        nsc.create(to_make)
        return return_val

    @classmethod
    def validate(cls, records):
        now = {date: date.today(), datetime: datetime.now(), type(None): None}
        date_fields = ['date_onset', 'date_seen', 'date_notified',
                       'admission_date', 'date_of_death']
        # we need to ensure that none of these fields are in the future
        for rec in records:
            if rec.encounter:
                if rec.encounter.patient != rec.patient:
                    cls.raise_user_error('Invalid encounter selected.'
                                         'Different patient')
            for fld in date_fields:
                val = getattr(rec, fld)
                if val and val > now[type(val)]:
                    val_name = getattr(cls, fld).string
                    cls.raise_user_error('%s cannot be in the future',
                                         (val_name, ))

    @classmethod
    def copy(cls, records, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default.update(diagnosis=None, state_changes=[])
        if 'name' in default:
            del default['name']
        return super(DiseaseNotification, cls).copy(records, default=default)

    @classmethod
    def epi_week(cls, instances, name):
        def ewcalc(k):
            return (k.id, epiweek_str(k.date_onset) if k.date_onset else '')
        if name == 'epi_week_onset':
            return dict(map(ewcalc, instances))

    @classmethod
    def get_selection_display(cls, instances, field_name):
        real_field = field_name[:0 - len('_display')]
        field_selections = cls._fields[real_field].selection
        xdict = dict(filter(lambda x: x[0], field_selections))
        return dict(map(lambda x: (x.id, xdict.get(getattr(x, real_field), '')),
                    instances))


class RiskFactorCondition(ModelSQL, ModelView):
    'Risk Factor Conditions'

    __name__ = 'gnuhealth.disease_notification.risk_disease'
    notification = fields.Many2One('gnuhealth.disease_notification',
                                   'Notification', required=True)
    pathology = fields.Many2One('gnuhealth.pathology', 'Condition',
                                required=True, states=RO_SAVED)
    comment = fields.Char('Comment')

    @classmethod
    def get_rec_name(cls, records, name):
        return dict([(x.id, x.pathology.rec_name) for x in records])


class LabResultType(ModelSQL, ModelView):
    'Notification Lab Result Type'

    __name__ = 'gnuhealth.disease_notification.labresulttype'
    name = fields.Char('Name', size=50)
    code = fields.Char('Code', size=20)

    @classmethod
    def __setup__(cls):
        super(LabResultType, cls).__setup__()
        cls._sql_error_messages = {
            'unique_code': 'There is another result type with this code'
        }
        cls._sql_constraints = [('code_uniq', 'UNIQUE(code)', 'unique_code')]


class NotifiedSpecimen(ModelSQL, ModelView):
    'Disease Notification Sample'

    __name__ = 'gnuhealth.disease_notification.specimen'
    notification = fields.Many2One('gnuhealth.disease_notification',
                                   'Notification', required=True)
    name = fields.Char('Code/Identifier',
                       help='Unique barcode or other identifier assigned to, '
                       'and used for tracking the sample')
    specimen_type = fields.Selection(SPECIMEN_TYPES, 'Type', required=True,
                                     states=RO_SAVED)
    date_taken = fields.Date('Date Sample Taken', required=True,
                             states=RO_SAVED)
    lab_sent_to = fields.Char('Lab sent to', required=True, states=RO_SAVED)
    lab_test_type = fields.Selection(LAB_TEST_TYPES, 'Lab Test Type')
    lab_result = fields.Text('Lab result details', states=RO_NEW)
    lab_result_type = fields.Many2One(
        'gnuhealth.disease_notification.labresulttype', 'Result type',
        states=RO_NEW)
    lab_result_state = fields.Selection(LAB_RESULT_STATES, 'Test Result State',
                                        states=RO_NEW)
    date_tested = fields.Date('Date tested', states=RO_NEW)
    has_result = fields.Function(fields.Boolean('Results in',
                                 help="Lab results have been entered"),
                                 'get_has_result',
                                 searcher='search_has_result')
    # lab_request = fields.Many2One('gnuhealth.patient.lab.test',
    #                               'Lab Test Request')
    specimen_type_display = fields.Function(fields.Char('Sample Type'),
                                            'get_selection_display')
    lab_test_type_display = fields.Function(fields.Char('Test Type'),
                                            'get_selection_display')
    lab_result_state_display = fields.Function(fields.Char('Result State'),
                                               'get_selection_display')

    @classmethod
    def get_has_result(cls, instances, name):
        return dict([(x.id, bool(x.date_tested and x.lab_result_state))
                    for x in instances])

    @classmethod
    def search_has_result(cls, field_name, clause):
        return [(And(Bool(Eval('date_tested')),
                     Bool(Eval('lab_result_state'))),
                 clause[1], clause[2])]

    @classmethod
    def get_selection_display(cls, instances, field_name):
        real_field = field_name[:0-len('_display')]
        field_selections = cls._fields[real_field].selection
        xdict = dict(filter(lambda x: x[0], field_selections))
        return dict(map(lambda x: (x.id, xdict.get(getattr(x, real_field), '')),
                    instances))


class NotificationSymptom(ModelView, ModelSQL):
    'Symptom'

    __name__ = 'gnuhealth.disease_notification.symptom'
    name = fields.Many2One('gnuhealth.disease_notification', 'Notification',
                           required=True, states=RO_SAVED)
    pathology = fields.Many2One('gnuhealth.pathology', 'Sign/Symptom',
                                domain=[('code', 'like', 'R%')], required=True,
                                states=RO_SAVED)
    date_onset = fields.Date('Date of onset')
    comment = fields.Char('Comment')

    @classmethod
    def get_rec_name(cls, records, name):
        return dict([(x.id, x.pathology.rec_name) for x in records])


class TravelHistory(ModelView, ModelSQL):
    'Travel History'

    __name__ = 'gnuhealth.disease_notification.travel'
    notification = fields.Many2One('gnuhealth.disease_notification',
                                   'Notification', required=True)
    country = fields.Many2One('country.country', 'Country', required=True,
                              states=RO_SAVED)
    subdiv = fields.Many2One('country.subdivision', 'Province/State',
                             domain=[('country', '=', Eval('country'))],
                             depends=['country'],
                             states=RO_SAVED)
    departure_date = fields.Date('Date of departure',
                                 help='Date departed from country visited',
                                 states=RO_SAVED)
    arrival_time = fields.DateTime('Date of arrival',
                                   help='Date of arrival in this locality')
    comment = fields.Char('Comment')

    _order = [('notification', 'DESC'), ('departure_date', 'DESC'),
              ('country', 'ASC')]

    @classmethod
    def get_rec_name(cls, records, name):
        return dict([(x.id, '%s, %s' % (x.subdiv.name, x.country.name))
                    for x in records])


class NotificationStateChange(ModelSQL, ModelView):
    """Notification State Change"""
    __name__ = 'gnuhealth.disease_notification.statechange'
    notification = fields.Many2One('gnuhealth.disease_notification',
                                   'Notification')
    orig_state = fields.Selection(NOTIFICATION_STATES, 'Changed From')
    target_state = fields.Selection(NOTIFICATION_STATES, 'Changed to',
                                    required=True)
    # use the built-in create_date and create_uid to determine who
    # changed the state of the notification and when it was changed.
    # Records in this model will, be created automatically
    healthprof = fields.Many2One('gnuhealth.healthprofessional', 'Changed by')
    change_date = fields.DateTime('Changed on')
    creator = fields.Function(fields.Char('Changed by'), 'get_creator_name')

    def get_creator_name(self, name):
        pool = Pool()
        Party = pool.get('party.party')
        persons = Party.search([('internal_user', '=', self.create_uid)])
        if persons:
            return persons[0].name
        else:
            return self.create_uid.name

    @staticmethod
    def default_change_date():
        return datetime.now()
