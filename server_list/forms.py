import re
from server_list import strings as st

from django import forms
from django.forms import CharField, ModelForm, GenericIPAddressField, Select

from server_list.models import Server, Rack, Room, Territory, Segment, Ip, ServerGroup
from django.db.utils import OperationalError


class ServerFormNameField(CharField):
    def validate(self, value):
        print('validate')
        return value


class ServerForm(ModelForm):
    room = forms.ModelChoiceField(label="Помещение", queryset=Room.objects.all(), required=False)
    territory = forms.ModelChoiceField(label="Территория", queryset=Territory.objects.all(), required=False)

    vm_fields_to_hide = ['unit',
                         'model',
                         'height',
                         'serial_num',
                         'territory',
                         'room',
                         'rack',
                         'location',
                         'group']
    physical_fields_to_hide = ['host_machine']

    field_order = ['hostname',
                   'purpose',
                   'is_on',
                   'is_physical',
                   'group',
                   'host_machine',
                   'os',
                   'model',
                   'specs',
                   'serial_num',
                   'sensitive_data',
                   'unit',
                   'height',
                   'location',
                   'territory',
                   'room',
                   'rack', ]

    class Meta:
        model = Server
        exclude = ('segments', 'description')
        widgets = {
            'room': Select(attrs={'pk': 'select'}),
            'territory': Select(attrs={'pk': 'select'}),
            'rack': Select(attrs={'pk': 'select'}),
            'host_machine': Select(attrs={'pk': 'select'}, choices=Server.objects.filter(is_physical=True)),
            'location': Select(attrs={'pk': 'select'}, choices=(('0', 'front'), ('1', 'back'), ('2', 'full')))
        }

        labels = {
            'hostname': st.STRING_HOSTNAME,
            'purpose': st.STRING_PURPOSE,
            'is_on': st.STRING_IS_ON,
            'is_physical': st.STRING_IS_PHYSICAL,
            'group': st.STRING_GROUP,
            'host_machine': st.STRING_HOST_MACHINE,
            'os': st.STRING_OS,
            'model': st.STRING_MODEL,
            'specs': st.STRING_SPECS,
            'serial_num': st.STRING_SN,
            'sensitive_data': st.STRING_SENSITIVE_DATA,
            'unit': st.STRING_UNIT,
            'height': st.STRING_HEIGHT,
            'location': st.STRING_LOCATION,
            'territory': st.STRING_TERRITORY,
            'room': st.STRING_ROOM,
            'rack': st.STRING_RACK,
        }

    def clean(self):
        self.cleaned_data['hostname'] = re.sub(r'\s+', ' ', self.cleaned_data['hostname'].strip())  # getting rid of double spaces
        for server in Server.objects.filter(hostname_lower=self.cleaned_data['hostname'].lower):
            if server.hostname_lower == self.cleaned_data['hostname'].lower and server != self.instance:
                self.errors.update({'hostname': ['Имя уже используется']})

        if self.cleaned_data['is_physical']:
            if self.cleaned_data['group'] is None:
                self.errors.update({'group': ['Укажите группу']})
            if self.cleaned_data['rack'] is None:
                self.errors.update({'rack': ['Укажите стойку']})
                return
            if self.cleaned_data['unit'] is None or self.cleaned_data['height'] is None or self.cleaned_data['unit'] <= 0 or self.cleaned_data['height'] <= 0:
                self.errors.update({'unit': ['Ошибка']})
                return
            this_unit_low = self.cleaned_data['unit']
            this_unit_high = this_unit_low + self.cleaned_data['height'] - 1
            this_location = int(self.cleaned_data['location'])
            rack = self.cleaned_data['rack']
            if this_unit_high > rack.size or this_unit_low <= 0:
                self.errors.update({'unit': ['расположение сервера выходит за размеры стойки']})
            for check_s in rack.server_set.all():
                if self.instance.id is not None and check_s.id == self.instance.id:
                    continue
                check_s_unit_low = check_s.unit
                check_s_unit_high = check_s_unit_low + check_s.height - 1
                check_s_location = check_s.location
                if (check_s_location == this_location or check_s_location == 2 or this_location == 2) \
                        and ((check_s_unit_low <= this_unit_low <= check_s_unit_high or check_s_unit_low <= this_unit_high <= check_s_unit_high)
                             or (this_unit_low < check_s_unit_low and this_unit_high > check_s_unit_high)):
                    self.errors.update({'unit': ['unit already in use by ' + check_s.hostname + '; units: ' + check_s.get_unit_string() + Server.locations.get(check_s.location)]})
        else:
            if self.cleaned_data['host_machine'] is None:
                self.errors.update({'host_machine': ['Это поле не должно быть пустым']})

    def __init__(self, *args, **kwargs):

        super(ServerForm, self).__init__(*args, **kwargs)
        if self.instance.rack is not None:
            print('kek')


class ServerFormOld(forms.Form):
    field_order = ['server_name',
                   'server_purpose',
                   'server_group',
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
    server_group = forms.ModelChoiceField(label="Группа", required=False, queryset=ServerGroup.objects.all(), initial=ServerGroup.objects.first())
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
    vm_fields_to_hide = ['server_unit', 'server_model', 'server_height', 'server_serial_number', 'server_territory', 'server_room', 'server_rack', 'server_location', 'server_group']
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
            if self.cleaned_data['server_group'] is None:
                self.errors.update({'server_group': ['Это поле не должно быть пустым']})
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
        else:
            if self.cleaned_data['host_machine'] is None:
                self.errors.update({'host_machine': ['Это поле не должно быть пустым']})

    def __init__(self, *args, **kwargs):
        self.server_id = kwargs.pop('server_id', None)
        self.new = kwargs.pop('new_server', False)
        super(ServerFormOld, self).__init__(*args, **kwargs)
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


class GroupForm(ModelForm):
    class Meta:
        model = ServerGroup
        fields = '__all__'

    def clean(self):
        for group in ServerGroup.objects.filter(name=self.cleaned_data['name']):
            if group.name == self.cleaned_data['name'] and group != self.instance:
                self.errors.update({'name': ['группа с таким именем уже существует']})


class IpFormTest(ModelForm):
    class Meta:
        model = Ip
        fields = ['segment', 'ip_as_string', 'server']
        widgets = {'server': forms.HiddenInput()}

    def clean(self):
        # if not Segment.objects.filter(pk=self.cleaned_data['segment_id']).exists:
        #    self.errors.update({'segment_id': ['invalid segment']})
        # inst = self.save(commit=False)
        for ip in Ip.objects.filter(ip_as_string=self.cleaned_data['ip_as_string']):
            if (not ip.ip_as_string == self.cleaned_data['ip_as_string']) or (self.cleaned_data['server'] == ip.server and ip.segment == self.cleaned_data['segment']):
                self.errors.update({'ip_as_string': ['данный ip уже существует']})
        if not Ip.check_ip(self.cleaned_data['ip_as_string']):
            self.errors.update({'ip_as_string': ['invalid ip']})


class SegmentForm(ModelForm):
    class Meta:
        model = Segment
        fields = ['name', 'description', 'is_root_segment', 'parent_segment']

    def __init__(self, *args, **kwargs):
        super(SegmentForm, self).__init__(*args, **kwargs)
        self.fields['name'].initial = "Новый сегмент"

    def clean(self):
        for seg in Segment.objects.filter(name=self.cleaned_data['name']):
            if seg.name == self.cleaned_data['name'] and seg != self.instance:
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
