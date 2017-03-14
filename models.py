# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from __future__ import unicode_literals

from django.db import models

app_label = 'plot'

class Awards(models.Model):
    award_id = models.TextField(primary_key=True)
    title = models.TextField()
    abstract = models.TextField()
    amount = models.IntegerField()
    start_date = models.CharField(max_length=10)
    end_date = models.CharField(max_length=10)
    # def __str__(self):
    #     return 'Award ID: ' + str(self.award_id)

    class Meta:
        managed = False
        db_table = 'awards'


class Institutions(models.Model):
    award_id = models.ForeignKey(Awards, on_delete=models.CASCADE)
    name = models.TextField(blank=True, null=True)
    city = models.TextField(blank=True, null=True)
    state = models.TextField(blank=True, null=True)
    state_code = models.CharField(max_length=2, blank=True, null=True)
    zipcode = models.TextField(blank=True, null=True)
    country = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'institutions'


class Investigators(models.Model):
    award_id = models.ForeignKey(Awards, on_delete=models.CASCADE)
    last_name = models.TextField(blank=True, null=True)
    first_name = models.TextField(blank=True, null=True)
    role = models.TextField(blank=True, null=True)
    email = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'investigators'


class Organizations(models.Model):
    award_id = models.ForeignKey(Awards, on_delete=models.CASCADE)
    organization_code = models.IntegerField(blank=True, null=True)
    directorate = models.TextField(blank=True, null=True)
    division = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'organizations'
