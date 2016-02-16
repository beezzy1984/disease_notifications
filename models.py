
from trytond.model import ModelView, ModelSQL, fields, ModelSingleton
from trytond.pyson import Eval, In, And, Bool
from trytond.pool import Pool
from trytond.modules.health_jamaica.tryton_utils import get_epi_week
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
    ('suspected', 'Suspected'),
    ('pending', 'Pending'),
    ('confirmed', 'Confirmed'),
    ('discarded', 'Discarded (confirmed negative)'),
    ('delete', 'Duplicate, Discard')
]
NOTIFICATION_END_STATES = ['discarded', 'delete', 'confirmed']
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
    ('blood smear', 'Blood Smear')]


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
    name = fields.Char('Code', size=18, states={'readonly': True})
    date_notified = fields.DateTime('Date reported', required=True,
                                    states=RO_SAVED)
    diagnosis = fields.Many2One('gnuhealth.pathology', 'Presumptive Diagnosis',
                                states=RO_STATE_END, required=False)
    symptoms = fields.One2Many('gnuhealth.disease_notification.symptom',
                               'name', 'Symptoms', states=RO_STATE_END)
    date_onset = fields.Date('Date of Onset',
                             help='Date of onset of the illness')
    epi_week_onset = fields.Function(fields.Char('Epi. Week of onset', size=8,
                                     help='Week of onset (epidemiological)'),
                                    'epi_week', searcher='search_epi_week')
    date_seen = fields.Date('Date Seen', states=RO_SAVED)
    encounter = fields.Many2One('gnuhealth.encounter', 'Clinical Encounter',
                                states={
                                    'readonly': And(Bool(Eval('id', 0)),
                                                    Bool(Eval('encounter')))})
    specimen_taken = fields.Boolean('Specimen Taken')
    specimens = fields.One2Many('gnuhealth.disease_notification.specimen',
                                'notification', 'Specimens',
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
    risk_factors = fields.One2Many(
        'gnuhealth.disease_notification.risk_disease', 'notification',
        'Risk Factors', help="Other conditions of merit")
    hx_travel = fields.Boolean('Overseas Travel',
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
        'State Changes')
    # medical_record_num = fields.Function(fields.Char('Medical Record Numbers'),
    #                                      'get_patient_field',
    #                                      searcher='search_patient_field')

    _order = [('date_notified', 'DESC')]

    @classmethod
    def get_patient_field(cls, instances, name):
        return dict([(x.id, getattr(x.patient, name)) for x in instances])

    @classmethod
    def get_rec_name(cls, records, name):
        return dict([(x.id, x.name) for x in records])

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

    @staticmethod
    def default_healthprof():
        healthprof_model = Pool().get('gnuhealth.healthprofessional')
        return healthprof_model.get_health_professional()

    @staticmethod
    def default_status():
        return 'suspected'

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
        NotificationStateChange.create(to_make)
        return return_val

    @classmethod
    def validate(cls, records):
        now = {date: date.today(), datetime: datetime.now(), type(None): None}
        date_fields = ['date_onset', 'date_seen', 'date_notified',
                       'admission_date', 'date_of_death']
        for rec in records:
            for fld in date_fields:
                val = getattr(rec, fld)
                if val and val > now[type(val)]:
                    val_name = getattr(cls, fld).string
                    cls.raise_user_error('%s cannot be in the future',
                                         (val_name, ))

    @classmethod
    def epi_week(cls, instances, name):
        epidisp = lambda d: '%d/%02d' % get_epi_week(d)[2:]
        if name == 'epi_week_onset':
            return dict([(k.id, epidisp(k.date_onset)) for k in instances])

    @classmethod
    def search_epi_week(cls, field_name, clause):
        pass


class RiskFactorCondition(ModelSQL, ModelView):
    'Risk Factor Conditions'

    __name__ = 'gnuhealth.disease_notification.risk_disease'
    notification = fields.Many2One('gnuhealth.disease_notification',
                                   'Notification', required=True)
    pathology = fields.Many2One('gnuhealth.pathology', 'Condition',
                                required=True, states=RO_SAVED)
    comment = fields.Char('Comment', size=200)

    @classmethod
    def get_rec_name(cls, records, name):
        return dict([(x.id, x.pathology.rec_name) for x in records])


class NotifiedSpecimen(ModelSQL, ModelView):
    'Specimen'

    __name__ = 'gnuhealth.disease_notification.specimen'
    notification = fields.Many2One('gnuhealth.disease_notification',
                                   'Notification', required=True)
    specimen_type = fields.Selection(SPECIMEN_TYPES, 'Type', required=True,
                                     states=RO_SAVED)
    date_taken = fields.Date('Date Speciment Taken', required=True,
                             states=RO_SAVED)
    lab_sent_to = fields.Char('Lab sent to', required=True, states=RO_SAVED)
    lab_result = fields.Text('Lab test result', states=RO_NEW)
    date_tested = fields.Date('Date tested', states=RO_NEW)
    comment = fields.Char('Comment')
    has_result = fields.Function(fields.Boolean('Results in',
                                 help="Lab results have been entered"),
                                 'get_has_result',
                                 searcher='search_has_result')
    # lab_request = fields.Many2One('gnuhealth.patient.lab.test',
    #                               'Lab Test Request')

    @classmethod
    def get_has_result(cls, instances, name):
        return dict([(x.id, bool(x.date_tested and x.lab_result))
                    for x in instances])

    @classmethod
    def search_has_result(cls, field_name, clause):
        return [(And(Bool(Eval('date_tested')), Bool(Eval('lab_result'))),
                 clause[1], clause[2])]


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
    change_date = fields.Function(fields.DateTime('Changed on'),
                                  'get_change_date')
    creator = fields.Function(fields.Char('Changed by'), 'get_creator_name')

    def get_creator_name(self, name):
        pool = Pool()
        Party = pool.get('party.party')
        persons = Party.search([('internal_user', '=', self.create_uid)])
        if persons:
            return persons[0].name
        else:
            return self.create_uid.name

    def get_change_date(self, name):
        # we're sending back the create date since these are readonly
        return self.create_date
