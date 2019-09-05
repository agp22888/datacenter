from django.contrib import admin
from pisar.models import Employee, Department, Report, DepartmentType

# Register your models here.


admin.site.register(Employee)
admin.site.register(Department)
admin.site.register(Report)
admin.site.register(DepartmentType)
