from django import forms
from django.core.exceptions import ValidationError
from django.forms import CharField

from server_list.models import Server, Unit, Rack, Room, Territory


# todo сделать отображение виртуалок физического сервера на странице редактирования // нужно ли?

class ServerFormNameField(CharField):
    def validate(self, value):
        print('validate')
        return value


class ServerForm(forms.Form):
    server_name = ServerFormNameField(label="Имя", required=True)
    server_purpose = forms.CharField(label="Назначение", required=False)
    power_state = forms.BooleanField(label="Питание", required=False)
    is_physical = forms.BooleanField(label="Физический сервер", required=False)
    server_os = forms.CharField(label="Операционная система", required=False)
    sensitive_data = forms.CharField(label="Учётные данные", required=False)
    host_machine = forms.ChoiceField(label="Физический сервер", required=False,
                                     choices=[(str(ser.id), ser.hostname) for ser in
                                              Server.objects.filter(is_physical=True)],
                                     initial=Server.objects.filter(pk=2))
    # host_machine = forms.ChoiceField(label="Физический сервер", required=False)
    server_unit = forms.IntegerField(label="Юнит", required=False)
    server_height = forms.IntegerField(label="Высота в юнитах", required=False)
    server_model = forms.CharField(label="Модель", required=False)
    server_specs = forms.CharField(label="Характеристики", required=False)
    server_serial_number = forms.CharField(label="Серийный номер", required=False)
    server_territory = forms.ChoiceField(label="Территория", required=False,
                                         choices=[(str(ter.id), ter.name) for ter in Territory.objects.all()])
    server_room = forms.ChoiceField(label='Помещение', required=False,
                                    choices=[(str(room.id), room.name) for room in Room.objects.all()])
    server_rack = forms.ChoiceField(label='Стойка', required=False,
                                    choices=[(str(rack.id), rack.name) for rack in Rack.objects.all()])

    vm_fields_to_hide = ['server_unit', 'server_model', 'server_height', 'server_serial_number', 'server_territory',
                         'server_room', 'server_rack']
    physical_fields_to_hide = ['host_machine']

    def clean(self):
        print("form_clean, server_id is:", self.server_id)

        # server = Server.objects.get(pk=self.server_id)
        if not self.cleaned_data['is_physical']:
            if self.cleaned_data['host_machine'] == self.server_id:
                self.errors.update({'host_machine': ['Виртуальная машина не может хоститься сама на себе!']})
        for field in self.fields:
            if 'ip_' in field:
                data = self.cleaned_data[field]
                data_split = data.split('.')
                if len(data_split) != 4:
                    self.errors.update({field: ['invalid ip']})
                for split in data_split:
                    try:
                        if int(split) > 255 or int(split) < 0:
                            self.errors.update({field: ['invalid ip']})
                    except ValueError:
                        self.errors.update({field: ['invalid ip']})

        if self.cleaned_data['is_physical'] and 'unit' in field and not self.new:
            if self.cleaned_data[field] is None or self.cleaned_data['server_height'] is None \
                    or self.cleaned_data[field] <= 0 or self.cleaned_data['server_height'] < - 0:
                self.errors.update({field: ['Error']})
                return
            unit_low = self.cleaned_data[field]
            unit_high = unit_low + self.cleaned_data['server_height'] - 1
            rack = int(self.cleaned_data['server_rack'])
            for s in Rack.objects.get(pk=rack).server_set.all():
                if s.id == int(self.server_id):
                    continue
                s_unit = s.unit
                s_unit_high = s_unit + s.height - 1
                if s_unit <= unit_low <= s_unit_high \
                        or s_unit <= unit_high <= s_unit_high \
                        or unit_low < s_unit and unit_high > s_unit_high:
                    self.errors.update({field: [
                        'unit already in use by ' + s.hostname + '; units: ' + s.get_unit_string()]})  # todo добавить ссылку на сервер, с которым идёт пересечение?

    def __init__(self, *args, **kwargs, ):
        self.server_id = kwargs.pop('server_id', None)
        self.new = kwargs.pop('new_server', False)
        super(ServerForm, self).__init__(*args, **kwargs)
        # if len(self.fields['host_machine'].choices) > 0:

        # self.data['host_machine'].initial = ('2', 2)  # self.fields['host_machine'].choices[0]
        if not self.new:
            ser = Server.objects.get(pk=self.server_id)
            self.server_is_physical = ser.is_physical
            if ser.is_physical:
                print('server_isphysical: true')
            else:
                self.host_machine_id = ser.host_machine.id
            for ip in ser.ip_set.all():
                field_name = r'ip_' + str(ip.id)
                self.fields[field_name] = forms.CharField(label=ip.segment.name, max_length=100)

# class MyForm(forms.Form):
#     def __init__(self, *args, **kwargs):
#         super(MyForm, self).__init__(*args, **kwargs)
#         for i, q in enumerate(Question.objects.all()):
#             self.fields['%s_field' % i] = forms.CharField(max_length=100, label=q.questionText)
