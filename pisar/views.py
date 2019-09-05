import os

from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from pisar.forms import MainForm, EmployeeForm

from docxtpl import DocxTemplate
from docx.shared import Pt
from petrovich.main import Petrovich
from petrovich.enums import Case, Gender
import pymorphy2
import datetime

from pisar.models import Employee


def main(request):
    emp = Employee.objects.get(pk=1)
    chain = []
    chain.append(emp)
    d = emp.dept
    while True:
        chain.append(d.chief)
        if d.parent_department is None:
            break
        d = d.parent_department

    return render(request, os.path.join('pisar', 'main.html'), {'chain': chain})


def employee(request):
    if request.method == 'GET':
        form = EmployeeForm()
        return render(request, os.path.join('pisar', 'main.html'), {'form': form})
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponse('saved')
        else:
            return render(request, os.path.join('pisar', 'main.html'), {'form': form})
