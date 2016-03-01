from trytond.pool import Pool
from .models import (DiseaseNotification, TravelHistory, NotificationSymptom,
                     NotifiedSpecimen, GnuHealthSequences, RiskFactorCondition,
                     NotificationStateChange)
from .reports import CaseCountReport, CaseCountWizard


def register():
    Pool.register(
        GnuHealthSequences,
        DiseaseNotification,
        NotificationSymptom,
        NotifiedSpecimen,
        RiskFactorCondition,
        TravelHistory,
        NotificationStateChange,
        module='health_disease_notification', type_='model')

    Pool.register(
        CaseCountReport,
        module='health_disease_notification', type_='report')

    Pool.register(
        CaseCountWizard,
        module='health_disease_notification', type_='wizard')
