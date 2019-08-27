from django import forms
from django.forms import ModelForm

from pisar.models import Department, Employee, Report


class MainForm(forms.Form):
    department_list = forms.ModelChoiceField(label="Отдел", queryset=Department.objects.all(), required=True)
    employee_list = forms.ModelChoiceField(label="Сотрудник", queryset=Employee.objects.all(), required=True)
    report_list = forms.ModelChoiceField(label="Рапорт", queryset=Report.objects.all(), required=True)

