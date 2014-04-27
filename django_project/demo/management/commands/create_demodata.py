import random

from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType

from ...models import Indicator, AdminLevel0, AdminLevel1, AdminLevel2


class Command(BaseCommand):
    help = 'Generates random data for demo app'

    def handle(self, *args, **options):

        ad0_ct = ContentType.objects.get(app_label="demo", model="adminlevel0")

        for ad0 in AdminLevel0.objects.all():
            new_indicator = Indicator()
            new_indicator.factor_a = random.random()
            new_indicator.factor_b = random.random()
            new_indicator.content_type = ad0_ct
            new_indicator.object_id = ad0.osm_id
            new_indicator.save()
        self.stdout.write('Created demo data for AdminLevel0')

        ad1_ct = ContentType.objects.get(app_label="demo", model="adminlevel1")
        for ad1 in AdminLevel1.objects.all():
            new_indicator = Indicator()
            new_indicator.factor_a = random.random()
            new_indicator.factor_b = random.random()
            new_indicator.content_type = ad1_ct
            new_indicator.object_id = ad1.osm_id
            new_indicator.save()
        self.stdout.write('Created demo data for AdminLevel1')

        ad2_ct = ContentType.objects.get(app_label="demo", model="adminlevel2")
        for ad2 in AdminLevel2.objects.all():
            new_indicator = Indicator()
            new_indicator.factor_a = random.random()
            new_indicator.factor_b = random.random()
            new_indicator.content_type = ad2_ct
            new_indicator.object_id = ad2.osm_id
            new_indicator.save()
        self.stdout.write('Created demo data for AdminLevel2')
