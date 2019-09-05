from django.db import models


# Create your models here.

class Employee(models.Model):
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    is_male = models.BooleanField(default=True)
    tel_number = models.CharField(max_length=15)
    rank = models.IntegerField()
    dept = models.ForeignKey('Department', on_delete=models.SET_DEFAULT, default=None)
    position = models.CharField(max_length=500)

    def __str__(self):
        return '{} {}{} {}.{}.'.format(str(self.position),
                                       str(self.dept.type) + ' ' if self.dept.type is not None else '',
                                       str(self.last_name),
                                       str(self.first_name)[0],
                                       str(self.middle_name)[0])


class Department(models.Model):
    type = models.ForeignKey('DepartmentType', on_delete=models.SET_DEFAULT, default=None, blank=True, null=True)
    name = models.CharField(max_length=500)
    chief = models.ForeignKey(Employee, on_delete=models.SET_DEFAULT, default=None, null=True, blank=True)
    parent_department = models.ForeignKey('self', on_delete=models.SET_DEFAULT, default=None, null=True, blank=True)

    def __str__(self):
        return ((str(self.type) + ' ') if self.type is not None else '') + str(self.name)


class DepartmentType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return str(self.name)


class Report(models.Model):
    name = models.CharField(max_length=500)
    template_path = models.CharField(max_length=500)
