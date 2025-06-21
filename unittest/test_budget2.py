import unittest
import datetime as dt
from models.budget2 import ButceYoneticisi
from models.employee import Calisan
from models.expense2 import Harcama


class TestButceYoneticisi(unittest.TestCase):

    def setUp(self):
        departmanlar = ["Satis", "Pazarlama", "IT", "Yonetim"]
        kategoriler = ["Seyahat", "Konaklama", "Eglence", "YiyecekIcecek"]
        butce_sozlugu = {}
        for dept in departmanlar:
            butce_sozlugu[dept] = {}
            for cat in kategoriler:
                butce_sozlugu[dept][cat] = 400.0
        self.esik = 200.0
        self.butce_yoneticisi = ButceYoneticisi(butce_sozlugu, self.esik)
        self.calisan = Calisan("Can Efe", "Satis")

        self.harcama_asim = Harcama(self.calisan, 500.0, "Konaklama", dt.datetime(2025, 5, 1))
        self.normal_harcama = Harcama(self.calisan, 300.0, "Seyahat", dt.datetime(2023, 11, 5))
        self.harcama_daha_fazla_asim = Harcama(self.calisan, 700.0, "YiyecekIcecek", dt.datetime(2024, 8, 17))
        self.sifir_tutarli_harcama = Harcama(self.calisan, 0.0, "Seyahat", dt.datetime(2024, 1, 1))
        self.negatif_tutarli_harcama = Harcama(self.calisan, -100.0, "Seyahat", dt.datetime(2024, 1, 1))


    def test_normal_onay(self):
        tutar, durum = self.butce_yoneticisi.harcama_onayla(self.normal_harcama.calisan.departman, self.normal_harcama.kategori, self.normal_harcama.tutar)
        self.assertEqual(tutar, self.normal_harcama.tutar)
        self.assertEqual(durum, "tam_odeme")
        self.assertEqual(self.butce_yoneticisi.kalan_butceyi_getir("Satis", "Seyahat"), 100.0)

    def test_kalan_butce(self):
        self.butce_yoneticisi.harcama_onayla(self.normal_harcama.calisan.departman, self.normal_harcama.kategori, self.normal_harcama.tutar)
        self.assertEqual(self.butce_yoneticisi.kalan_butceyi_getir("Satis"), {"Seyahat": 100.0, "Konaklama": 400.0, "Eglence": 400.0, "YiyecekIcecek": 400.0})

    def test_baslangic_butce(self):
        self.assertEqual(self.butce_yoneticisi.baslangic_butceyi_getir("Satis"), {"Seyahat": 400.0, "Konaklama": 400.0, "Eglence": 400.0, "YiyecekIcecek": 400.0})

    def test_butce_donem_bayraklarini_sifirla(self):
        self.butce_yoneticisi.harcama_onayla(self.harcama_asim.calisan.departman, self.harcama_asim.kategori, self.harcama_asim.tutar)
        self.assertTrue(self.butce_yoneticisi.donem_icin_asim_tetiklendi)
        self.butce_yoneticisi.butce_donem_bayraklarini_sifirla()
        self.assertFalse(self.butce_yoneticisi.donem_icin_asim_tetiklendi)

    def test_kismi_asim(self):
        beklenen_tutar = self.esik + self.butce_yoneticisi.kalan_butceler[self.harcama_daha_fazla_asim.calisan.departman][self.harcama_daha_fazla_asim.kategori]
        tutar, durum = self.butce_yoneticisi.harcama_onayla(self.harcama_daha_fazla_asim.calisan.departman, self.harcama_daha_fazla_asim.kategori, self.harcama_daha_fazla_asim.tutar)
        self.assertEqual(tutar, beklenen_tutar)
        self.assertEqual(durum, "kismi_odeme_esik_limiti")
        self.assertEqual(self.butce_yoneticisi.kalan_butceyi_getir("Satis", "YiyecekIcecek"), 0)

    def test_tam_asim(self):
        tutar, durum = self.butce_yoneticisi.harcama_onayla(self.harcama_asim.calisan.departman, self.harcama_asim.kategori, self.harcama_asim.tutar)
        self.assertEqual(tutar, self.harcama_asim.tutar)
        self.assertEqual(durum, "tam_odeme_esik_kullanildi")
        self.assertEqual(self.butce_yoneticisi.kalan_butceyi_getir("Satis", "Konaklama"), 0)

    def test_sifir_tutarli_harcama_onayla(self):
        tutar, durum = self.butce_yoneticisi.harcama_onayla(self.sifir_tutarli_harcama.calisan.departman, self.sifir_tutarli_harcama.kategori, self.sifir_tutarli_harcama.tutar)
        self.assertEqual(tutar, 0.0)
        self.assertEqual(durum, "hata_sifir_veya_negatif_tutar")

    def test_negatif_tutarli_harcama_onayla(self):
        tutar, durum = self.butce_yoneticisi.harcama_onayla(self.negatif_tutarli_harcama.calisan.departman, self.negatif_tutarli_harcama.kategori, self.negatif_tutarli_harcama.tutar)
        self.assertEqual(tutar, 0.0)
        self.assertEqual(durum, "hata_sifir_veya_negatif_tutar")

    def test_gecersiz_departman_veya_kategori(self):
        tutar, durum = self.butce_yoneticisi.harcama_onayla("GecersizDepartman", "Seyahat", 100.0)
        self.assertEqual(tutar, 0.0)
        self.assertEqual(durum, "hata_gecersiz_butce_kalemi")

        tutar, durum = self.butce_yoneticisi.harcama_onayla("Satis", "GecersizKategori", 100.0)
        self.assertEqual(tutar, 0.0)
        self.assertEqual(durum, "hata_gecersiz_butce_kalemi")

    def test_butce_sifir_ve_esik_kullanilmis_harcama_reddi(self):
        self.butce_yoneticisi.harcama_onayla(self.harcama_asim.calisan.departman, self.harcama_asim.kategori, self.harcama_asim.tutar) 
        self.assertEqual(self.butce_yoneticisi.kalan_butceyi_getir(self.harcama_asim.calisan.departman, self.harcama_asim.kategori), 0)
        self.assertTrue(self.butce_yoneticisi.donem_icin_asim_tetiklendi)
        
        yeni_harcama_ayni_kategori = Harcama(self.calisan, 50.0, "Konaklama", dt.datetime(2025, 6, 1))
        tutar, durum = self.butce_yoneticisi.harcama_onayla(yeni_harcama_ayni_kategori.calisan.departman, yeni_harcama_ayni_kategori.kategori, yeni_harcama_ayni_kategori.tutar)
        self.assertEqual(tutar, 0.0)
        self.assertEqual(durum, "red_butce_sifir_esik_sonrasi")

    def test_butceye_iade_et(self):
        self.butce_yoneticisi.harcama_onayla("Satis", "Seyahat", 200.0)
        self.assertEqual(self.butce_yoneticisi.kalan_butceyi_getir("Satis", "Seyahat"), 200.0)
        self.assertTrue(self.butce_yoneticisi.butceye_iade_et("Satis", "Seyahat", 100.0))
        self.assertEqual(self.butce_yoneticisi.kalan_butceyi_getir("Satis", "Seyahat"), 300.0)
        self.assertFalse(self.butce_yoneticisi.butceye_iade_et("Satis", "GecersizKategori", 50.0))

    def test_butceden_dus(self):
        self.assertEqual(self.butce_yoneticisi.kalan_butceyi_getir("Satis", "Eglence"), 400.0)
        self.assertTrue(self.butce_yoneticisi.butceden_dus("Satis", "Eglence", 150.0))
        self.assertEqual(self.butce_yoneticisi.kalan_butceyi_getir("Satis", "Eglence"), 250.0)
        self.assertFalse(self.butce_yoneticisi.butceden_dus("IT", "OlmayanKategori", 50.0))
