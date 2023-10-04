from pytest_factoryboy import register
from tests.factories import ServerFactory, SegmentFactory, ServerGroupFactory, \
    RackFactory, TerritoryFactory, RoomFactory, IpFactory, UserFactory

register(ServerFactory)
register(SegmentFactory)
register(ServerGroupFactory)
register(RackFactory)
register(TerritoryFactory)
register(RoomFactory)
register(IpFactory)
register(UserFactory)
