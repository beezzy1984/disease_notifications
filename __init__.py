from trytond.pool import Pool
from .models import (DiseaseNotification, TravelHistory, NotificationSymptom,
                     NotifiedSpecimen, GnuHealthSequences, RiskFactorCondition,
                     NotificationStateChange, LabResultType)
from .reports import (RawDataReport, CaseCountReport, CaseCountWizard,
                      CaseCountStartModel)


def register():
    Pool.register(
        GnuHealthSequences,
        DiseaseNotification,
        NotificationSymptom,
        LabResultType,
        NotifiedSpecimen,
        RiskFactorCondition,
        TravelHistory,
        NotificationStateChange,
        CaseCountStartModel,
        module='health_disease_notification', type_='model')

    Pool.register(
        RawDataReport,
        CaseCountReport,
        module='health_disease_notification', type_='report')

    Pool.register(
        CaseCountWizard,
        module='health_disease_notification', type_='wizard')
