from trytond.pool import Pool
from .models import (DiseaseNotification, TravelHistory, NotificationSymptom,
                     NotifiedSpecimen, GnuHealthSequences)

def register():
    Pool.register(
        GnuHealthSequences,
        DiseaseNotification,
        NotificationSymptom,
        NotifiedSpecimen,
        TravelHistory,
        module='health_disease_notification', type_='model')
