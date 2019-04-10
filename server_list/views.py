import os
from itertools import chain

from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.urls import reverse, reverse_lazy

from . import utils
from django.core import serializers
from django.shortcuts import render, redirect
from server_list.models import Server, Segment, Ip, Rack, Room, Territory
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from .forms import ServerForm, IpFormTest, SegmentForm, RackForm, TerritoryForm, RoomForm, UserForm, ServerFormTest
from django.http import Http404


# Create your views here.
def proof(request):
    return HttpResponseRedirect(reverse('list'))


def server_view_all(request):
    server_list = Server.objects.filter(is_physical=True)
    return render(request, os.path.join('server_list', 'servers_all.html'), {"servers": server_list})


def servers(request):
    links = {}
    for segment in Segment.objects.filter(is_root_segment=True):
        links.update({segment.id: segment.name})
    territories = []
    target_segment = request.GET.get('segment')

    if target_segment is None:
        first = Segment.objects.filter(is_root_segment=True).first()
        if first is None:
            return HttpResponse('no segments')
        return HttpResponseRedirect(reverse('list') + '?segment=' + str(first.id))
        # return render(request, os.path.join('server_list', 'server_list.html'),{"links": links, "tabs": {}, "servers": {}})

    for server in Segment.objects.get(pk=target_segment).server_set.all():
        if not server.is_physical:
            continue
        territory = server.get_territory()
        if territory not in territories:
            territories.append(territory)
    tabs = {}  # список территорий для вкладок
    ser_dict = {}  # список серверов (список списков по территориям?)
    # {territory:{room:{rack::server_list}}}
    for t in territories:
        tabs.update({t.id: t.name})
        seg_list = Segment.objects.filter(server__in=t.get_servers(target_segment)).distinct()

        for room in t.room_set.all():
            for rack in room.rack_set.all():
                ser_list = {}
                row = ["unit", "model", "Имя", "power", "VM", "OS", "Назначение"]
                for seg in seg_list:
                    row.append(seg.name)
                row.append("s/n")
                row.append("хар-ки")
                ser_list.update({"header": row})
                for server in rack.server_set.all():
                    if not len(server.segments.filter(id=target_segment)) == 0:
                        row = [server.get_unit_string() + " " + Server.locations.get(server.location), server.model,
                               server.hostname,
                               "on" if server.is_on else "off",
                               "", server.os, server.purpose]
                        for seg in seg_list:
                            row.append([x.ip_as_string for x in list(server.ip_set.filter(segment=seg))])
                        row.append(server.serial_num)
                        row.append(server.specs)
                        ser_list.update({server.id: row})
                        for vm in server.server_set.all():
                            vm_row = ["", "", " ", "on" if vm.is_on else "off", vm.hostname, vm.os, vm.purpose]
                            for seg in seg_list:  # segment dict

                                vm_row.append(
                                    [x.ip_as_string for x in list(vm.ip_set.filter(segment=seg))])
                            vm_row.append("")
                            vm_row.append("")
                            ser_list.update({vm.id: vm_row})
                        ser_dict = utils.update(ser_dict, {t: {room: {rack: ser_list}}})
    actions = [{'link': reverse('server_view_all'), 'divider': False, 'name': 'Все серверы'},
               {'link': reverse('server_new'), 'divider': False, 'name': 'Добавить сервер'},
               {'divider': True},
               {'link': reverse('dump'), 'divider': False, 'name': 'Сохранить базу'}]
    return render(request, os.path.join('server_list', 'server_list.html'), {"links": links, "tabs": tabs, "servers": ser_dict, 'actions': actions})


@login_required(login_url=reverse_lazy('custom_login'))
def server_edit(request, server_id):
    try:
        server = Server.objects.get(id=server_id)
    except Server.DoesNotExist:
        raise Http404("No server found")

    if request.method == 'POST':
        form = ServerForm(request.POST, server_id=server_id)
        if not form.is_valid():
            return render(request, os.path.join('server_list', 'server_edit.html'), {'form': form})
        else:
            server.hostname = form.cleaned_data['server_name']
            server.is_on = form.cleaned_data['power_state']
            server.purpose = form.cleaned_data['server_purpose']
            server.sensitive_data = form.cleaned_data['sensitive_data']
            server.os = form.cleaned_data['server_os']
            server.is_physical = form.cleaned_data['is_physical']
            if form.cleaned_data['is_physical']:
                server.unit = form.cleaned_data['server_unit']  #
                server.height = form.cleaned_data['server_height']  #
                server.model = form.cleaned_data['server_model']  #
                server.specs = form.cleaned_data['server_specs']  #
                server.serial_num = form.cleaned_data['server_serial_number']  #
                server.rack = form.cleaned_data['server_rack']
                server.host_machine = None
            else:
                server.unit = 0
                server.height = 0
                server.location = None
                server.model = ''
                server.specs = ''
                server.serial_num = ''
                server.rack = None
                server.host_machine = form.cleaned_data['host_machine']

            for seg in (x for x in form.cleaned_data if 'ip_' in x):
                num = int(seg.split('_')[1])
                server.ip_set.get(pk=num).ip_as_int = Ip.get_ip_from_string(form.cleaned_data[seg])

            server.save()
        return redirect('server_view', server_id=server.id)

    elif request.method == 'GET':
        form_dict = {'server_name': server.hostname,
                     'power_state': server.is_on,
                     'server_unit': server.unit if server.unit is not None else -1,
                     'server_height': server.height,
                     'server_model': server.model,
                     'server_os': server.os,
                     'server_specs': server.specs,
                     'server_serial_number': server.serial_num,
                     'server_purpose': server.purpose,
                     'sensitive_data': server.sensitive_data,
                     'is_physical': server.is_physical,
                     }
        # for ip in server.ip_set.all():
        #    form_dict.update({'ip_' + str(ip.id): ip.ip_as_string})
        if server.is_physical:
            rack = server.rack
            room = rack.room
            form_dict.update({'server_location': server.location,
                              'server_territory': room.territory.id,
                              'server_room': room.id,
                              'server_rack': rack.id})
        else:
            form_dict.update({'host_machine': server.host_machine})
        form = ServerForm(form_dict, server_id=server_id)
        # form = ServerFormTest(instance=server)

        return render(request, os.path.join('server_list', 'server_edit.html'), {'form': form})


@login_required(login_url=reverse_lazy('custom_login'))
def server_new(request):
    if request.method == 'GET':
        form = ServerForm(new_server=True)
        return render(request, os.path.join('server_list', 'server_edit.html'), {'form': form})
    elif request.method == 'POST':
        form = ServerForm(request.POST, new_server=True)
        if form.is_valid():
            s = Server()
            s.hostname = form.cleaned_data['server_name']

            s.purpose = form.cleaned_data['server_purpose']
            s.is_on = form.cleaned_data['power_state']
            s.is_physical = form.cleaned_data['is_physical']
            s.os = form.cleaned_data['server_os']
            s.sensitive_data = form.cleaned_data['sensitive_data']
            if s.is_physical:
                s.model = form.cleaned_data['server_model']
                s.specs = form.cleaned_data['server_specs']
                s.serial_num = form.cleaned_data['server_serial_number']
                s.unit = form.cleaned_data['server_unit']
                s.height = form.cleaned_data['server_height']
                s.location = form.cleaned_data['server_location']
                s.rack = form.cleaned_data['server_rack']
            else:
                s.host_machine = form.cleaned_data['host_machine']
            s.save()
            return redirect("server_view", s.id)
        else:
            print("not valid")
            print("bound", form.is_bound)
            return render(request, os.path.join('server_list', 'server_edit.html'), {'form': form})


@login_required(login_url=reverse_lazy('custom_login'))
def ip_edit(request, ip_id):
    try:
        ip = Ip.objects.get(pk=ip_id)
    except Ip.DoesNotExist:
        raise Http404("IP not found")
    if request.method == 'GET':
        # data = {'segment_id': ip.segment.id,
        #        'ip': ip.__str__()}
        form = IpFormTest(instance=ip)
        return render(request, os.path.join('server_list', 'ip_edit.html'), {'form': form})
    elif request.method == 'POST':
        form = IpFormTest(request.POST)
        if form.is_valid():
            ip.ip_as_string = form.cleaned_data['ip_as_string']
            ip.segment = form.cleaned_data['segment']
            ip.save()
            return HttpResponse("<script>window.close()</script>")
        else:
            return render(request, os.path.join('server_list', 'ip_edit.html'), {'form': form})


@login_required(login_url=reverse_lazy('custom_login'))
def ip_new(request, server_id):
    try:
        server = Server.objects.get(pk=server_id)
    except Server.DoesNotExist:
        raise Http404("Server not found")
    if request.method == 'GET':
        return render(request, os.path.join('server_list', 'ip_edit.html'), {'form': IpFormTest()})
    elif request.method == 'POST':
        form = IpFormTest(request.POST)
        if form.is_valid():
            ip = Ip()
            # ip.ip_as_int = Ip.get_ip_from_string(form.cleaned_data['ip'])
            ip.segment = form.cleaned_data['segment']
            ip.ip_as_string = form.cleaned_data['ip_as_string']
            ip.mask_as_int = 0
            ip.gateway_as_int = 0
            ip.server = server
            ip.save()
            return HttpResponse("<script>window.close()</script>")
        else:
            return render(request, os.path.join('server_list', 'ip_edit.html'), {'form': form})


@login_required(login_url=reverse_lazy('custom_login'))
def segment_new(request):
    if request.method == 'GET':
        form = SegmentForm()
        return render(request, os.path.join('server_list', 'segment_edit.html'), {'form': form})
    if request.method == 'POST':
        form = SegmentForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponse("<script>window.close()</script>")
        else:
            return render(request, os.path.join('server_list', 'segment_edit.html'), {'form': form})


@login_required(login_url=reverse_lazy('custom_login'))
def segment_edit(request, segment_id):
    if request.method == 'GET':
        try:
            form = SegmentForm(instance=Segment.objects.get(pk=segment_id))
        except Segment.DoesNotExist:
            raise Http404("No segment found")
        return render(request, os.path.join('server_list', 'segment_edit.html'), {'form': form})
    if request.method == 'POST':
        form = SegmentForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponse("<script>window.close()</script>")
        else:
            return render(request, os.path.join('server_list', 'segment_edit.html'), {'form': form})

    return None


def rack_view(request, rack_id):
    try:
        rack = Rack.objects.get(pk=rack_id)
    except Rack.DoesNotExist:
        raise Http404("No rack found")
    rack_front = {}
    rack_back = {}
    for s in rack.server_set.all():
        units = [s.unit, s.height]
        if s.location != 0:
            rack_front.update({s: units})
        if s.location != 1:
            rack_back.update({s: units})
    return render(request, os.path.join('server_list', 'rack_view.html'), {'rack': rack, 'front': rack_front, 'back': rack_back})


@login_required(login_url=reverse_lazy('custom_login'))
def rack_edit(request, rack_id):
    print('post', request.POST.get('close'))
    print('get', request.GET.get('close'))
    try:
        rack = Rack.objects.get(pk=rack_id)
    except Rack.DoesNotExists:
        raise Http404("No rack found")
    if request.method == 'GET':
        form = RackForm(instance=rack)
        return render(request, os.path.join('server_list', 'rack_edit.html'), {'form': form})
    if request.method == 'POST':
        print(request.POST)
        form = RackForm(request.POST, instance=rack)
        if form.is_valid():
            form.save()
            if request.GET.get('close') == 'True':
                return HttpResponse("<script>window.close()</script>")
            return redirect('rack_view', rack_id)
        else:
            return render(request, os.path.join('server_list', 'rack_edit.html'), {'form': form})

    return HttpResponse('ok')


def server_view(request, server_id):
    try:
        server = Server.objects.get(pk=server_id)
    except Server.DoesNotExist:
        raise Http404("No server found")
    ip_list = []
    for ip in server.ip_set.all():
        ip_list.append((ip.segment.name, ip.ip_as_string, ip.id))
    data_dict = {"server_id": server_id,
                 "model": server.model,
                 "hostname": server.hostname,
                 "power_state": server.is_on,
                 "os": server.os,
                 "purpose": server.purpose,
                 "ip_list": ip_list,
                 "serial_number": server.serial_num,
                 "specs": server.specs,
                 "root_ip_list": (server.ip_set.filter(segment__is_root_segment=True)),
                 }
    if server.is_physical:
        rack = server.rack
        room = rack.room
        territory = room.territory
        data_dict.update({"is_physical": True,
                          "unit": server.get_unit_string(),
                          "territory": territory,
                          "room": room,
                          "rack": rack,
                          "vm_list": server.server_set.all()})
    else:
        data_dict.update({"is_physical": False,
                          "host_machine": server.host_machine.hostname,
                          "host_machine_id": server.host_machine.id,
                          })

    return render(request, os.path.join('server_list', 'server_view.html'), {'server_dict': data_dict})


def ajax(request):  # todo добавить верификацию юзера
    print('test, requested: ', request.GET.get('model'))
    if request.GET.get('model') == 'territory':
        return HttpResponse(serializers.serialize('json', Territory.objects.all(), fields='name'), content_type='application/json')
    if request.GET.get('model') == 'room':
        ter = request.GET.get('territory')
        if ter is None:
            ter = 1
            print("ajax request ter is None")
        return HttpResponse(
            serializers.serialize('json', Room.objects.filter(territory=Territory.objects.get(pk=int(ter))), fields='name'), content_type='application/json')
    if request.GET.get('model') == 'rack':
        room = request.GET.get('room')
        if room is None:
            print("ajax request room is None")
            room = 1
        return HttpResponse(
            serializers.serialize('json', Rack.objects.filter(room=Room.objects.get(pk=int(room))), fields='name'), content_type='application/json')
    if request.GET.get('model') == 'server':
        if request.user.is_authenticated:
            try:
                ser = Server.objects.get(pk=int(request.GET.get('server_id')))
                return HttpResponse(ser.sensitive_data + ' ')
            except Server.DoesNotExist:
                raise Http404
            except ValueError:
                return HttpResponse('500')
        else:
            return HttpResponse('Access Denied')
    if request.GET.get('model') == 'vm':
        return HttpResponse(
            serializers.serialize('json', Server.objects.filter(is_physical=True), fields=('pk', 'hostname')), content_type='application/json')
    if request.GET.get('action') == 'delete_ip':
        ip_id = request.GET.get('ip_id')
        try:
            ip = Ip.objects.get(pk=ip_id)
            ip.delete()
        except Ip.DoesNotExist:
            raise Http404
        return HttpResponse('ok')
    if request.GET.get('action') == 'search':
        search_query = request.GET.get('query')
        # print('search query', "'" + search_query + "'")
        # pattern = r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.?){0,2}(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)?)$'
        # if re.match(pattern, search_query):
        #     matching_ips = []
        #     # todo проверить не находится ли уже ip в списке
        #     for ip in Ip.objects.filter(ip_as_string__contains=search_query):
        #         matching_ips.append({'pk': ip.id, 'fields': {'ip': Ip.get_string_ip(ip.ip_as_int)}, 'model': 'server_list.ip'})
        #     print(matching_ips)
        #     return HttpResponse(json.dumps(matching_ips))
        #
        # sers = serializers.serialize('json', Server.objects.filter(hostname__contains=search_query), fields=('pk', 'hostname'))

        query_set = Server.objects.filter(hostname__icontains=search_query)
        query_set |= Server.objects.filter(
            purpose__icontains=search_query)  # todo icontains doesn't work with russian text https://stackoverflow.com/questions/47946879/how-to-search-text-containing-non-ascii-characters-with-django-icontains-query#47954143
        query_set |= Server.objects.filter(ip__ip_as_string__contains=search_query)
        query_set.distinct()
        print(query_set)
        # print(filt.count())
        serialize = serializers.serialize('json', query_set, fields=('pk', 'hostname', 'ip'))
        # print(serialize)
        return HttpResponse(
            serialize,
            content_type='application/json')

    return None


# todo по закрытию окна редактирования вместо перезагрузки страницы, перезагрузить списки
def segment_view():
    return None


@login_required(login_url=reverse_lazy('custom_login'))
def room_edit(request, room_id):
    try:
        room = Room.objects.get(pk=room_id)
    except Room.DoesNotExists:
        raise Http404("No rack found")
    if request.method == 'GET':
        form = RoomForm(instance=room)
        return render(request, os.path.join('server_list', 'room_edit.html'), {'form': form})
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            if request.GET.get('close') == 'True':
                return HttpResponse("<script>window.close()</script>")
            return redirect('room_view', room_id)
        else:
            return render(request, os.path.join('server_list', 'room_edit.html'), {'form': form})
    return HttpResponse('ok')


def room_view(request, room_id):
    try:
        room = Room.objects.get(pk=room_id)
    except Room.DoesntExist:
        raise Http404
    racks = {}
    for rack in room.rack_set.all():
        racks.update({rack.id: rack.name})
    return render(request, os.path.join('server_list', 'room_view.html'), {'room': room, 'racks': racks})


def territory_view(request, territory_id):
    try:
        territory = Territory.objects.get(pk=territory_id)
    except Territory.DoesntExist:
        raise Http404
    rooms = {}
    for room in territory.room_set.all():
        rooms.update({room.id: room.name})
    return render(request, os.path.join('server_list', 'territory_view.html'), {'territory': territory, 'rooms': rooms})


@login_required(login_url=reverse_lazy('custom_login'))
def territory_edit(request, territory_id):
    try:
        territory = Territory.objects.get(pk=territory_id)
    except Room.DoesNotExists:
        raise Http404("No rack found")
    if request.method == 'GET':
        form = TerritoryForm(instance=territory)
        return render(request, os.path.join('server_list', 'territory_edit.html'), {'form': form})
    if request.method == 'POST':
        form = TerritoryForm(request.POST, instance=territory)
        if form.is_valid():
            form.save()
            if request.GET.get('close') == 'True':
                return HttpResponse("<script>window.close()</script>")
            return redirect('territory_view', territory_id)
        else:
            return render(request, os.path.join('server_list', 'territory_edit.html'), {'form': form})
    return HttpResponse('ok')


@login_required(login_url=reverse_lazy('custom_login'))
def test(request):
    # f = open(os.path.join('server_list', 'templates', 'server_list', 'test.html'), 'r')
    # my_file = File(f)
    fmt = 'xml'
    qs_room = Room.objects.all()
    qs_territory = Territory.objects.all()
    qs_rack = Rack.objects.all()
    qs_segment = Segment.objects.all()
    qs_server = Server.objects.all()
    qs_ip = Ip.objects.all()
    qs_combined = list(chain(qs_room, qs_territory, qs_rack, qs_segment, qs_server, qs_ip))
    ser = serializers.serialize(fmt, qs_combined)
    # s = ''
    # s += serializers.serialize('json', Ip.objects.all())
    # s += serializers.serialize('json', Server.objects.all())
    d = serializers.deserialize(fmt, ser)
    for obj in d:
        print(obj)
    response = HttpResponse(ser, content_type='application/plain-text')
    response['Content-Disposition'] = 'attachment; filename=backup_base.' + fmt
    # return HttpResponse('ok')
    return response
    # return render(request, os.path.join('server_list', 'test.html'))


@login_required(login_url=reverse_lazy('custom_login'))
def dump(request):
    fmt = 'xml'
    qs_room = Room.objects.all()
    qs_territory = Territory.objects.all()
    qs_rack = Rack.objects.all()
    qs_segment = Segment.objects.all()
    qs_server = Server.objects.all()
    qs_ip = Ip.objects.all()
    qs_combined = list(chain(qs_room, qs_territory, qs_rack, qs_segment, qs_server, qs_ip))
    ser = serializers.serialize(fmt, qs_combined)
    # d = serializers.deserialize(fmt, ser)
    # for obj in d:
    #     print(obj)
    response = HttpResponse(ser, content_type='application/plain-text')
    response['Content-Disposition'] = 'attachment; filename=backup_base.' + fmt
    return response


def search(request):
    if request.method == 'GET':
        print("GET")
        return HttpResponseBadRequest("400")
    if request.method == 'POST':
        print(request)
        return HttpResponse(request.POST.items())
    return HttpResponse('search')


def custom_logout(request):
    logout(request)
    return redirect(request.GET.get('next'))


def custom_login(request):
    redirect_to = request.GET.get('next')
    if request.method == 'GET':
        form = UserForm()
        return render(request, os.path.join('server_list', 'login.html'), {'form': form})
    elif request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return HttpResponseRedirect(redirect_to if redirect_to is not None else reverse('list'))
            else:
                form.add_error(None, 'Пользователь не существует')
            return render(request, os.path.join('server_list', 'login.html'), {'form': form})
        else:
            return render(request, os.path.join('server_list', 'login.html'), {'form': form})
    return HttpResponse('login')


@login_required(login_url=reverse_lazy('custom_login'))
def rack_new(request):
    if request.method == 'GET':
        form = RackForm()
        return render(request, os.path.join('server_list', 'rack_edit.html'), {'form': form})
    if request.method == 'POST':
        form = RackForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponse("<script>window.close()</script>")
        else:
            return render(request, os.path.join('server_list', 'rack_edit.html'), {'form': form})


@login_required(login_url=reverse_lazy('custom_login'))
def room_new(request):
    if request.method == 'GET':
        form = RoomForm()
        return render(request, os.path.join('server_list', 'room_edit.html'), {'form': form})
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponse("<script>window.close()</script>")
        else:
            return render(request, os.path.join('server_list', 'room_edit.html'), {'form': form})


@login_required(login_url=reverse_lazy('custom_login'))
def territory_new(request):
    if request.method == 'GET':
        form = TerritoryForm()
        return render(request, os.path.join('server_list', 'territory_edit.html'), {'form': form})
    if request.method == 'POST':
        form = TerritoryForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponse("<script>window.close()</script>")
        else:
            return render(request, os.path.join('server_list', 'territory_edit.html'), {'form': form})
