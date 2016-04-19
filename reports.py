

from datetime import datetime, timedelta
import pytz
from trytond.pyson import Eval, PYSONEncoder, Date
from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.report import Report
from itertools import groupby
from trytond.model import ModelView, fields
from trytond.wizard import (Wizard, StateView, StateTransition, Button,
                            StateAction)
from collections import OrderedDict, Counter, defaultdict
from trytond.modules.health_jamaica import tryton_utils as utils
from .models import NOTIFICATION_STATES

__all__ = ['RawDataReport', 'CaseCountReport', 'CaseCountStartModel',
           'CaseCountWizard']


class RawDataReport(Report):
    'Disease Notification Spreadsheet Export'
    __name__ = 'health_disease_notification.rawdata'

    @classmethod
    def parse(cls, report, records, data, localcontext):
        symptoms = [("R19.7", "Diarrhoea, unspecified"),
                    ("R53.1", "Asthenia (generalized weakness)"),
                    ("R29.5", "Joint pain or stiffness (arthralgia)"),
                    ("R29.7", "Joint swelling "),
                    ("R60.2", "Periarticular oedema"),
                    ("R52.3", "Muscle pain"),
                    ("R52.4", "Back pain"),
                    ("R11.1", "Vomitting"),
                    ("R50.9", "Fever, unspecified "),
                    ("R05", "Cough"),
                    ("R06.0", "Dyspnoea "),
                    ("R06.2", "Wheezing"),
                    ("R07.4", "Chest pain"),
                    ("R60.0", "Swelling of feet"),
                    ("R56.0", "Convulsions, not elsewhere classified"),
                    ("R07.0", "Pain in throat (sore throat)"),
                    ("R21", "Rash"),
                    ("R68.6", "Non-purulent conjunctivitis "),
                    ("R68.7", "Conjunctival hyperaemia"),
                    ("R51", "Headache"),
                    ("R53", "Malaise and fatigue"),
                    ("R17", "Jaundice"),
                    ("R29.1", "Meningeal irritation "),
                    ("R40", "Altered consciousness/somnolence "),
                    ("R40.1", "Stupor"),
                    ("R26", "Paralysis"),
                    ("R04.2", "Cough with Haemorrhage "),
                    ("R58", "Haemorrhage"),
                    ("R04.4", "Epistaxis")]
        default_symptoms = defaultdict(lambda: u'')
        ordered_symptoms = defaultdict(default_symptoms.copy)
        other_symptoms = default_symptoms.copy()
        symptom_set = set([x for x, _ in symptoms])
        for rec in records:
            my_symptoms = set([x.pathology.code for x in rec.symptoms])
            my_yeses = my_symptoms.intersection(symptom_set)
            my_others = my_symptoms.difference(symptom_set)
            ordered_symptoms[rec.id].update([(r, u'Yes') for r in my_yeses])
            if my_others:
                other_symptoms[rec.id] = u', '.join(sorted(my_others))
        # This value represents the number days from 0000-00-00 to 1900-01-02
        # xldate = 693594
        # xldate = lambda val: val.toordinal() - 693594 if val else None
        xldate = lambda val: val if val else None
        # 42449 is the xldate for March 20, 2016
        localcontext.update(
            ordered_symptoms=ordered_symptoms,
            symptom_list=symptoms,
            xldate=xldate,
            other_symptoms=other_symptoms)

        return super(RawDataReport, cls).parse(report, records, data,
                                               localcontext)


class CaseCountStartModel(ModelView):
    '''Notification date range (of onset)'''
    __name__ = 'gnuhealth.disease_notification.report.case_count_start'

    on_or_after = fields.Date('Start date', required=True)
    on_or_before = fields.Date('End date')
    state = fields.Selection(NOTIFICATION_STATES[:-1], 'State',
                             sort=False)

    @classmethod
    def __setup__(cls):
        super(CaseCountStartModel, cls).__setup__()
        cls.state.selection[0] = (None, 'All States')

    @staticmethod
    def default_state():
        return 'suspected'


class CaseCountWizard(Wizard):
    __name__ = 'health_disease_notification.case_count_wizard'
    start = StateView(
        'gnuhealth.disease_notification.report.case_count_start',
        'health_disease_notification.view_form-case_count_start',
        [Button('Cancel', 'end', 'tryton-cancel'),
         Button('Generate report', 'generate_report', 'tryton-ok',
                default=True)])
    generate_report = StateAction(
        'health_disease_notification.reptnotif_case_count')

    def transition_generate_report(self):
        return 'end'

    def do_generate_report(self, action):
        data = {'start_date': self.start.on_or_after,
                'end_date': self.start.on_or_after,
                'state': self.start.state}

        if self.start.on_or_before:
            data['end_date'] = self.start.on_or_before

        # if self.start.institution:
        #     data['institution'] = self.start.institution.id
        # else:
        #     self.start.raise_user_error('required_institution')
        #     return 'start'

        return action, data


class CaseCountReport(Report):
    '''
    Case Count Report (by Epi Week)
    '''
    __name__ = 'health_disease_notification.case_count'

    @classmethod
    def parse(cls, report, records, data, localcontext):
        pool = Pool()
        tz = utils.get_timezone()
        start_week = utils.get_epi_week(data['start_date'])
        start_date = utils.get_start_of_day(start_week[0], tz)
        end_week = utils.get_epi_week(data['end_date'])
        end_date = utils.get_start_of_next_day(end_week[1], tz)
        all_weeks = [utils.epiweek_str(start_week)]
        if start_week[2:] != end_week[2:]:
            adder = 1
            while (start_date + timedelta(7 * adder)) < end_date:
                all_weeks.append(
                    utils.epiweek_str(start_date + timedelta(7 * adder)))
                adder += 1
            all_weeks.append(utils.epiweek_str(end_week))

        empty_weeks = dict(zip(all_weeks, [0] * len(all_weeks)))
        status_dict = dict(NOTIFICATION_STATES)
        if data['state']:
            query_status = data['state']
            selected_status = status_dict.get(data['state'], 'Unknown')
        else:
            query_status = False
            selected_status = 'All'

        search_domain = [('date_notified', '>=', start_date),
                         ('date_notified', '<', end_date)]
        if query_status:
            search_domain.append(('status', '=', query_status))
        notifi_model = pool.get('gnuhealth.disease_notification')
        notification_ids = notifi_model.search(
            search_domain, order=[('diagnosis', 'ASC'), ('date_onset', 'ASC')])
        notifications = notifi_model.read(
            notification_ids,
            fields_names=['diagnosis.name', 'date_onset', 'name',
                          'epi_week_onset', 'diagnosis'])
        counts = {}
        epi_weeks = Counter(empty_weeks.copy())
        for pathology, pnotif in groupby(notifications,
                                         lambda x: x['diagnosis.name']):
            counts.setdefault(pathology, Counter(empty_weeks.copy())).update(
                Counter([x['epi_week_onset'] for x in pnotif]))
        count_out = []
        for p, c in counts.items():
            epi_weeks.update(c)
            count_out.append({'week_counts': c, 'disease': p,
                              'total': sum(c.values())})
        count_out.sort(key=lambda x: x['disease'])

        localcontext.update(weeks=sorted(epi_weeks.keys()),
                            disease_counts=count_out, week_totals=epi_weeks,
                            start_date_str=start_date.strftime('%Y-%m-%d'),
                            end_date_str=end_date.strftime('%Y-%m-%d'),
                            status=selected_status)

        return super(CaseCountReport, cls).parse(report, records, data,
                                                 localcontext)
