from trytond.pool import Pool
from .models import (DiseaseNotification, TravelHistory, NotificationSymptom,
                     NotifiedSpecimen)

def register():
    Pool.register(
        DiseaseNotification,
        NotificationSymptom,
        NotifiedSpecimen,
        TravelHistory,
        module='health_disease_notification', type_='model')
