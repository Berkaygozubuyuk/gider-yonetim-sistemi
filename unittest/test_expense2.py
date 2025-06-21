import unittest
import datetime as dt
from models.expense2 import Harcama
from models.employee import Calisan

class TestHarcama(unittest.TestCase):

    def setUp(self):
        self.calisan = Calisan("Ayse Yilmaz", "Pazarlama")
        self.harcama = Harcama(self.calisan, 500, "Taksi Ucreti", dt.datetime(2025, 5, 1), "Musteri Toplantisi", "BELGE001")

    def test_baslangic_degerleri(self):
        kontrol_tarihi = dt.datetime(2025, 5, 1)
        self.assertEqual(self.harcama.calisan.isim, "Ayse Yilmaz")
        self.assertEqual(self.harcama.calisan.departman, "Pazarlama")
        self.assertEqual(self.harcama.tutar, 500)
        self.assertEqual(self.harcama.kategori, "Taksi Ucreti")
        self.assertEqual(self.harcama.tarih, kontrol_tarihi)
        self.assertEqual(self.harcama.aciklama, "Musteri Toplantisi")
        self.assertEqual(self.harcama.belge_referansi, "BELGE001")

    def test_varsayilan_degerler(self):
        self.assertFalse(self.harcama.onaylandi)
        self.assertFalse(self.harcama.odendi)
        self.assertEqual(self.harcama.odenen_tutar, 0.0)
        self.assertEqual(self.harcama.odeme_sonrasi_durum, "")
