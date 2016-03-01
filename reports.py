

from datetime import datetime, timedelta
import pytz
from trytond.pyson import Eval, PYSONEncoder, Date
from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.report import Report
from itertools import groupby
from trytond.wizard import (Wizard, StateView, StateTransition, Button,
                            StateAction)
from collections import OrderedDict, Counter
from trytond.modules.health_jamaica.tryton_utils import (
    get_epi_week, replace_clause_column, get_timezone
)
from trytond.modules.health_jamaica.wizards import StartEndDateModel


__all__ = ['CaseCountReport']


class CaseCountStartModel(ModelView):
    '''Notification date range (of onset)'''
    __name__ = 'health.disease_notification.report.case_count_start'

    on_or_after = fields.Date('Start date', required=True)
    on_or_before = fields.Date('End date')



class CaseCountWizard(Wizard):
    __name__ = 'health_disease_notification.case_count_wizard'
    start = StateTransition()
    generate_report = StateAction(
        'health_disease_notification.reptnotif_case_count')

    def transition_generate_report(self):
        return 'end'

    def transition_start(self):
        return 'generate_report'

    def do_generate_report(self, action):
        # data = {'start_date': self.start.on_or_after,
        #         'end_date': self.start.on_or_after}

        # if self.start.on_or_before:
        #     data['end_date'] = self.start.on_or_before

        # if self.start.institution:
        #     data['institution'] = self.start.institution.id
        # else:
        #     self.start.raise_user_error('required_institution')
        #     return 'start'

        # return action, data
        return action, {}


class CaseCountReport(Report):
    '''
    Case Count Report (by Epi Week)
    '''
    __name__ = 'health_disease_notification.case_count'

    @classmethod
    def parse(cls, report, records, data, localcontext):
        pool = Pool()
        tz = get_timezone()
        # start_date = utils.get_start_of_day(data['start_date'], tz)
        # end_date = utils.get_start_of_next_day(data['end_date'], tz)
        start_date = datetime(2016, 1, 1, 0, 0, 0, tzinfo=tz)
        end_date = datetime.now(tz)
        notifi_model = pool.get('gnuhealth.disease_notification')
        notification_ids = notifi_model.search(
            [('date_notified', '>=', start_date),
             ('date_notified', '<', end_date)],
            order=[('diagnosis', 'ASC'), ('date_onset', 'ASC')])
        notifications = notifi_model.read(notification_ids,
            fields_names=['diagnosis.name', 'date_onset', 'name',
                          'epi_week_onset', 'diagnosis'])
        counts = {}
        epi_weeks = Counter()
        for pathology, pnotif in groupby(notifications,
                                         lambda x: x['diagnosis.name']):
            counts.setdefault(pathology, Counter([])).update(
                Counter([x['epi_week_onset'] for x in pnotif]))
        count_out = []
        for p, c in counts.items():
            epi_weeks.update(c)
            count_out.append({'week_counts': c, 'disease': p,
                              'total': sum(c.values())})
        count_out.sort(key=lambda x: x['disease'])

        localcontext.update(weeks=sorted(epi_weeks.keys()),
                            disease_counts=count_out, week_totals=epi_weeks,
                            start_date_str=start_date.strftime('%Y-%b-%d'),
                            end_date_str=end_date.strftime('%Y-%b-%d'),
                            status='All')
        print('%s\n%s\n%s' % ('*'*77, repr(notifications), '*'*77))
        return super(CaseCountReport, cls).parse(report, records, data,
                                                 localcontext)
