import pytest
from faker import Faker
from faker.providers import internet

from server_list.models import Ip

pytestmark = pytest.mark.django_db


class TestTerritoryModel:
    def test_str_return(self, territory_factory):
        name = "test name"
        rack = territory_factory(name=name)
        assert rack.__str__() == name

    def test_get_servers(self,
                         territory_factory,
                         server_factory, room_factory,
                         rack_factory,
                         segment_factory,
                         ip_factory):
        f = Faker()
        f.add_provider(internet)
        segment = segment_factory(name='test_segment')
        territory = territory_factory(name='test')
        room = room_factory(territory=territory)
        rack = rack_factory(room=room)
        servers = set()
        for _ in range(10):
            server = server_factory(hostname=f.hostname(), rack=rack)
            __ = ip_factory(server=server, segment=segment)
            servers.add(server)
        t_servers = set(territory.get_servers(segment.id))
        assert servers == t_servers


class TestIpModel:
    def test_ip(self):
        assert Ip.check_ip('10.21.62.33')
        assert Ip.check_ip('10.21.62.33/24')
        assert not Ip.check_ip('310.21.62.33')
        assert not Ip.check_ip('a0.21.62.3')
        assert not Ip.check_ip('10.21.62.33/40')
        assert not Ip.check_ip('10.21.62.33/a')
        assert not Ip.check_ip('3.10.21.62.33')
        assert not Ip.check_ip('10.10.10.10/24/12')

    def test_str(self, ip_factory, segment_factory, server_factory):
        ip_str = "10.10.10.10"
        ip = ip_factory(ip_as_string=ip_str, segment=segment_factory(), server=server_factory())
        assert ip.__str__() == ip_str

    def test_ip_from_string(self):
        ip_str = "10.10.10.10"
        assert Ip.get_ip_from_string(ip_str) == 168430090


class TestServerGroupModel:
    def test_str(self, server_group_factory):
        name = "test_group"
        sg = server_group_factory(name=name)
        assert sg.__str__() == name


class TestRoomModel:

    def test_str(self, room_factory):
        name = "test_room"
        room = room_factory(name=name)
        assert room.__str__() == name


class TestRackModel:
    def test_str(self, rack_factory):
        name = "test_rack"
        rack = rack_factory(name=name)
        assert rack.__str__() == name

    def test_full_str(self, rack_factory, room_factory, territory_factory):
        t_name = "test_territory"
        rm_name = "test_room"
        rk_name = "test_rack"
        territory = territory_factory(name=t_name)
        room = room_factory(name=rm_name, territory=territory)
        rack = rack_factory(name=rk_name, room=room)
        assert rack.full_str() == f'{rm_name}, {t_name}, {rk_name}'


class TestServerModel:

    def test_str(self, server_factory):
        hostname = "test_server"
        server = server_factory(hostname=hostname)
        assert server.__str__() == hostname

    def test_get_territory(self, server_factory, rack_factory, room_factory, territory_factory):
        territory = territory_factory()
        server = server_factory(rack=rack_factory(room=room_factory(territory=territory)))
        assert server.get_territory() is territory

    def test_unit_string(self, server_factory, rack_factory):
        rack = rack_factory(size=42)
        server = server_factory(rack=rack, height=1, unit=10)
        assert server.get_unit_string() == '10'
        server = server_factory(rack=rack, height=3, unit=15)
        assert server.get_unit_string() == '15-17'


class TestSegmentModel:

    def test_str(self, segment_factory):
        name = "test segment"
        segment = segment_factory(name=name)
        assert segment.__str__() == name
