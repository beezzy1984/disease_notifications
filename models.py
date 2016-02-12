
from trytond.model import ModelView, ModelSQL, fields, ModelSingleton
from trytond.pyson import Eval
from trytond.pool import Pool
import re

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
    ('confirmed', 'Confirmed'),
    ('discarded', 'Discarded (confirmed negative)')
]
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
    patient = fields.Many2One('gnuhealth.patient', 'Patient', required=True,
                              states=RO_SAVED)
    status = fields.Selection(NOTIFICATION_STATES, 'Status', required=True,
                              sort=False)
    name = fields.Char('Code', size=18, states={'readonly': True})
    date_notified = fields.DateTime('Date reported', required=True,
                                    states=RO_SAVED)
    diagnosis = fields.Many2One('gnuhealth.pathology', 'Presumptive Diagnosis',
                                states=RO_SAVED, required=True)
    symptoms = fields.One2Many('gnuhealth.disease_notification.symptom',
                               'name', 'Symptoms')
    date_onset = fields.Date('Date of Onset', required=True,
                             help='Date of onset of the illness',
                             states=RO_SAVED)
    date_seen = fields.Date('Date Seen', states=RO_SAVED)
    encounter = fields.Many2One('gnuhealth.encounter', 'Clinical Encounter'),
    specimen_taken = fields.Boolean('Specimen Taken')
    specimens = fields.One2Many('gnuhealth.disease_notification.specimen',
                                'notification', 'Specimens',
                                states=ONLY_IF_LAB)
    hospitalized = fields.Boolean('Admitted to hospital')
    admission_date = fields.Date('Date admitted', states=ONLY_IF_ADMITTED)
    hospital = fields.Many2One('gnuhealth.institution', 'hospital',
                               states=ONLY_IF_ADMITTED)
    ward = fields.Char('Ward', states=ONLY_IF_ADMITTED)
    deceased = fields.Boolean('Deceased')
    date_of_death = fields.Date('Date of Death', states=ONLY_IF_DEAD)
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
    # medical_record_num = fields.Function(fields.Char('Medical Record Numbers'),
    #                                      'get_patient_field',
    #                                      searcher='search_patient_field')

    _order = [('date_notified', 'DESC')]

    @classmethod
    def get_patient_field(cls, instances, name):
        return dict([(x.id, getattr(x.patient, name)) for x in instances])

    @fields.depends('diagnosis')
    def on_change_with_name(self):
        return '%s:' % self.diagnosis.code

    @classmethod
    def create(cls, vlist):
        pool = Pool()
        Sequence = pool.get('ir.sequence')
        Config = pool.get('gnuhealth.sequences')
        config = Config(1)
        vlist = [x.copy() for x in vlist]
        for values in vlist:
            if values.get('name', '').endswith(':'):
                newcode = Sequence.get_id(config.notification_sequence.id)
                print 'Assigning code: %s%s' % (values['name'], newcode)
                values['name'] = '%s%s' % (values['name'], newcode)

        return super(DiseaseNotification, cls).create(vlist)


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
    has_result = fields.Function(fields.Boolean('Results in'), 'get_has_result',
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
