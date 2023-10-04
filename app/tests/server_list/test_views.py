import random

import pytest
from django.urls import reverse, reverse_lazy
from faker import Faker
from faker.providers import internet

from server_list.forms import RackForm
from server_list.models import Room, Rack

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
        assert set(resp.context['front']) == {x for x in servers if x.location is 0}
        assert set(resp.context['back']) == {x for x in servers if x.location is 1}

    def test_rack_edit_get(self,
                           client_with_user,
                           rack_factory):
        rack = rack_factory()
        url = f"{reverse('rack_edit')}/?rack_id={rack.id}"
        resp = client_with_user.get(url)
        form = resp.context['form']
        assert resp.status_code == 200
        assert form.instance == rack

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
        assert resp.content.decode() == "Wrong Method"
