import os
from itertools import chain

from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.urls import reverse, reverse_lazy

from server_list import strings
from server_list.utils import search_servers, order_query
from . import utils
from django.core import serializers
from django.shortcuts import render, redirect
from server_list.models import Server, Segment, Ip, Rack, Room, Territory, ServerGroup
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from .forms import ServerFormOld, IpFormTest, SegmentForm, RackForm, TerritoryForm, RoomForm, UserForm, ServerForm, GroupForm
from django.http import Http404


# Create your views here.
def proof(request):
    return HttpResponseRedirect(reverse('list'))


@login_required(login_url=reverse_lazy('custom_login'))
def server_view_all(request):
    server_list = Server.objects.filter(is_physical=True)
    return render(request, os.path.join('server_list', 'servers_all.html'), {"servers": server_list})


@login_required(login_url=reverse_lazy('custom_login'))
def servers(request):
    try:
        target_group_id = int(request.GET.get('group'))
    except TypeError:
        first = ServerGroup.objects.first()
        if first is None:
            return HttpResponse('no groups')
        return HttpResponseRedirect(reverse('list') + '?group=' + str(first.id))
    links = {}
    for group in ServerGroup.objects.all():
        links.update({group.id: group.name})
    territories = []
    target_group = ServerGroup.objects.get(pk=int(target_group_id))
    servers_in_target_group = target_group.server_set.all()
    for server in servers_in_target_group.filter(is_physical=True):
        territory = server.get_territory()
        if territory not in territories:
            territories.append(territory)
    tabs = {}  # список территорий для вкладок
    ser_dict = {}
    # {territory:{room:{rack::server_list}}}

    order = '-unit'
    order_by = request.GET.get('order_by')

    # if order_by is not None:
    #     orders = order_by.split('-')
    #     if len(orders) > 0:
    #         if orders[0] == 'vm':
    #             vm_order = ('' if orders[1] == 'asc' else '-') + 'hostname'
    #         else:
    #             order = ('' if orders[1] == 'asc' else '-') + orders[0]
    for t in territories:
        tabs.update({t.id: t.name})
        for room in t.room_set.all():
            for rack in room.rack_set.all():
                seg_list = Segment.objects.filter(server__in=servers_in_target_group).distinct().filter(server__in=rack.server_set.all())
                ser_list = {}
                rack.server_set.filter(group=target_group)
                row = {'unit': strings.STRING_UNIT,
                       'model': strings.STRING_MODEL,
                       'hostname': strings.STRING_HOSTNAME,
                       'is_on': strings.STRING_IS_ON}
                vm_col_needed = len(rack.server_set.filter(group=target_group).annotate(number_of_vms=Count('server')).filter(number_of_vms__gt=0)) > 0
                if vm_col_needed:
                    row.update({'vm': strings.STRING_VM})
                row.update({'os': strings.STRING_OS,
                            'purpose': strings.STRING_PURPOSE})
                for seg in seg_list:
                    row['seg_' + str(seg.id)] = seg.name
                row['serial_num'] = strings.STRING_SN
                row['specs'] = strings.STRING_SPECS
                ser_list.update({"header": row})

                for server in order_query(rack.server_set.filter(group=target_group), order_by):
                    row = [server.get_unit_string() + " " + Server.locations.get(server.location), server.model,
                           server.hostname,
                           "on" if server.is_on else "off"]
                    if vm_col_needed:
                        row.append([""])
                    row.append(server.os)
                    row.append(server.purpose)
                    for seg in seg_list:
                        row.append([x.ip_as_string for x in list(server.ip_set.filter(segment=seg))])
                    row.append(server.serial_num)
                    row.append(server.specs)
                    ser_list.update({server.id: row})
                    if vm_col_needed:
                        for vm in order_query(server.server_set.all(), order_by):
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
    if request.method == 'GET':
        form = ServerForm(instance=server)
        return render(request, os.path.join('server_list', 'server_edit.html'), {'form': form})
    elif request.method == 'POST':
        form = ServerForm(request.POST, instance=server)
        if not form.is_valid():
            return render(request, os.path.join('server_list', 'server_edit.html'), {'form': form})
        else:
            form.save()
        return redirect('server_view', server_id=server.id)


@login_required(login_url=reverse_lazy('custom_login'))
def server_new(request):
    if request.method == 'GET':
        form = ServerForm()
        return render(request, os.path.join('server_list', 'server_edit.html'), {'form': form})
    elif request.method == 'POST':
        form = ServerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("server_view", form.instance.id)
        else:
            return render(request, os.path.join('server_list', 'server_edit.html'), {'form': form})


@login_required(login_url=reverse_lazy('custom_login'))
def ip_edit(request, ip_id):
    try:
        ip = Ip.objects.get(pk=ip_id)
    except Ip.DoesNotExist:
        raise Http404("IP not found")
    if request.method == 'GET':
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
        ip = Ip()
        ip.server = server
        return render(request, os.path.join('server_list', 'ip_edit.html'), {'form': IpFormTest(instance=ip)})
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
    try:
        instance = Segment.objects.get(pk=segment_id)

    except Segment.DoesNotExist:
        raise Http404("No segment found")
    if request.method == 'GET':
        form = SegmentForm(instance=instance)
        return render(request, os.path.join('server_list', 'segment_edit.html'), {'form': form})
    if request.method == 'POST':
        form = SegmentForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return HttpResponse("<script>window.close()</script>")
        else:
            return render(request, os.path.join('server_list', 'segment_edit.html'), {'form': form})

    return None


@login_required(login_url=reverse_lazy('custom_login'))
def rack_view(request, rack_id):
    try:
        rack = Rack.objects.get(pk=rack_id)
    except Rack.DoesNotExist:
        raise Http404("No rack found")
    rack_front = {}
    rack_back = {}
    for s in rack.server_set.all():
        units = [s.unit, s.height]
        if s.location != 1:
            rack_front.update({s: units})
        if s.location != 0:
            rack_back.update({s: units})
    return render(request, os.path.join('server_list', 'rack_view.html'), {'rack': rack, 'front': rack_front, 'back': rack_back})


@login_required(login_url=reverse_lazy('custom_login'))
def rack_edit(request, rack_id):
    # print('post', request.POST.get('close'))
    # print('get', request.GET.get('close'))
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


@login_required(login_url=reverse_lazy('custom_login'))
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
                 "root_ip_list": (server.ip_set.filter(segment__is_root_segment=True).distinct()),
                 "group": server.group,
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


# @login_required(login_url=reverse_lazy('custom_login'))
def ajax(request):
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

    if request.GET.get('action') == 'delete_ip':
        if not request.user.is_authenticated:
            return HttpResponse("Вы не авторизованы")
        ip_id = request.GET.get('ip_id')
        try:
            ip = Ip.objects.get(pk=ip_id)
            ip.delete()
        except Ip.DoesNotExist:
            raise Http404
        return HttpResponse('ok')

    if request.GET.get('action') == 'delete_server':
        server_id = request.GET.get('server_id')
        try:
            server_to_delete = Server.objects.get(pk=server_id)
        except Server.DoesNotExist:
            raise Http404
        if server_to_delete.server_set.count() > 0:
            return HttpResponse('Перенесите виртуальные машины на другой сервер')
        server_to_delete.delete()
        return HttpResponse('ok')

    if request.GET.get('action') == 'delete_rack':
        rack_id = request.GET.get('rack_id')
        try:
            rack_to_delete = Rack.objects.get(pk=rack_id)
        except Rack.DoesNotExist:
            raise Http404
        if rack_to_delete.server_set.count() > 0:
            return HttpResponse('Перенесите серверы в другую стойку')
        rack_to_delete.delete()
        return HttpResponse('ok')

    if request.GET.get('action') == 'delete_territory':
        territory_id = request.GET.get('territory_id')
        try:
            territory_to_delete = Territory.objects.get(pk=territory_id)
        except Territory.DoesNotExist:
            raise Http404
        if territory_to_delete.room_set.count() > 0:
            return HttpResponse('Перенесите помещения на другую территорию')
        territory_to_delete.delete()
        return HttpResponse('ok')

    if request.GET.get('action') == 'delete_room':
        room_id = request.GET.get('room_id')
        try:
            room_to_delete = Room.objects.get(pk=room_id)
        except Room.DoesNotExist:
            raise Http404
        if room_to_delete.rack_set.count() > 0:
            return HttpResponse('Перенесите стойки в другое помещение')
        room_to_delete.delete()
        return HttpResponse('ok')

    if not request.user.is_authenticated:
        return HttpResponse('[{"model": "server_list.error", "message":"User is not authenticated!"}]', content_type='application_json')

    if request.GET.get('model') == 'territory':
        return HttpResponse(serializers.serialize('json', Territory.objects.all(), fields='name'), content_type='application/json')

    if request.GET.get('model') == 'room':
        ter = request.GET.get('territory')
        if ter is None:
            ter = 1
        return HttpResponse(
            serializers.serialize('json', Room.objects.filter(territory=Territory.objects.get(pk=int(ter))), fields='name'), content_type='application/json')

    if request.GET.get('model') == 'rack':
        room = request.GET.get('room')
        if room is None:
            # print("ajax request room is None")
            room = 1
        return HttpResponse(
            serializers.serialize('json', Rack.objects.filter(room=Room.objects.get(pk=int(room))), fields='name'), content_type='application/json')

    if request.GET.get('model') == 'vm':
        return HttpResponse(serializers.serialize('json', Server.objects.filter(is_physical=True), fields=('pk', 'hostname')), content_type='application/json')

    if request.GET.get('action') == 'search':
        search_query = request.GET.get('query')
        serialize = serializers.serialize('json', search_servers(search_query), fields=('pk', 'purpose', 'hostname', 'ip_as_string', 'server'))
        print('serialize', serialize)
        return HttpResponse(serialize, content_type='application/json')


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


@login_required(login_url=reverse_lazy('custom_login'))
def room_view(request, room_id):
    try:
        room = Room.objects.get(pk=room_id)
    except Room.DoesntExist:
        raise Http404
    racks = {}
    for rack in room.rack_set.all():
        racks.update({rack.id: rack.name})
    return render(request, os.path.join('server_list', 'room_view.html'), {'room': room, 'racks': racks})


@login_required(login_url=reverse_lazy('custom_login'))
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
    except Territory.DoesNotExists:
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
def group_view(request, group_id):
    try:
        group = ServerGroup.objects.get(pk=group_id)
    except ServerGroup.DoesntExist:
        raise Http404
    return render(request, os.path.join('server_list', 'group_view.html'), {'group': group})


@login_required(login_url=reverse_lazy('custom_login'))
def group_edit(request, group_id):
    try:
        group = ServerGroup.objects.get(pk=group_id)
    except ServerGroup.DoesNotExists:
        raise Http404("Нет такой группы")
    if request.method == 'GET':
        form = GroupForm(instance=group)
        return render(request, os.path.join('server_list', 'group_edit.html'), {'form': form})
    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            if request.GET.get('close') == 'True':
                return HttpResponse("<script>window.close()</script>")
            return redirect('list')
        else:
            return render(request, os.path.join('server_list', 'group_edit.html'), {'form': form})
    return HttpResponse('ok')


@login_required(login_url=reverse_lazy('custom_login'))
def group_add(request):
    if request.method == 'GET':
        form = GroupForm()
        render(request, os.path.join('server_list', 'group_edit.html'), {'form': form})

    return None


@login_required(login_url=reverse_lazy('custom_login'))
def test(request):
    return render(request, os.path.join('server_list', 'test.html'))


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


@login_required(login_url=reverse_lazy('custom_login'))
def search(request):
    if request.method == 'GET':
        print("GET")
        return HttpResponseBadRequest("400")
    if request.method == 'POST':
        search_query = request.POST.get('searchInput')
        result_set = Server.objects.filter(hostname_lower__icontains=search_query)
        result_set |= Server.objects.filter(purpose_lower__icontains=search_query)

        result_set.distinct()
        print(result_set)  # todo убрать ip
        return render(request, os.path.join('server_list', 'search.html'), {'result_set': result_set})
    return HttpResponse('search')


@login_required(login_url=reverse_lazy('custom_login'))
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
