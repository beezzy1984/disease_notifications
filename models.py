
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval

ONLY_IF_ADMITTED = {'invisible': ~Eval('hospital_admission', False)}
ONLY_IF_LAB = {'invisible': ~Eval('specimen_taken', False)}
ONLY_IF_DEAD = {'invisible': ~Eval('deceased', False)}

REQD_IF_LAB = dict([('required', Eval('specimen_taken', False))] +
                   ONLY_IF_LAB.items())
RO_SAVED = {'readonly': Eval('id', 0) > 0}
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
    ('csf', 'Csf, - Cerebrospinal Fluid'),
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

    @classmethod
    def __setup__(cls):
        super(DiseaseNotification, cls).__setup__()
        cls._order.insert(0, ('date_notified', 'DESC'))


class NotifiedSpecimen(ModelSQL, ModelView):
    'Specimen'

    __name__ = 'gnuhealth.disease_notification.specimen'
    notification = fields.Many2One('gnuhealth.disease_notification',
                                   'Notification', required=True)
    specimen_type = fields.Char('Type', required=True)
    date_taken = fields.Date('Date Speciment Taken', required=True)
    lab_sent_to = fields.Char('Lab sent to', required=True)
    lab_result = fields.Char('Lab test result')
    date_tested = fields.Date('Date tested')
    lab_request = fields.Many2One('gnuhealth.patient.lab.test',
                                  'Lab Test Request')


class NotificationSymptom(ModelView, ModelSQL):
    'Symptom'

    __name__ = 'gnuhealth.disease_notification.symptom'
    name = fields.Many2One('gnuhealth.disease_notification', 'Notification')
    pathology = fields.Many2One('gnuhealth.pathology', 'Sign/Symptom',
                                domain=[('code', 'like', 'R%')], required=True)
    date_onset = fields.Date('Date of onset')
    comment = fields.Char('Comment')


class TravelHistory(ModelView, ModelSQL):
    'Travel History'

    __name__ = 'gnuhealth.disease_notification.travel'
    notification = fields.Many2One('gnuhealth.disease_notification',
                                   'Notification')
    country = fields.Many2One('country.country', 'Country', required=True)
    subdiv = fields.Many2One('country.subdivision', 'Province/State',
                             domain=[('country', '=', Eval('country'))],
                             depends=['country'])
    departure_date = fields.Date('Date of departure',
                                 help='Date departed from country visited')
