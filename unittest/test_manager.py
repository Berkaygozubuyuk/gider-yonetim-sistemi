import unittest
import datetime as dt
from models.employee import Calisan
from models.manager import Yonetici
from models.expense2 import Harcama

class TestYonetici(unittest.TestCase):

    def setUp(self):
        self.yonetici = Yonetici("Mehmet Demir", "Yonetim")
        self.calisan = Calisan("Zeynep Kaya", "IT")
        self.negatif_harcama = Harcama(self.calisan, -250, "Ofis Malzemesi", dt.datetime(2025, 5, 1))
        self.pozitif_harcama = Harcama(self.calisan, 500, "Yazilim Lisansi", dt.datetime(2025, 5, 1))
        self.yonetici.onaylanan_harcamalar = [] 

    def test_pozitif_harcama_onayla(self):
        self.yonetici.harcama_onayla(self.pozitif_harcama)
        self.assertTrue(self.pozitif_harcama.onaylandi)
        

    def test_negatif_harcama_onayla(self):
        self.yonetici.harcama_onayla(self.negatif_harcama)
        self.assertFalse(self.negatif_harcama.onaylandi)
        
