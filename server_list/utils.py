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
