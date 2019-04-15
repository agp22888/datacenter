from django.test import TestCase
from server_list.models import Ip


class IpTestCase(TestCase):
    def test_ip(self):
        self.assertTrue(Ip.check_ip('10.21.62.33'))
        self.assertTrue(Ip.check_ip('10.21.62.33/24'))
        self.assertFalse(Ip.check_ip('310.21.62.33'))
        self.assertFalse(Ip.check_ip('a0.21.62.3'))
        self.assertFalse(Ip.check_ip('10.21.62.33/40'))
        self.assertFalse(Ip.check_ip('10.21.62.33/a'))
        self.assertFalse(Ip.check_ip('3.10.21.62.33'))
# Create your tests here.
