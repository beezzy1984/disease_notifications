from trytond.pool import Pool
from .models import DiseaseNotification, TravelHistory, NotificationSymptom


def register():
    Pool.register(
        DiseaseNotification,
        NotificationSymptom,
        TravelHistory,
        module='health_disease_notification', type_='model')

