
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval

ONLY_IF_ADMITTED = {'invisible': ~Eval('hospital_admission', False)}
ONLY_IF_LAB = {'invisible': ~Eval('specimen_taken', False)}
ONLY_IF_DEAD = {'invisible': ~Eval('deceased', False)}

REQD_IF_LAB = dict([('required', Eval('specimen_taken', False))] +
                   ONLY_IF_LAB.items())
RO_SAVED = {'readonly': Eval('id', 0) > 0}  # readonly after saved
RO_NEW = {'readonly': Eval('id', 0) < 0}  # readonly when new

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


class DiseaseNotification(ModelView, ModelSQL):
    'Disease Notification'

    __name__ = 'gnuhealth.disease_notification'
    name = fields.Char('Code',)
    patient = fields.Many2One('gnuhealth.patient', 'Patient', required=True,
                              states=RO_SAVED)
    status = fields.Selection(NOTIFICATION_STATES, 'Status')
    name = fields.Char('Code', states=RO_SAVED)
    date_notified = fields.DateTime('Date reported', required=True,
                                    states=RO_SAVED)
    diagnosis = fields.Many2One('gnuhealth.pathology', 'Presumptive Diagnosis',
                                states=RO_SAVED)
    symptoms = fields.One2Many('gnuhealth.disease_notification.symptom',
                               'name', 'Symptoms')
    date_onset = fields.Date('Date of Onset',
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
        states={'invisible': ~Eval('hx_travel', False),
                'required': Eval('hx_travel', False)})
    age = fields.Function(fields.Char('Age'), 'get_patient_field',
                          searcher='search_patient_field')
    sex_display = fields.Function(fields.Char('Sex'), 'get_patient_field',
                                  searcher='search_patient_field')
    puid = fields.Function(fields.Char('UPI'), 'get_patient_field',
                           searcher='search_patient_field')
    # medical_record_num = fields.Function(fields.Char('Medical Record Numbers'),
    #                                      'get_patient_field',
    #                                      searcher='search_patient_field')

    _order = [('date_notified', 'DESC')]


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
    lab_request = fields.Many2One('gnuhealth.patient.lab.test',
                                  'Lab Test Request')


class NotificationSymptom(ModelView, ModelSQL):
    'Symptom'

    __name__ = 'gnuhealth.disease_notification.symptom'
    name = fields.Many2One('gnuhealth.disease_notification', 'Notification',
                           required=True)
    pathology = fields.Many2One('gnuhealth.pathology', 'Sign/Symptom',
                                domain=[('code', 'like', 'R%')], required=True)
    date_onset = fields.Date('Date of onset')
    comment = fields.Char('Comment')


class TravelHistory(ModelView, ModelSQL):
    'Travel History'

    __name__ = 'gnuhealth.disease_notification.travel'
    notification = fields.Many2One('gnuhealth.disease_notification',
                                   'Notification', required=True)
    country = fields.Many2One('country.country', 'Country', required=True)
    subdiv = fields.Many2One('country.subdivision', 'Province/State',
                             domain=[('country', '=', Eval('country'))],
                             depends=['country'])
    departure_date = fields.Date('Date of departure',
                                 help='Date departed from country visited')

    _order = [('notification', 'DESC'), ('departure_date', 'DESC'),
              ('country', 'ASC')]
