from django.contrib import admin
from server_list.models import Server, Territory, Rack, Unit, Room, Segment, Ip

admin.site.register(Server)
admin.site.register(Territory)
admin.site.register(Rack)
admin.site.register(Unit)
admin.site.register(Room)
admin.site.register(Segment)
admin.site.register(Ip)
