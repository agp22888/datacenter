from django.db import models


# Create your models here.

class Employee(models.Model):
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    is_male = models.BooleanField(default=True)
    tel_number = models.CharField(max_length=11)
    rank = models.IntegerField()
    supervisor = models.ForeignKey('self', on_delete=models.SET_DEFAULT, default=None)
    department = models.ForeignKey('Department', on_delete=models.SET_DEFAULT, default=None)
    position = models.CharField(max_length=500)


class Department(models.Model):
    name = models.CharField(max_length=500)
    chief = models.ForeignKey(Employee, on_delete=models.SET_DEFAULT, default=None)
    parent_department = models.ForeignKey('self', on_delete=models.SET_DEFAULT, default=None)


class Report(models.Model):
    name = models.CharField(max_length=500)
    template_path = models.CharField(max_length=500)
