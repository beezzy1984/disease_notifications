
from datetime import datetime
from trytond.wizard import StateAction
from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.pyson import PYSONEncoder
from trytond.modules.health_encounter.wizard import OneEncounterWizard
from trytond.modules.health_jamaica.tryton_utils import localtime

class NotifyFromEncounter(OneEncounterWizard):
    'Disease Notification from Encounter'
    __name__ = 'gnuhealth.disease_notification.encounter_wizard'

    start_state = 'goto_notification'
    goto_notification = StateAction(
        'health_disease_notification.actwin-notification_formfirst')

    def do_goto_notification(self, action):

        enctr_id, encounter = self._get_active_encounter()

        # Does the notification entry already exist?
        notification = Pool().get('gnuhealth.disease_notification').search([
            ('encounter', '=', enctr_id)])
        if notification:
            rd = {'active_id': notification[0].id}
            action['res_id'] = rd['active_id']
        else:
            now = datetime.now()
            patient = encounter.patient
            facility = encounter.institution
            rd = {}
            action['pyson_domain'] = PYSONEncoder().encode([
                ('encounter', '=', enctr_id),
                ('patient', '=', patient.id),
                ('reporting_facility', '=', facility.id),
                ('date_notified', '=', localtime(now).strftime('%F %T'))
            ])
            action['pyson_context'] = PYSONEncoder().encode({
                'encounter': enctr_id,
                'patient': patient.id,
                'reporting_facility': facility.id,
                'date_notified': now
            })

        return action, rd
