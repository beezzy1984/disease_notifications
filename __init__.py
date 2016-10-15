"""PythoThis file tell python that this folder is a python package"""
from trytond.pool import Pool
from .models import (DiseaseNotification, TravelHistory, NotificationSymptom,
                     NotifiedSpecimen, GnuHealthSequences, RiskFactorCondition,
                     NotificationStateChange, LabResultType)
from .reports import (RawDataReport, CaseCountReport, CaseCountWizard,
                      CaseCountStartModel, Notifications)
from .wizards import NotifyFromEncounter


def register():
    """Register models to tryton's pool"""
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
        Notifications,
        module='health_disease_notification', type_='report')

    Pool.register(
        CaseCountWizard,
        NotifyFromEncounter,
        module='health_disease_notification', type_='wizard')
