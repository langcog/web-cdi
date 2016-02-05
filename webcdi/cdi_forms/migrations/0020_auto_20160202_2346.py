# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cdi_forms', '0019_auto_20151026_1840'),
    ]

    operations = [
        migrations.AlterField(
            model_name='backgroundinfo',
            name='annual_income',
            field=models.CharField(max_length=30, verbose_name=b'Estimated Annual Family Income (in USD)', choices=[(b'<10000', b'Under $10,000'), (b'10000-20000', b'$10,000-$20,000'), (b'20000-30000', b'$20,000-$30,000'), (b'30000-40000', b'$30,000-$40,000'), (b'40000-50000', b'$40,000-$50,000'), (b'50000-60000', b'$50,000-$60,000'), (b'60000-70000', b'$60,000-$70,000'), (b'70000-80000', b'$70,000-$80,000'), (b'80000-90000', b'$80,000-$90,000'), (b'90000-100000', b'$90,000-$100,000'), (b'100000-110000', b'$100,000-$110,000'), (b'110000-120000', b'$110,000-$120,000'), (b'120000-130000', b'$120,000-$130,000'), (b'130000-140000', b'$130,000-$140,000'), (b'140000-150000', b'$140,000-$150,000'), (b'150000-160000', b'$150,000-$160,000'), (b'160000-170000', b'$160,000-$170,000'), (b'170000-180000', b'$170,000-$180,000'), (b'180000-190000', b'$180,000-$190,000'), (b'190000-200000', b'$190,000-$200,000'), (b'>200000', b'Over $200,000'), (None, b'Prefer not to disclose')]),
        ),
        migrations.AlterField(
            model_name='backgroundinfo',
            name='sex',
            field=models.CharField(max_length=1, choices=[(b'M', b'Male'), (b'F', b'Female'), (b'O', b'Other')]),
        ),
    ]
