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


def order_query(query, order):
    if order is not None:
        parts = order.split('-')
        if len(parts) > 0:
            if 'seg_' in parts[0]:
                list_query = list(query)
                seg = Segment.objects.get(pk=int(parts[0].split('_')[1]))
                list_query.sort(key=lambda x: Ip.get_ip_from_string(x.ip_set.filter(segment=seg).first().ip_as_string) if x.ip_set.filter(segment=seg).first() is not None else 0,
                                reverse=parts[1] == 'desc')
                return list_query
            else:
                order = ('' if parts[1] == 'asc' else '-') + parts[0]
                return query.order_by(order)
    return query
