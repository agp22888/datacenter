import collections
from server_list.models import Server, Ip, Territory, Rack, Room, Segment
from django.core import serializers


def update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            d[k] = update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


def search_servers(search_query):
    result_list = list(Server.objects.filter(hostname_lower__icontains=search_query))
    result_list.extend([x for x in Server.objects.filter(purpose_lower__icontains=search_query) if x not in result_list])
    result_list.extend([x for x in Server.objects.filter(ip__ip_as_string__contains=search_query) if x not in result_list])
    result_list.extend([y for x in result_list for y in x.ip_set.all()])
    return result_list
