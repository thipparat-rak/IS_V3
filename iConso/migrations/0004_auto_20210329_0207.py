# Generated by Django 3.1.5 on 2021-03-28 19:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('iConso', '0003_coa_master_fs_group'),
    ]

    operations = [
        migrations.CreateModel(
            name='Plan_Master',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plan_code', models.CharField(max_length=5, unique=True)),
                ('plan_description', models.CharField(max_length=100, unique=True)),
                ('plan_price', models.FloatField(max_length=15)),
                ('plan_date_create', models.DateTimeField(auto_now_add=True)),
                ('plan_date_update', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Subscription_Master',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_code', models.CharField(max_length=5, unique=True)),
                ('plan_code', models.CharField(max_length=100, unique=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(blank=True, null=True)),
                ('date_create', models.DateTimeField(auto_now_add=True)),
                ('date_update', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.DeleteModel(
            name='Conso',
        ),
        migrations.AlterField(
            model_name='company_master',
            name='company_type',
            field=models.CharField(max_length=100),
        ),
    ]