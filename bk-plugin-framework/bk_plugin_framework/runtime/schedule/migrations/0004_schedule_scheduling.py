# Generated by Django 2.2.16 on 2022-02-14 21:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("schedule", "0003_auto_20210830_1945"),
    ]

    operations = [
        migrations.AddField(
            model_name="schedule",
            name="scheduling",
            field=models.BooleanField(default=False, verbose_name="是否正在调度"),
        ),
    ]
