import unittest
import datetime as dt
from models.accounting2 import Muhasebe
from models.budget2 import ButceYoneticisi
from models.expense2 import Harcama
from models.employee import Calisan
from models.manager import Yonetici

class TestMuhasebe(unittest.TestCase):

    def setUp(self):
        departmanlar = ["Satis", "Pazarlama", "IT", "Yonetim"]
        kategoriler = ["Seyahat", "Konaklama", "Eglence", "YiyecekIcecek", "Danismanlik"]
        butce_sozlugu = {}
        for dept in departmanlar:
            butce_sozlugu[dept] = {}
            for cat in kategoriler:
                butce_sozlugu[dept][cat] = 400.0
        self.esik = 200.0
        self.butce_yoneticisi = ButceYoneticisi(butce_sozlugu, self.esik)
        self.muhasebe = Muhasebe(self.butce_yoneticisi)
        self.calisan_satis = Calisan("Cem Yilmaz", "Satis")
        self.yonetici_satis = Yonetici("Okan Bayulgen", "Satis") 

        self.normal_harcama = Harcama(self.calisan_satis, 300.0, "Eglence", dt.datetime(2025, 5, 1))
        self.yonetici_satis.harcama_onayla(self.normal_harcama)

        self.onaylanmamis_harcama = Harcama(self.calisan_satis, 250.0, "Konaklama", dt.datetime(2025, 3, 12))

        self.zaten_odenmis_harcama = Harcama(self.calisan_satis, 350.0, "YiyecekIcecek", dt.datetime(2025, 10, 20))
        self.yonetici_satis.harcama_onayla(self.zaten_odenmis_harcama)
        self.muhasebe.geri_odeme_yap(self.zaten_odenmis_harcama)

        self.kategori_guncelleme_harcamasi = Harcama(self.calisan_satis, 100.0, "Seyahat", dt.datetime(2025, 1, 15))
        self.yonetici_satis.harcama_onayla(self.kategori_guncelleme_harcamasi)


    def test_harcama_geri_odeme(self):
        durum = self.muhasebe.geri_odeme_yap(self.normal_harcama)
        self.assertTrue(self.normal_harcama.odendi)
        self.assertEqual(durum, "tam_odeme")
        self.assertEqual(self.normal_harcama.odenen_tutar, 300.0)
        self.assertEqual(self.butce_yoneticisi.kalan_butceyi_getir("Satis", "Eglence"), 100.0)


    def test_onaylanmamis_harcama_geri_odeme(self):
        durum = self.muhasebe.geri_odeme_yap(self.onaylanmamis_harcama)
        self.assertEqual(durum, "hata_onaylanmamis")
        self.assertFalse(self.onaylanmamis_harcama.odendi)

    def test_zaten_odenmis_harcama_geri_odeme(self):
        durum = self.muhasebe.geri_odeme_yap(self.zaten_odenmis_harcama)
        self.assertEqual(durum, "hata_zaten_odenmis")

    def test_harcama_kategorisi_guncelle_odenmemis(self):
        eski_kategori = self.kategori_guncelleme_harcamasi.kategori
        yeni_kategori = "Danismanlik"
        durum = self.muhasebe.harcama_kategorisi_guncelle(self.kategori_guncelleme_harcamasi, yeni_kategori)

        self.assertEqual(durum, "basarili")
        self.assertEqual(self.kategori_guncelleme_harcamasi.kategori, yeni_kategori)

        self.assertEqual(self.butce_yoneticisi.kalan_butceyi_getir("Satis", eski_kategori), 400.0)
        self.assertEqual(self.butce_yoneticisi.kalan_butceyi_getir("Satis", yeni_kategori), 400.0)

    def test_harcama_kategorisi_guncelle_odenmis(self):
        self.muhasebe.geri_odeme_yap(self.kategori_guncelleme_harcamasi)
        self.assertTrue(self.kategori_guncelleme_harcamasi.odendi)
        self.assertEqual(self.kategori_guncelleme_harcamasi.odenen_tutar, 100.0)

        kalan_seyahat_on_guncelleme = self.butce_yoneticisi.kalan_butceyi_getir("Satis", "Seyahat")
        kalan_danismanlik_on_guncelleme = self.butce_yoneticisi.kalan_butceyi_getir("Satis", "Danismanlik")

        eski_kategori = self.kategori_guncelleme_harcamasi.kategori
        yeni_kategori = "Danismanlik"

        durum = self.muhasebe.harcama_kategorisi_guncelle(self.kategori_guncelleme_harcamasi, yeni_kategori)
        self.assertEqual(durum, "basarili")
        self.assertEqual(self.kategori_guncelleme_harcamasi.kategori, yeni_kategori)

        self.assertEqual(self.butce_yoneticisi.kalan_butceyi_getir("Satis", eski_kategori), kalan_seyahat_on_guncelleme + self.kategori_guncelleme_harcamasi.odenen_tutar)
        self.assertEqual(self.butce_yoneticisi.kalan_butceyi_getir("Satis", yeni_kategori), kalan_danismanlik_on_guncelleme - self.kategori_guncelleme_harcamasi.odenen_tutar)

    def test_harcama_kategorisi_guncelle_ayni_kategori(self):
        mevcut_kategori = self.kategori_guncelleme_harcamasi.kategori
        durum = self.muhasebe.harcama_kategorisi_guncelle(self.kategori_guncelleme_harcamasi, mevcut_kategori)
        self.assertEqual(durum, "bilgi_ayni_kategori")

    def test_harcama_kategorisi_guncelle_gecersiz_yeni_kategori(self):
        durum = self.muhasebe.harcama_kategorisi_guncelle(self.kategori_guncelleme_harcamasi, "GecersizKategoriAdi")
        self.assertEqual(durum, "hata_gecersiz_yeni_kategori")
        self.assertNotEqual(self.kategori_guncelleme_harcamasi.kategori, "GecersizKategoriAdi")

    def test_harcama_kategorisi_guncelle_odenmis_sifir_tutar(self):
        sifir_tutarli_odenmis_harcama = Harcama(self.calisan_satis, 0.0, "Seyahat", dt.datetime(2025, 2, 1))
        self.yonetici_satis.harcama_onayla(sifir_tutarli_odenmis_harcama)
        self.assertFalse(sifir_tutarli_odenmis_harcama.onaylandi) 
        self.assertEqual(sifir_tutarli_odenmis_harcama.odenen_tutar, 0.0)

        durum = self.muhasebe.geri_odeme_yap(sifir_tutarli_odenmis_harcama)
        self.assertEqual(durum, "hata_onaylanmamis") 

        eski_kategori_kalan = self.butce_yoneticisi.kalan_butceyi_getir("Satis", "Seyahat")
        yeni_kategori_kalan = self.butce_yoneticisi.kalan_butceyi_getir("Satis", "Danismanlik")

        durum = self.muhasebe.harcama_kategorisi_guncelle(sifir_tutarli_odenmis_harcama, "Danismanlik")
        self.assertEqual(durum, "basarili") 
        self.assertEqual(sifir_tutarli_odenmis_harcama.kategori, "Danismanlik") 

        self.assertEqual(self.butce_yoneticisi.kalan_butceyi_getir("Satis", "Seyahat"), eski_kategori_kalan)
        self.assertEqual(self.butce_yoneticisi.kalan_butceyi_getir("Satis", "Danismanlik"), yeni_kategori_kalan)
