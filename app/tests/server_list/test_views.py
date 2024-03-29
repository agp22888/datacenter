import random

import pytest
from django.urls import reverse
from faker import Faker
from faker.providers import internet, lorem, ssn

from server_list.forms import RackForm, RoomForm, TerritoryForm
from server_list.models import Rack, Room, Territory

pytestmark = pytest.mark.django_db


class TestRack:
    @pytest.fixture
    def client_with_user(self, client, user_factory):
        user = user_factory()
        client.force_login(user)
        return client

    def test_rack_view(self,
                       client_with_user,
                       rack_factory):
        rack = rack_factory()
        url = reverse('rack_view', args=[rack.id])
        response = client_with_user.get(url)
        assert response.status_code == 200
        assert response.context['rack'] == rack

    def test_404(self,
                 client_with_user, ):
        url = reverse('rack_view', args=[100])
        response = client_with_user.get(url)
        assert response.status_code == 404

    def test_rack_with_servers(self,
                               client_with_user,
                               rack_factory,
                               server_factory):
        f = Faker()
        f.add_provider(internet)
        rack = rack_factory()
        servers = [server_factory(hostname=f.hostname(), rack=rack, location=random.randint(0, 1)) for _ in range(10)]
        url = reverse('rack_view', args=[rack.id])
        resp = client_with_user.get(url)
        assert set(resp.context['front']) == {x for x in servers if x.location == 0}
        assert set(resp.context['back']) == {x for x in servers if x.location == 1}

    def test_rack_edit_get(self,
                           client_with_user,
                           rack_factory):
        rack = rack_factory()
        url = f"{reverse('rack_edit')}/?rack_id={rack.id}"
        resp = client_with_user.get(url)
        form = resp.context['form']
        assert resp.status_code == 200
        assert form.instance == rack

    def test_rack_edit_get_404(self,
                               client_with_user,
                               rack_factory):
        rack = rack_factory()
        url = f"{reverse('rack_edit')}/?rack_id={rack.id + 100}"
        resp = client_with_user.get(url)
        assert resp.status_code == 404

    def test_rack_edit_change_success(self,
                                      client_with_user,
                                      rack_factory):
        rack = rack_factory()
        url = f"{reverse('rack_edit')}/?rack_id={rack.id}"
        resp = client_with_user.get(url)
        data = resp.context['form'].initial
        data['name'] = 'edited'
        resp = client_with_user.post(url, data=data)
        assert resp.status_code == 302
        resp = client_with_user.get(resp.url)
        rack_edited = Rack.objects.get(pk=rack.id)
        assert resp.context['rack'] == rack_edited

    def test_rack_edit_change_with_errors(self,
                                          client_with_user,
                                          rack_factory):
        rack = rack_factory()
        url = f"{reverse('rack_edit')}/?rack_id={rack.id}"
        resp = client_with_user.get(url)
        data = resp.context['form'].initial
        data['name'] = 'edited'
        data['size'] = 0
        resp = client_with_user.post(url, data=data)
        assert resp.status_code == 200
        assert len(resp.context['form'].errors) > 0
        rack_edited = Rack.objects.get(pk=rack.id)
        assert resp.context['form'].instance == rack_edited

    def test_rack_edit_close(self,
                             client_with_user,
                             rack_factory):
        rack = rack_factory()
        url = f"{reverse('rack_edit')}/?rack_id={rack.id}&close=true"
        resp = client_with_user.get(url)
        data = resp.context['form'].initial
        data['name'] = 'edited'
        resp = client_with_user.post(url, data=data)
        assert resp.status_code == 200
        assert resp.content.decode() == f"<script>if (opener!=null) " \
                                        f"opener.call_reload('rack',[{rack.id},{rack.room.id},{rack.room.territory.id}])" \
                                        f";window.close()</script>"

    def test_rack_edit_wrong_method(self,
                                    client_with_user,
                                    rack_factory):
        rack = rack_factory()
        url = f"{reverse('rack_edit')}/?rack_id={rack.id}"
        resp = client_with_user.put(url)
        assert resp.status_code == 405

    def test_rack_edit_new_get(self,
                               client_with_user):
        url = f"{reverse('rack_edit')}/?new=true"
        resp = client_with_user.get(url)
        assert resp.status_code == 200
        assert isinstance(resp.context["form"], RackForm)

    def test_rack_edit_new_post(self,
                                client_with_user,
                                room_factory):
        room = room_factory()
        url = f"{reverse('rack_edit')}/?new=true"
        resp = client_with_user.get(url)
        data = resp.context['form'].initial
        data['name'] = 'new_rack'
        data['size'] = 36
        data['room'] = room.pk
        data['territory'] = room.territory.pk
        resp = client_with_user.post(url, data=data)
        assert resp.status_code == 302
        resp = client_with_user.get(resp.url)
        created_rack = resp.context['rack']
        assert created_rack.name == data['name']
        assert created_rack.size == data['size']
        assert created_rack.room.pk == data['room']
        assert created_rack.room.territory.pk == data['territory']


class TestRoom:
    @pytest.fixture
    def client_with_user(self, client, user_factory):
        user = user_factory()
        client.force_login(user)
        return client

    def test_room_view(self,
                       client_with_user,
                       room_factory):
        room = room_factory()
        url = reverse('room_view', args=[room.id])
        response = client_with_user.get(url)
        assert response.status_code == 200
        assert response.context['room'] == room

    def test_404(self,
                 client_with_user):
        url = reverse('room_view', args=[100])
        response = client_with_user.get(url)
        assert response.status_code == 404

    def test_room_with_racks(self,
                             client_with_user,
                             room_factory,
                             rack_factory):
        f = Faker()
        f.add_provider(lorem)
        f.add_provider(ssn)
        room = room_factory()
        racks = [rack_factory(name=f.word(), room=room) for _ in range(10)]
        url = reverse('room_view', args=[room.id])
        resp = client_with_user.get(url)
        assert len(resp.context['racks']) == len(racks)
        assert resp.context['room'] == room
        assert {k: v for k, v in resp.context['racks'].items()} == {x.id: x.name for x in racks}

    def test_room_edit_get(self,
                           client_with_user,
                           room_factory):
        room = room_factory()
        url = f"{reverse('room_edit')}/?room_id={room.id}"
        resp = client_with_user.get(url)
        form = resp.context['form']
        assert resp.status_code == 200
        assert form.instance == room

    def test_room_edit_get_404(self,
                               client_with_user,
                               room_factory):
        room = room_factory()
        url = f"{reverse('room_edit')}/?room_id={room.id + 100}"
        resp = client_with_user.get(url)
        assert resp.status_code == 404

    def test_room_edit_change_success(self,
                                      client_with_user,
                                      room_factory):
        room = room_factory()
        url = f"{reverse('room_edit')}/?room_id={room.id}"
        resp = client_with_user.get(url)
        data = resp.context['form'].initial
        data['name'] = 'edited'
        resp = client_with_user.post(url, data=data)
        assert resp.status_code == 302
        resp = client_with_user.get(resp.url)
        room_edited = Room.objects.get(pk=room.id)
        assert resp.context['room'] == room_edited

    def test_room_edit_close(self,
                             client_with_user,
                             room_factory):
        room = room_factory()
        url = f"{reverse('room_edit')}/?room_id={room.id}&close=true"
        resp = client_with_user.get(url)
        data = resp.context['form'].initial
        data['name'] = 'edited'
        resp = client_with_user.post(url, data=data)
        assert resp.status_code == 200
        assert resp.content.decode() == f"<script>if (opener!=null) " \
                                        f"opener.call_reload('room',[{room.id},{room.territory.id}])" \
                                        f";window.close()</script>"

    def test_room_edit_wrong_method(self,
                                    client_with_user,
                                    room_factory):
        room = room_factory()
        url = f"{reverse('room_edit')}/?room_id={room.id}"
        resp = client_with_user.put(url)
        assert resp.status_code == 405

    def test_room_edit_new_get(self,
                               client_with_user):
        url = f"{reverse('room_edit')}/?new=true"
        resp = client_with_user.get(url)
        assert resp.status_code == 200
        assert isinstance(resp.context["form"], RoomForm)

    #
    def test_room_edit_new_post(self,
                                client_with_user,
                                territory_factory):
        territory = territory_factory()
        url = f"{reverse('room_edit')}/?new=true"
        resp = client_with_user.get(url)
        data = resp.context['form'].initial
        data['name'] = 'new_room'
        data['description'] = 'description'
        data['territory'] = territory.pk
        resp = client_with_user.post(url, data=data)
        assert resp.status_code == 302
        resp = client_with_user.get(resp.url)
        created_room = resp.context['room']
        assert created_room.name == data['name']
        assert created_room.description == data['description']
        assert created_room.territory.pk == data['territory']


class TestTerritory:
    @pytest.fixture
    def client_with_user(self, client, user_factory):
        user = user_factory()
        client.force_login(user)
        return client

    def test_territory_view(self,
                            client_with_user,
                            territory_factory):
        territory = territory_factory()
        url = reverse('territory_view', args=[territory.id])
        response = client_with_user.get(url)
        assert response.status_code == 200
        assert response.context['territory'] == territory

    def test_404(self,
                 client_with_user):
        url = reverse('territory_view', args=[100])
        response = client_with_user.get(url)
        assert response.status_code == 404

    def test_territory_with_rooms(self,
                                  client_with_user,
                                  territory_factory,
                                  room_factory):
        f = Faker()
        f.add_provider(lorem)
        territory = territory_factory()
        rooms = [room_factory(name=f.word(), territory=territory) for _ in range(10)]
        url = reverse('territory_view', args=[territory.id])
        resp = client_with_user.get(url)
        assert len(resp.context['rooms']) == len(rooms)
        assert resp.context['territory'] == territory
        assert {k: v for k, v in resp.context['rooms'].items()} == {x.id: x.name for x in rooms}

    def test_territory_edit_get(self,
                                client_with_user,
                                territory_factory):
        territory = territory_factory()
        url = f"{reverse('territory_edit')}/?territory_id={territory.id}"
        resp = client_with_user.get(url)
        form = resp.context['form']
        assert resp.status_code == 200
        assert form.instance == territory

    def test_territory_edit_get_404(self,
                                    client_with_user,
                                    territory_factory):
        territory = territory_factory()
        url = f"{reverse('territory_edit')}/?territory_id={territory.id + 100}"
        resp = client_with_user.get(url)
        assert resp.status_code == 404

    def test_territory_edit_change_success(self,
                                           client_with_user,
                                           territory_factory):
        territory = territory_factory()
        url = f"{reverse('territory_edit')}/?territory_id={territory.id}"
        resp = client_with_user.get(url)
        data = resp.context['form'].initial
        data['name'] = 'edited'
        resp = client_with_user.post(url, data=data)
        assert resp.status_code == 302
        resp = client_with_user.get(resp.url)
        territory_edited = Territory.objects.get(pk=territory.id)
        assert resp.context['territory'] == territory_edited

    def test_territory_edit_close(self,
                                  client_with_user,
                                  territory_factory):
        territory = territory_factory()
        url = f"{reverse('territory_edit')}/?territory_id={territory.id}&close=true"
        resp = client_with_user.get(url)
        data = resp.context['form'].initial
        data['name'] = 'edited'
        resp = client_with_user.post(url, data=data)
        assert resp.status_code == 200
        assert resp.content.decode() == f"<script>if (opener!=null) " \
                                        f"opener.call_reload('territory',[{territory.id}])" \
                                        f";window.close()</script>"

    def test_territory_edit_wrong_method(self,
                                         client_with_user,
                                         territory_factory):
        territory = territory_factory()
        url = f"{reverse('territory_edit')}/?territory_id={territory.id}"
        resp = client_with_user.put(url)
        assert resp.status_code == 405

    def test_territory_edit_new_get(self,
                                    client_with_user):
        url = f"{reverse('territory_edit')}/?new=true"
        resp = client_with_user.get(url)
        assert resp.status_code == 200
        assert isinstance(resp.context["form"], TerritoryForm)

    #
    def test_territory_edit_new_post(self,
                                     client_with_user):
        url = f"{reverse('territory_edit')}/?new=true"
        resp = client_with_user.get(url)
        data = resp.context['form'].initial
        data['name'] = 'new_territory'
        data['description'] = 'description'
        resp = client_with_user.post(url, data=data)
        assert resp.status_code == 302
        resp = client_with_user.get(resp.url)
        created_territory = resp.context['territory']
        assert created_territory.name == data['name']
        assert created_territory.description == data['description']


