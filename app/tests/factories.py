import factory
from server_list.models import Territory, Server, Ip, Segment, Rack, Room, ServerGroup


class TerritoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Territory

    name = 'x'
    address = 'x'
    description = 'x'


class RoomFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Room

    name = 'x'
    description = 'x'
    territory = factory.SubFactory(TerritoryFactory)


class RackFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Rack

    name = 'x'
    description = 'x'
    room = factory.SubFactory(RoomFactory)
    serial_number = 'x'
    size = 0
    topdown = True


class SegmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Segment

    name = 'x'
    description = 'x'
    is_root_segment = True
    parent_segment = None  # factory.SubFactory('tests.factories.SegmentFactory')


class IpFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Ip

    mask_as_int = 24
    gateway_as_int = 0
    server = factory.SubFactory('tests.factories.ServerFactory')
    segment = factory.SubFactory(SegmentFactory)
    ip_as_string = '0.0.0.0'


class ServerGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ServerGroup

    name = 'x'
    description = 'x'


class ServerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Server

    hostname = 'x'
    model = 'x'
    is_physical = True
    host_machine = None  # factory.RelatedFactory('tests.factories.ServerFactory')
    is_on = True
    os = 'x'
    purpose = 'x'
    description = 'x'
    serial_num = 'x'
    specs = 'x'
    sensitive_data = 'x'
    # segments = factory.SubFactory(SegmentFactory)
    height = 2
    unit = 0
    location = 0
    rack = factory.SubFactory(RackFactory)
    group = factory.SubFactory(ServerGroupFactory)
    hostname_lower = 'x'
    purpose_lower = 'x'
