from trytond.pool import Pool
from .models import DiseaseNotification


def register():
    Pool.register(
        DiseaseNotification,
        module='health_disease_notification', type_='model')

