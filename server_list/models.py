from django.db import models


# Create your models here.
class Territory(models.Model):
    name = models.CharField(max_length=50)
    address = models.CharField(max_length=200, blank=True)
    description = models.CharField(max_length=500, blank=True)

    def __str__(self):
        return str(self.name)

    def get_servers(self, target_segment):
        server_list = []
        for room in self.room_set.all():
            for rack in room.rack_set.all():
                for server in rack.server_set.all():
                    server_list.append(server)
        server_query_set = Server.objects.filter(
            rack__in=Rack.objects.filter(
                room__in=Room.objects.filter(
                    id__in=self.room_set.all()))). \
            filter(segments__in=Segment.objects.filter(id=int(target_segment)))
        return server_query_set


class ServerGroup(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.name


class Room(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=500, blank=True)
    territory = models.ForeignKey(Territory, on_delete=models.SET_DEFAULT, default=None)

    def __str__(self):
        return (self.territory.__str__() if self.territory is not None else 'None') + ", " + self.name


class Rack(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=500, blank=True)
    room = models.ForeignKey(Room, on_delete=models.SET_DEFAULT, default=None)
    serial_number = models.CharField(max_length=100, blank=True)
    size = models.IntegerField(default=0)
    topdown = models.BooleanField(default=False)

    def __str__(self):
        return (self.room.__str__() if self.room is not None else 'None') + ", " + self.name


class Segment(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=200, blank=True)
    is_root_segment = models.BooleanField(default=False)
    parent_segment = models.ForeignKey('self', on_delete=models.SET_DEFAULT, default=None, blank=True, null=True)

    def __str__(self):
        return str(self.name)


class Server(models.Model):
    locations = {0: "front", 1: "back", 2: "full"}
    hostname = models.CharField(max_length=50)
    model = models.CharField(max_length=50, blank=True)  # separate table?
    is_physical = models.BooleanField(default=True)
    host_machine = models.ForeignKey('self', on_delete=models.SET_DEFAULT, default=None, blank=True, null=True)
    is_on = models.BooleanField(default=True)
    os = models.CharField(max_length=50, blank=True)  # separate table?
    purpose = models.CharField(max_length=200, blank=True)
    description = models.CharField(max_length=500, blank=True)
    serial_num = models.CharField(max_length=100, blank=True)
    specs = models.CharField(max_length=200, blank=True)  # as field in separate table "model"?
    sensitive_data = models.CharField(max_length=200, blank=True)  # add encryption?
    segments = models.ManyToManyField(Segment, through='Ip')
    height = models.IntegerField(blank=True, null=True)
    unit = models.IntegerField(blank=True, null=True)
    location = models.IntegerField(blank=True, null=True)
    # unit = models.OneToOneField(Unit, on_delete=models.CASCADE, default=None, blank=True, null=True)
    rack = models.ForeignKey(Rack, on_delete=models.SET_DEFAULT, default=None, blank=True, null=True)
    group = models.ForeignKey(ServerGroup, on_delete=models.SET_DEFAULT, default=None, blank=True, null=True)

    def __str__(self):
        return self.hostname

    def get_territory(self):
        return self.rack.room.territory

    def get_unit_string(self):
        return str(self.unit) if self.height == 1 else str(self.unit) + "-" + str(self.unit + self.height - 1)


class Ip(models.Model):
    # ip_as_int = models.IntegerField()
    mask_as_int = models.IntegerField()
    gateway_as_int = models.IntegerField()
    server = models.ForeignKey(Server, on_delete=models.CASCADE)
    segment = models.ForeignKey(Segment, on_delete=models.CASCADE)
    ip_as_string = models.CharField(max_length=20)

    def __str__(self):
        return self.ip_as_string

    # def save(self, *args, **kwargs):
    #    self.ip_as_string = self.__str__()
    #    super().save(*args, **kwargs)

    # @staticmethod
    # def get_string_ip(ip_as_int):
    #     counter = 0
    #     mask = 255
    #     result = ""
    #     while counter < 32:
    #         if len(result) != 0:
    #             result = "." + result
    #         t = ip_as_int & (mask << counter)
    #         result = str(t >> counter) + result
    #         counter += 8
    #     return result

    @staticmethod
    def get_ip_from_string(ip_str):
        split = ip_str.split(".")
        result = 0
        for i in range(4):
            result += int(split[i]) * 256 ** (3 - i)
        return result

    @staticmethod
    def check_ip(ip_str):
        split = ip_str.split('/')
        if len(split) not in (1, 2):
            return False
        if len(split) == 2:
            try:
                if not 0 <= int(split[1]) <= 32:
                    return False
            except(ValueError, TypeError) as e:
                print('error', e)
                return False
        ip = split[0].split('.')
        if len(ip) != 4:
            return False
        for octet in ip:
            try:
                if not 0 <= int(octet) <= 255:
                    return False
            except (ValueError, TypeError) as e:
                print('error', e)
                return False
        return True
