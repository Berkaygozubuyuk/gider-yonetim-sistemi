import unittest
from models.employee import Calisan

class TestCalisan(unittest.TestCase):

    def setUp(self):
        self.calisan = Calisan("Ali Veli", "Satis")

    def test_isim(self):
        self.assertEqual("Ali Veli", self.calisan.isim)

    def test_departman(self):
        self.assertEqual("Satis", self.calisan.departman)
