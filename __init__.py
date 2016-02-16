from trytond.pool import Pool
from .models import (DiseaseNotification, TravelHistory, NotificationSymptom,
                     NotifiedSpecimen, GnuHealthSequences, RiskFactorCondition,
                     NotificationStateChange)


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
