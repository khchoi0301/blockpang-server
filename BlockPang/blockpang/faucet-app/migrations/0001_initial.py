# Generated by Django 2.1.3 on 2018-11-27 11:16

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('TxHash', models.CharField(max_length=70)),
                ('Block', models.IntegerField()),
                ('Age', models.DateField(auto_now_add=True)),
                ('From_Wallet', models.CharField(max_length=50)),
                ('To_Wallet', models.CharField(max_length=50)),
                ('Amount', models.DecimalField(decimal_places=12, max_digits=20)),
                ('TxFee', models.DecimalField(decimal_places=12, max_digits=20)),
            ],
        ),
    ]
