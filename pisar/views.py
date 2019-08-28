import os

from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from pisar.forms import MainForm


def main(request):
    form = MainForm()
    return render(request, os.path.join('pisar', 'main.html'), {'form': form})
