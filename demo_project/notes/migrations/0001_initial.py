# Generated by Django 3.2.5 on 2021-07-04 10:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('from_country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='notes.country')),
            ],
        ),
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('from_country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='notes.country')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='notes.person')),
            ],
        ),
    ]
