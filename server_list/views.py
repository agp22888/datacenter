import collections, os

from django.core import serializers
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect
from server_list.models import Server, Segment, Ip, Rack, Room, Territory
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from .forms import ServerForm, IpForm, SegmentForm
from django.http import Http404


# Create your views here.
def proof(request):
    return HttpResponse('blank')


def server_view_all(request):
    server_list = Server.objects.filter(is_physical=True).filter(ip__segment__is_root_segment=True)
    return render(request, os.path.join('server_list', 'servers_all.html'), {"servers": server_list})


def servers(request):
    links = {}
    for segment in Segment.objects.filter(is_root_segment=True):
        links.update({segment.id: segment.name})
    territories = []
    target_segment = request.GET.get('segment')

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
                        row = [server.get_unit_string(), server.model, server.hostname,
                               get_power_state(server.is_on),
                               "", server.os, server.purpose]
                        for seg in seg_list:  # segment dict
                            # ip_str = ''
                            # new_line = ''
                            # for ip in server.ip_set.filter(segment=seg):  # todo много ip в одном сегменте
                            #     ip_str += new_line + Ip.get_string_ip(ip.ip_as_int)
                            #     new_line = '\n'
                            # row.append(ip_str)

                            row.append([Ip.get_string_ip(x.ip_as_int) for x in list(server.ip_set.filter(segment=seg))])
                        row.append(server.serial_num)
                        row.append(server.specs)
                        # row.append(server.sensitive_data)
                        #  <!-- Unit Модель Имя Питание VM OS Назначение IP Mask/Gateway ilo iscsi port s/n specs sens-->
                        ser_list.update({server.id: row})
                        for vm in server.server_set.all():
                            vm_row = ["", "", " ", get_power_state(vm.is_on), vm.hostname, vm.os, vm.purpose]
                            for seg in seg_list:  # segment dict

                                vm_row.append(
                                    [Ip.get_string_ip(x.ip_as_int) for x in list(vm.ip_set.filter(segment=seg))])
                            vm_row.append("")
                            vm_row.append("")
                            # vm_row.append(vm.sensitive_data)
                            ser_list.update({vm.id: vm_row})
                        ser_dict = update(ser_dict, {t: {room: {rack: ser_list}}})

    return render(request, os.path.join('server_list', 'server_list.html'),
                  {"links": links, "tabs": tabs, "servers": ser_dict})


def server_edit(request, server_id):
    print('user_auth', request.user.is_authenticated)
    if not request.user.is_authenticated:
        return HttpResponseForbidden()
    try:
        server = Server.objects.get(id=server_id)
    except Server.DoesNotExist:
        raise Http404("No server found")

    if request.method == 'POST':
        print('POST', request.POST.get('server_name'))
        form = ServerForm(request.POST, server_id=server_id)
        print("form.is_valid()", form.is_valid())
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
                server.rack = Rack.objects.get(pk=form.cleaned_data['server_rack'])
                server.host_machine = None
            else:
                server.unit = 0
                server.height = 0
                server.model = ''
                server.specs = ''
                server.serial_num = ''
                server.rack = None
                server.host_machine = Server.objects.get(pk=form.cleaned_data['host_machine'])

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
        for ip in server.ip_set.all():
            form_dict.update({'ip_' + str(ip.id): Ip.get_string_ip(ip.ip_as_int)})
        if server.is_physical:
            rack = server.rack
            room = rack.room
            form_dict.update({'server_territory': room.territory.id,
                              'server_room': room.id,
                              'server_rack': rack.id})
        form = ServerForm(form_dict, server_id=server_id)
        return render(request, os.path.join('server_list', 'server_edit.html'), {'form': form})


def server_new(request):
    print('user_auth', request.user.is_authenticated)
    if not request.user.is_authenticated:
        raise PermissionDenied
    server = Server()
    server_id = max(Server.objects.all().values_list('id', flat=True)) + 1
    if request.method == 'GET':

        data_dict = {
            'server_name': 'New server',
            'power_state': True,
            'is_physical': True,
            'host_machine': Server.objects.filter(is_physical=True).first().id}
        form = ServerForm(data_dict, server_id=server_id, new_server=True)
        print("is_bound: ", form.is_bound)
        return render(request, os.path.join('server_list', 'server_edit.html'), {'form': form})
    elif request.method == 'POST':
        form = ServerForm(request.POST, server_id=server_id, new_server=True)
        if form.is_valid():

            return HttpResponse("OK")
        else:
            print("not valid")
            print("bound", form.is_bound)
            return render(request, os.path.join('server_list', 'server_edit.html'), {'form': form})


def ip_edit(request, ip_id):
    if not request.user.is_authenticated:
        raise PermissionDenied
    try:
        ip = Ip.objects.get(pk=ip_id)
    except Ip.DoesNotExist:
        raise Http404("IP not found")
    if request.method == 'GET':
        data = {'segment_id': ip.segment.id,
                'ip': ip.get_string_ip()}
        form = IpForm(data)
        return render(request, os.path.join('server_list', 'ip_edit.html'), {'form': form})
    elif request.method == 'POST':
        form = IpForm(request.POST)
        if form.is_valid():
            ip.ip_as_int = Ip.get_ip_from_string(form.cleaned_data['ip'])
            ip.segment = Segment.objects.get(pk=form.cleaned_data['segment_id'])
            ip.save()
            return HttpResponse("<script>window.close()</script>")
        else:
            return render(request, os.path.join('server_list', 'ip_edit.html'), {'form': form})


# todo на странице просмотра сервера если много ip из корневых сегментов, то расположение дублируется

def ip_new(request, server_id):
    if not request.user.is_authenticated:
        raise PermissionDenied
    try:
        server = Server.objects.get(pk=server_id)
    except Server.DoesNotExist:
        raise Http404("Server not found")
    if request.method == 'GET':
        return render(request, os.path.join('server_list', 'ip_edit.html'), {'form': IpForm()})
    elif request.method == 'POST':
        form = IpForm(request.POST)
        if form.is_valid():
            ip = Ip()
            ip.ip_as_int = Ip.get_ip_from_string(form.cleaned_data['ip'])
            ip.segment = Segment.objects.get(pk=form.cleaned_data['segment_id'])
            ip.mask_as_int = 0
            ip.gateway_as_int = 0
            ip.server = server
            ip.save()
            return HttpResponse("<script>window.close()</script>")
        else:
            return render(request, os.path.join('server_list', 'ip_edit.html'), {'form': form})


def segment_new(request):
    if not request.user.is_authenticated:
        return PermissionDenied
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


def segment_edit(request, segment_id):
    if not request.user.is_authenticated:
        return PermissionDenied
    if request.method == 'GET':
        try:
            form = SegmentForm(instance=Segment.objects.get(pk=segment_id))
        except Segment.DoesNotExist:
            raise Http404("No segment found")
        return render(request, os.path.join('server_list', 'segment_edit.html'), {'form': form})
    if request.method == 'POST':
        form = SegmentForm(request)
        if form.is_valid():
            form.save()
            return HttpResponse("<script>window.close()</script>")
        else:
            return render(request, os.path.join('server_list', 'segment_edit.html'), {'form': form})

    return None


def server_view(request, server_id):
    try:
        server = Server.objects.get(pk=server_id)
    except Server.DoesNotExist:
        raise Http404("No server found")
    ip_list = []
    for ip in server.ip_set.all():
        ip_list.append((ip.segment.name, Ip.get_string_ip(ip.ip_as_int)))
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


def ajax(request):
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
    # response = HttpResponse(
    #     serializers.serialize('json', Server.objects.all(), fields=('pk', 'hostname', 'purpose')),
    #     content_type='application/json')
    if request.GET.get('model') == 'vm':
        return HttpResponse(
            serializers.serialize('json', Server.objects.filter(is_physical=True), fields=('pk', 'hostname')),
            content_type='application/json')
    # return response
    if request.GET.get('action') == 'delete_ip':
        ip_id = request.GET.get('ip_id')
        try:
            ip = Ip.objects.get(pk=ip_id)
            ip.delete()
        except Ip.DoesNotExist:
            raise Http404
        return HttpResponse('ok')
    return None


def update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            d[k] = update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def get_power_state(server_is_on):  # todo move to templatetags
    return "on" if server_is_on else "off"


def segment_view():
    return None
