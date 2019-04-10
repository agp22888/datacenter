import re

from django import forms
from django.forms import CharField, ModelForm, GenericIPAddressField

from server_list.models import Server, Rack, Room, Territory, Segment, Ip
from django.db.utils import OperationalError


# todo сделать отображение виртуалок физического сервера на странице редактирования // нужно ли?

class ServerFormNameField(CharField):
    def validate(self, value):
        print('validate')
        return value


class ServerFormTest(ModelForm):
    class Meta:
        model = Server
        fields = '__all__'


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
                   'server_territory',
                   'server_room',
                   'server_rack', ]
    server_name = ServerFormNameField(label="Имя", required=True, initial="Новый сервер")
    server_purpose = forms.CharField(label="Назначение", required=False)
    power_state = forms.BooleanField(label="Питание", required=False, initial=True)
    is_physical = forms.BooleanField(label="Физический сервер", required=False, initial=True)
    server_os = forms.CharField(label="Операционная система", required=False)
    sensitive_data = forms.CharField(label="Учётные данные", required=False)
    # try:
    host_machine = forms.ModelChoiceField(label="Физический сервер", required=False, queryset=Server.objects.filter(is_physical=True), to_field_name='hostname')
    server_territory = forms.ModelChoiceField(label="Территория", required=False, queryset=Territory.objects.all())
    server_room = forms.ModelChoiceField(label='Помещение', required=False, queryset=Room.objects.all())
    server_rack = forms.ModelChoiceField(label='Стойка', required=False, queryset=Rack.objects.all())

    # except OperationalError:
    #     print("operational error")
    #     pass
    server_unit = forms.IntegerField(label="Юнит", required=False)
    server_height = forms.IntegerField(label="Высота в юнитах", required=False)
    server_model = forms.CharField(label="Модель", required=False)
    server_specs = forms.CharField(label="Характеристики", required=False)
    server_serial_number = forms.CharField(label="Серийный номер", required=False)
    server_location = forms.ChoiceField(label='Расположение в стойке', required=False,
                                        choices=[(i, n) for i, n in Server.locations.items()])
    vm_fields_to_hide = ['server_unit', 'server_model', 'server_height', 'server_serial_number', 'server_territory', 'server_room', 'server_rack', 'server_location']
    physical_fields_to_hide = ['host_machine']

    def clean(self):
        self.cleaned_data['server_name'] = re.sub(r'\s+', ' ', self.cleaned_data['server_name'].strip())  # getting rid of double spaces
        if self.new and Server.objects.filter(hostname=self.cleaned_data['server_name']).count() > 0:
            self.errors.update({'server_name': ['Имя уже используется']})

        # if not self.cleaned_data['is_physical']:
        #     if self.cleaned_data['host_machine'] == self.server_id:
        #         self.errors.update({'host_machine': ['Виртуальная машина не может хоститься сама на себе!']})
        # for field in self.fields:
        #     if 'ip_' in field:
        #         data = self.cleaned_data[field]
        #         if not Ip.check_ip(data):
        #             self.errors.update({field: ['invalid ip']})

        if self.cleaned_data['is_physical']:
            if self.cleaned_data['server_unit'] is None or self.cleaned_data['server_height'] is None or self.cleaned_data['server_unit'] <= 0 or self.cleaned_data['server_height'] <= 0:
                self.errors.update({'server_unit': ['Error']})
                return
            this_unit_low = self.cleaned_data['server_unit']
            this_unit_high = this_unit_low + self.cleaned_data['server_height'] - 1
            this_location = int(self.cleaned_data['server_location'])
            rack = self.cleaned_data['server_rack']
            if this_unit_high > rack.size or this_unit_low <= 0:
                self.errors.update({'server_unit': ['расположение сервера выходит за размеры стойки']})
            for check_s in rack.server_set.all():
                if self.server_id is not None and check_s.id == int(self.server_id):
                    continue
                check_s_unit_low = check_s.unit
                check_s_unit_high = check_s_unit_low + check_s.height - 1
                check_s_location = check_s.location
                print('server location is', self.cleaned_data['server_location'], check_s_location)

                if (check_s_location == this_location or check_s_location == 2 or this_location == 2) \
                        and ((check_s_unit_low <= this_unit_low <= check_s_unit_high or check_s_unit_low <= this_unit_high <= check_s_unit_high)
                             or (this_unit_low < check_s_unit_low and this_unit_high > check_s_unit_high)):
                    self.errors.update({'server_unit': [
                        'unit already in use by ' + check_s.hostname + '; units: ' +
                        check_s.get_unit_string() + Server.locations.get(check_s.location)]})
                    # todo добавить ссылку на сервер, с которым идёт пересечение?

    def __init__(self, *args, **kwargs, ):
        self.server_id = kwargs.pop('server_id', None)
        self.new = kwargs.pop('new_server', False)
        super(ServerForm, self).__init__(*args, **kwargs)
        # if not self.new:
        #     ser = Server.objects.get(pk=self.server_id)
        #     for ip in ser.ip_set.all():
        #         field_name = r'ip_' + str(ip.id)
        #         self.fields[field_name] = forms.CharField(label=ip.segment.name, max_length=100)


# class IpForm(forms.Form):
#     try:
#         segment_id = forms.ChoiceField(label='Сегмент', required=False, choices=[(str(seg.id), seg.name) for seg in Segment.objects.all()])
#     except OperationalError:
#         pass
#     ip = forms.CharField(label="IP", required=True, initial="0.0.0.0")
#
#     def __init__(self, *args, **kwargs):
#         super(IpForm, self).__init__(*args, **kwargs)
#         self.fields['segment_id'] = forms.ChoiceField(label='Сегмент',
#                                                       choices=[(str(seg.id), seg.name) for seg in Segment.objects.all()])
#
#     def clean(self):
#         if not Segment.objects.filter(pk=self.cleaned_data['segment_id']).exists:
#             self.errors.update({'segment_id': ['invalid segment']})
#         if not Ip.check_ip(self.cleaned_data['ip']):
#             self.errors.update({'ip': ['invalid ip']})


class IpFormTest(ModelForm):
    class Meta:
        model = Ip
        fields = ['segment', 'ip_as_string']

    def clean(self):
        # if not Segment.objects.filter(pk=self.cleaned_data['segment_id']).exists:
        #    self.errors.update({'segment_id': ['invalid segment']})
        if not Ip.check_ip(self.cleaned_data['ip_as_string']):
            self.errors.update({'ip': ['invalid ip']})


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

    def clean(self):
        if int(self.cleaned_data['size']) <= 0:
            self.errors.update({'size': ["Неверный размер"]})
        for server in self.instance.server_set.all():
            if server.unit + server.height - 1 > self.cleaned_data['size']:
                self.errors.update(
                    {'size': ["сервер " + server.hostname + " имеет расположение, которое выходит за границы размеров стойки"]})


class RoomForm(ModelForm):
    class Meta:
        model = Room
        fields = '__all__'


class TerritoryForm(ModelForm):
    class Meta:
        model = Territory
        fields = '__all__'


class UserForm(forms.Form):
    username = forms.CharField(max_length=50)
    password = forms.CharField(max_length=30, widget=forms.PasswordInput)

    def clean(self):
        if len(self.cleaned_data['password']) < 3:
            self.errors.update({'password': ['Пароль слишком короткий']})
