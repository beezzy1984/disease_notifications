

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
from collections import OrderedDict, Counter
from trytond.modules.health_jamaica import tryton_utils as utils
from .models import NOTIFICATION_STATES

__all__ = ['CaseCountReport', 'CaseCountStartModel', 'CaseCountWizard']


class CaseCountStartModel(ModelView):
    '''Notification date range (of onset)'''
    __name__ = 'gnuhealth.disease_notification.report.case_count_start'

    on_or_after = fields.Date('Start date', required=True)
    on_or_before = fields.Date('End date')
    state = fields.Selection(NOTIFICATION_STATES[:], 'State')

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
