# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cdi_forms', '0023_auto_20160205_0919'),
    ]

    operations = [
        migrations.AlterField(
            model_name='backgroundinfo',
            name='annual_income',
            field=models.CharField(max_length=30, verbose_name=b'Estimated Annual Family Income (in USD)', choices=[(b'<25000', b'Under $25,000'), (b'25000-50000', b'$25,000-$50,000'), (b'50000-75000', b'$50,000-$75,000'), (b'75000-100000', b'$75,000-$100,000'), (b'100000-125000', b'$100,000-$125,000'), (b'125000-150000', b'$125,000-$150,000'), (b'150000-175000', b'$150,000-$175,000'), (b'175000-200000', b'$175,000-$200,000'), (b'>200000', b'Over $200,000'), (b'Prefer not to disclose', b'Prefer not to disclose')]),
        ),
    ]
