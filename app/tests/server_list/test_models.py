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
