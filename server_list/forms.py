from django import forms
from django.forms import CharField, ModelForm, GenericIPAddressField

from server_list.models import Server, Rack, Room, Territory, Segment, Ip
from django.db.utils import OperationalError


# todo сделать отображение виртуалок физического сервера на странице редактирования // нужно ли?

class ServerFormNameField(CharField):
    def validate(self, value):
        print('validate')
        return value


class ServerForm(forms.Form):
    field_order = ['server_name',
                   'server_purpose',
                   'power_state',
                   'is_physical',
                   'host_machine',
                   'server_os',
                   'server_model',
                   'server_specs',
                   'server_serial_number',
                   'sensitive_data',
                   'server_unit',
                   'server_height',
                   'server_location',
                   'server_rack',
                   'server_room',
                   'server_territory']
    server_name = ServerFormNameField(label="Имя", required=True, initial="Новый сервер")
    server_purpose = forms.CharField(label="Назначение", required=False)
    power_state = forms.BooleanField(label="Питание", required=False, initial=True)
    is_physical = forms.BooleanField(label="Физический сервер", required=False, initial=True)
    server_os = forms.CharField(label="Операционная система", required=False)
    sensitive_data = forms.CharField(label="Учётные данные", required=False)
    try:
        host_machine = forms.ChoiceField(label="Физический сервер", required=False,
                                         choices=[(str(ser.id), ser.hostname) for ser in
                                                  Server.objects.filter(is_physical=True)],
                                         initial=Server.objects.filter(pk=2))
        server_territory = forms.ChoiceField(label="Территория", required=False,
                                             choices=[(str(ter.id), ter.name) for ter in Territory.objects.all()])
        server_room = forms.ChoiceField(label='Помещение', required=False,
                                        choices=[(str(room.id), room.name) for room in Room.objects.all()])
        server_rack = forms.ChoiceField(label='Стойка', required=False,
                                        choices=[(str(rack.id), rack.name) for rack in Rack.objects.all()])
    except OperationalError:
        print("operational error")
        pass
    server_unit = forms.IntegerField(label="Юнит", required=False)
    server_height = forms.IntegerField(label="Высота в юнитах", required=False)
    server_model = forms.CharField(label="Модель", required=False)
    server_specs = forms.CharField(label="Характеристики", required=False)
    server_serial_number = forms.CharField(label="Серийный номер", required=False)
    server_location = forms.ChoiceField(label='Расположение в стойке', required=False,
                                        choices=[(i, n) for i, n in Server.locations.items()])
    vm_fields_to_hide = ['server_unit', 'server_model', 'server_height', 'server_serial_number', 'server_territory',
                         'server_room', 'server_rack', 'server_location']
    physical_fields_to_hide = ['host_machine']

    def clean(self):
        print("form_clean, server_id is:", self.server_id)

        if not self.cleaned_data['is_physical']:
            if self.cleaned_data['host_machine'] == self.server_id:
                self.errors.update({'host_machine': ['Виртуальная машина не может хоститься сама на себе!']})
        for field in self.fields:
            if 'ip_' in field:
                data = self.cleaned_data[field]
                if not Ip.check_ip(data):
                    self.errors.update({field: ['invalid ip']})

        if self.cleaned_data['is_physical']:
            if self.cleaned_data['server_unit'] is None or self.cleaned_data['server_height'] is None \
                    or self.cleaned_data['server_unit'] <= 0 or self.cleaned_data['server_height'] <= 0:
                self.errors.update({'server_unit': ['Error']})
                return
            unit_low = self.cleaned_data['server_unit']
            unit_high = unit_low + self.cleaned_data['server_height'] - 1
            rack = int(self.cleaned_data['server_rack'])
            for s in Rack.objects.get(pk=rack).server_set.all():
                if self.server_id is not None and s.id == int(self.server_id):
                    continue
                s_unit_low = s.unit
                s_unit_high = s_unit_low + s.height - 1
                s_location = s.location
                print('server location is', self.cleaned_data['server_location'], s_location)
                if ((s_unit_low <= unit_low <= s_unit_high or s_unit_low <= unit_high <= s_unit_high) \
                    or (unit_low < s_unit_low and unit_high > s_unit_high)) \
                        and (s_location == int(self.cleaned_data['server_location']) or s_location == 3):
                    self.errors.update({'server_unit': [
                        'unit already in use by ' + s.hostname + '; units: ' +
                        s.get_unit_string() + Server.locations.get(s.location)]})
                    # todo добавить ссылку на сервер, с которым идёт пересечение?

    def __init__(self, *args, **kwargs, ):
        self.server_id = kwargs.pop('server_id', None)
        self.new = kwargs.pop('new_server', False)
        super(ServerForm, self).__init__(*args, **kwargs)
        if not self.new:
            ser = Server.objects.get(pk=self.server_id)
            for ip in ser.ip_set.all():
                field_name = r'ip_' + str(ip.id)
                self.fields[field_name] = forms.CharField(label=ip.segment.name, max_length=100)


class IpForm(forms.Form):
    try:
        segment_id = forms.ChoiceField(label="Сегмент", required=False, choices=[(str(seg.id), seg.name) for seg in
                                                                                 Segment.objects.all()])
    except OperationalError:
        pass
    ip = forms.CharField(label="IP", required=True, initial="0.0.0.0")

    def __init__(self, *args, **kwargs):
        super(IpForm, self).__init__(*args, **kwargs)
        self.fields['segment_id'] = forms.ChoiceField(
            choices=[(str(seg.id), seg.name) for seg in Segment.objects.all()])

    def clean(self):
        if not Segment.objects.filter(pk=self.cleaned_data['segment_id']).exists:
            self.errors.update({'segment_id': ['invalid segment']})
        if not Ip.check_ip(self.cleaned_data['ip']):
            self.errors.update({'ip': ['invalid ip']})


class IpFormTest(ModelForm):
    class Meta:
        model = Ip
        fields = '__all__'
        field_classes = {
            'ip_as_int': GenericIPAddressField
        }


class SegmentForm(ModelForm):
    class Meta:
        model = Segment
        fields = ['name', 'description', 'is_root_segment', 'parent_segment']

    def __init__(self, *args, **kwargs):
        super(SegmentForm, self).__init__(*args, **kwargs)
        self.fields['name'].initial = "Новый сегмент"

    def clean(self):
        if self.cleaned_data['name'] in [x.name for x in Segment.objects.all()]:
            self.errors.update({'name': ['Сегмент с таким именем уже существует']})
        parent_segment = self.cleaned_data['parent_segment']
        if self.cleaned_data['is_root_segment'] is False and parent_segment == -1:
            self.errors.update(
                {'segment_parent_segment': ['Некорневой сегмент должен быть наследованным от корневого']})
        # if parent_segment is not None and not Segment.objects.filter(pk=parent_segment).exists():
        #    self.errors.update({'parent_segment': ['Сегмент не существует']})


class RackForm(ModelForm):
    class Meta:
        model = Rack
        fields = '__all__'
