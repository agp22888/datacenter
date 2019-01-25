import collections, os

from django.core import serializers
from django.shortcuts import render, get_object_or_404
from server_list.models import Server, Segment, Ip, Rack, Room, Territory
from django.http import HttpResponse
from .forms import ServerForm
from django.http import Http404


# Create your views here.
def proof(request):
    # output = '<head><style>table{font-family: arial, sans-serif;border-collapse: collapse;width: 100%;}td, th {border: 1px solid #dddddd;text-align: left;padding: 8px;}tr:nth-child(even) {background-color: #dddddd;}</style></head><table>'
    # output += '<tr><td>Unit</td><td>Модель</td><td>Имя</td><td>Power state</td><td>Virtual machine</td><td>OS</td><td>Назначение</td><td>Ip адрес</td><td>Маска/шлюз</td><td>Ilo</td><td>s/n</td><td>Характеристики</td>'
    # for p_host in Server.objects.filter(is_physical=True):
    #     name = p_host.hostname
    #     unit = "10 h"
    #     model = p_host.model
    #     power_state = 'On' if p_host.is_on else 'Off'
    #     os = p_host.os
    #     purpose = p_host.purpose
    #     s = Segment.objects.get(id=1)
    #     s_man = Segment.objects.get(id=2)
    #     ip = str(p_host.ip_set.get(segment=s))
    #     mask = '255.255.255.0 h'
    #     ilo_ip = str(p_host.ip_set.get(segment=s_man))
    #     ser_num = p_host.serial_num
    #     specs = p_host.specs
    #     output += '<tr><td>' + unit + '</td><td>' + model + '</td><td>' + name + '</td><td>' + power_state + '</td><td> </td><td>' + os + '</td><td>' + purpose + '</td><td>' + ip + '</td><td>' + mask + '</td><td>' + ilo_ip + '</td><td>' + ser_num + ' </td><td>' + specs + '</td></tr>'
    #     for v_host in p_host.server_set.all():
    #         name = v_host.hostname
    #         unit = ' '
    #         model = " "
    #         power_state = 'On' if v_host.is_on else 'Off'
    #         os = v_host.os
    #         purpose = v_host.purpose
    #         s = Segment.objects.get(id=1)
    #         ip = str(p_host.ip_set.get(segment=s))
    #         mask = '255.255.255.0 h'
    #         ilo_ip = " "
    #         ser_num = " "
    #         specs = " "
    #         output += '<tr><td>' + unit + '</td><td>' + model + '</td><td> </td><td>' + power_state + '</td><td>' + name + '</td><td>' + os + '</td><td>' + purpose + '</td><td>' + ip + '</td><td>' + mask + '</td><td>' + ilo_ip + '</td><td>' + ser_num + ' </td><td>' + specs + '</td></tr>'
    return HttpResponse('blank')


def servers(request):
    links = {}  # список сегментов для ссылок
    territories = []
    target_segment = request.GET.get('segment')
    for server in Segment.objects.filter(is_root_segment=True):
        links.update({server.id: server.name})
    if target_segment is None:
        return render(request, os.path.join('server_list', 'server_list.html'),
                      {"links": links, "tabs": {}, "servers": {}})
    for server in Segment.objects.get(pk=target_segment).server_set.all():
        if not server.is_physical:
            continue
        territory = server.get_territory()
        if territory not in territories:
            territories.append(territory)
    tabs = []  # список территорий для вкладок
    ser_dict = {}  # список серверов (список списков по территориям?)
    # {territory:{room:{rack::server_list}}}

    for t in territories:
        tabs.append(t.name)
        seg_list = Segment.objects.filter(server__in=t.get_servers(target_segment)).distinct()

        for room in t.room_set.all():
            for rack in room.rack_set.all():
                ser_list = {}
                row = ["unit", "model", "Имя", "power", "VM", "OS", "Назначение"]
                for seg in seg_list:
                    row.append(seg)
                row.append("s/n")
                row.append("хар-ки")
                # row.append("учётные данные")
                ser_list.update({-1: row})
                for server in rack.server_set.all():
                    if not len(server.segments.filter(id=target_segment)) == 0:
                        row = [server.get_unit_string(), server.model, server.hostname, get_power_state(server.is_on),
                               "", server.os, server.purpose]
                        for seg in seg_list:  # segment dict
                            try:
                                ip = server.ip_set.get(segment=seg)
                            except Ip.DoesNotExist:
                                ip = ""
                            row.append(ip)
                        row.append(server.serial_num)
                        row.append(server.specs)
                        # row.append(server.sensitive_data)
                        #  <!-- Unit Модель Имя Питание VM OS Назначение IP Mask/Gateway ilo iscsi port s/n specs sens-->
                        ser_list.update({server.id: row})
                        for vm in server.server_set.all():
                            vm_row = ["", "", " ", get_power_state(vm.is_on), vm.hostname, vm.os, vm.purpose]
                            for seg in seg_list:  # segment dict
                                try:
                                    ip = vm.ip_set.get(segment=seg)
                                except Ip.DoesNotExist:
                                    ip = ""
                                vm_row.append(ip)
                            vm_row.append("")
                            vm_row.append("")
                            # vm_row.append(vm.sensitive_data)
                            ser_list.update({vm.id: vm_row})
                        ser_dict = update(ser_dict, {t: {room: {rack: ser_list}}})

    return render(request, os.path.join('server_list', 'server_list.html'),
                  {"links": links, "tabs": tabs, "servers": ser_dict})


def edit(request, server_id):
    try:
        server = Server.objects.get(id=server_id)
    except Server.DoesNotExist:
        raise Http404("No server found")

    if request.method == 'POST':
        print('POST', request.POST.get('server_name'))
        form = ServerForm(request.POST, server_id=server_id, user_auth=request.user.is_authenticated)
        print("form.is_valid()", form.is_valid())
        if not form.is_valid():
            return render(request, os.path.join('server_list', 'server_edit.html'), {'form': form})
        else:
            for field in form.cleaned_data:
                print(field, form.cleaned_data[field])
            return HttpResponse('!')

    elif request.method == 'GET':
        form_dict = {'server_name': server.hostname,
                     'power_state': server.is_on,
                     'server_unit': server.unit if server.unit is not None else -1,
                     'server_height': server.height,
                     'server_model': server.model,
                     'server_specs': server.specs,
                     'server_serial_number': server.serial_num,
                     'server_purpose': server.purpose,
                     'sensitive_data': server.sensitive_data,
                     'is_physical': server.is_physical,
                     }
        for ip in server.ip_set.all():
            form_dict.update({'segment_' + str(ip.segment.id): ip.get_string_ip()})
        if server.is_physical:
            rack = server.rack
            room = rack.room
            form_dict.update({'server_territory': room.territory.id,
                              'server_room': room.id,
                              'server_rack': rack.id})
        form = ServerForm(form_dict, server_id=server_id, user_auth=request.user.is_authenticated)
        return render(request, os.path.join('server_list', 'server_edit.html'), {'form': form})


def new(request):
    server = Server()  # todo if request.method.get request.method.post
    server_id = max(Server.objects.all().values_list('id', flat=True)) + 1
    if request.method == 'GET':

        data_dict = {'server_name': 'New server',
                     'power_state': True,
                     'is_physical': True}
        form = ServerForm(data_dict, server_id=server_id, new_server=True)
        return render(request, os.path.join('server_list', 'server_edit.html'), {'form': form})
    elif request.method == 'POST':
        form = ServerForm(request.POST, server_id=server_id, new_server=True)
        if form.is_valid():
            return HttpResponse("OK")
        else:
            print("not valid")
            print("bound", form.is_bound)
            return render(request, os.path.join('server_list', 'server_edit.html'), {'form': form})


def view(request, server_id):
    try:
        server = Server.objects.get(pk=server_id)
    except Server.DoesNotExist:
        raise Http404("No server found")
    ip_list = []
    for ip in server.ip_set.all():
        ip_list.append((ip.segment.name, ip.get_string_ip()))
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


def test_ajax(request):
    print('test, requested: ', request.GET.get('model'))
    if request.GET.get('model') == 'territory':
        return HttpResponse(serializers.serialize('json', Territory.objects.all(), fields='name'),
                            content_type='application/json')
    if request.GET.get('model') == 'room':
        ter = request.GET.get('territory')
        if ter is None:
            ter = 1
            print("ajax request ter is None")
        return HttpResponse(
            serializers.serialize('json', Room.objects.filter(territory=Territory.objects.get(pk=int(ter))),
                                  fields='name'), content_type='application/json')
    if request.GET.get('model') == 'rack':
        room = request.GET.get('room')
        if room is None:
            print("ajax request room is None")
            room = 1
        return HttpResponse(
            serializers.serialize('json', Rack.objects.filter(room=Room.objects.get(pk=int(room))), fields='name'),
            content_type='application/json')
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
    response = HttpResponse(serializers.serialize('json', Server.objects.all(), fields=('pk', 'hostname', 'purpose')),
                            content_type='application/json')
    return response


def update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            d[k] = update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def get_power_state(server_is_on):
    return "on" if server_is_on else "off"
