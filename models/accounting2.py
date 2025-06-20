from models.expense2 import Harcama 
from models.budget2 import ButceYoneticisi

class Muhasebe:
    def __init__(self, butce_yoneticisi: ButceYoneticisi):
        self.butce_yoneticisi = butce_yoneticisi

    def geri_odeme_yap(self, harcama: Harcama):
        if harcama.onaylandi and not harcama.odendi:
            odenen_tutar, durum = self.butce_yoneticisi.harcama_onayla(
                harcama.calisan.departman, harcama.kategori, harcama.tutar
            )
            harcama.odenen_tutar = odenen_tutar
            harcama.odeme_sonrasi_durum = durum

            if odenen_tutar >= 0:  
                harcama.odendi = True

            return durum
        elif not harcama.onaylandi:
            return "hata_onaylanmamis"
        elif harcama.odendi:
            return "hata_zaten_odenmis"
        return "hata_bilinmiyor"

    def harcama_kategorisi_guncelle(self, guncellenecek_harcama: Harcama, yeni_kategori: str):
        calisan_departmani = guncellenecek_harcama.calisan.departman
        eski_kategori = guncellenecek_harcama.kategori

        if eski_kategori == yeni_kategori:
            return "bilgi_ayni_kategori"

        if not (calisan_departmani in self.butce_yoneticisi.butceler and \
                yeni_kategori in self.butce_yoneticisi.butceler[calisan_departmani]):
            print(f"[MUHASEBE_HATA] Yeni kategori '{yeni_kategori}' departman '{calisan_departmani}' icin gecerli degil.")
            return "hata_gecersiz_yeni_kategori"

        if guncellenecek_harcama.odendi:
            ayarlanacak_tutar = guncellenecek_harcama.odenen_tutar
            if ayarlanacak_tutar > 0: 
                print(f"[MUHASEBE] Odenmis harcama icin butceler ayarlaniyor. Departman: {calisan_departmani}, Eski Kat: {eski_kategori}, Yeni Kat: {yeni_kategori}, Tutar: {ayarlanacak_tutar}")
                iade_basarili = self.butce_yoneticisi.butceye_iade_et(calisan_departmani, eski_kategori, ayarlanacak_tutar)
                dusum_basarili = self.butce_yoneticisi.butceden_dus(calisan_departmani, yeni_kategori, ayarlanacak_tutar)

                if not iade_basarili:
                    print(f"[MUHASEBE_UYARI] {calisan_departmani}-{eski_kategori} icin butce iadesi basarisiz.")
                if not dusum_basarili:
                    print(f"[MUHASEBE_UYARI] {calisan_departmani}-{yeni_kategori} icin butce dusumu basarisiz.")
        
        guncellenecek_harcama.kategori = yeni_kategori
        print(f"[MUHASEBE] {guncellenecek_harcama.calisan.isim} (Tutar: {guncellenecek_harcama.tutar}) icin harcama kategorisi '{eski_kategori}' -> '{yeni_kategori}' olarak guncellendi.")
        return "basarili"
