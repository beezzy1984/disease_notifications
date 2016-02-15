from trytond.pool import Pool
from .models import (DiseaseNotification, TravelHistory, NotificationSymptom,
                     NotifiedSpecimen, GnuHealthSequences,
                     NotificationStateChange)

def register():
    Pool.register(
        GnuHealthSequences,
        DiseaseNotification,
        NotificationSymptom,
        NotifiedSpecimen,
        TravelHistory,
        NotificationStateChange,
        module='health_disease_notification', type_='model')
