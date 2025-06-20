import collections

class ButceYoneticisi:
    def __init__(self, butceler, esik_deger):
        self.butceler = {dept: {cat: tutar for cat, tutar in cats.items()} for dept, cats in butceler.items()}
        self.kalan_butceler = {dept: {cat: tutar for cat, tutar in cats.items()} for dept, cats in butceler.items()}
        self.esik_deger = esik_deger
        self.donem_icin_asim_tetiklendi = False

    def harcama_onayla(self, departman, kategori, tutar):
        if departman not in self.kalan_butceler or kategori not in self.kalan_butceler[departman]:
            return 0.0, "hata_gecersiz_butce_kalemi"

        mevcut_kalan = self.kalan_butceler[departman][kategori]

        if tutar <= 0:
            return 0.0, "hata_sifir_veya_negatif_tutar"

        if mevcut_kalan == 0 and self.donem_icin_asim_tetiklendi:
            print(f"[BUTCE_RED] Departman: {departman}, Kategori: {kategori}. Butce sifir ve esik mekanizmasi bu donem aktiflestirilmis.")
            return 0.0, "red_butce_sifir_esik_sonrasi"


        if tutar <= mevcut_kalan:
            self.kalan_butceler[departman][kategori] -= tutar
            print(f"[BUTCE_ONAY_TAM] Departman: {departman}, Kategori: {kategori}, Tutar: {tutar:.2f}. Kalan Butce: {self.kalan_butceler[departman][kategori]:.2f}")
            return tutar, "tam_odeme"
        else:
            gereken_asim = tutar - mevcut_kalan
            print(f"[BUTCE_ASIM] Departman: {departman}, Kategori: {kategori}, Tutar: {tutar:.2f}, Kalan: {mevcut_kalan:.2f}, Asim: {gereken_asim:.2f}, Esik: {self.esik_deger:.2f}")
            self.donem_icin_asim_tetiklendi = True

            if gereken_asim <= self.esik_deger:
                onaylanan_tutar = tutar
                self.kalan_butceler[departman][kategori] = 0
                print(f"[BUTCE_ONAY_ESIK_TAM] Departman: {departman}, Kategori: {kategori}, Onaylanan: {onaylanan_tutar:.2f} (esik kullanildi). Butce simdi 0.")
                return onaylanan_tutar, "tam_odeme_esik_kullanildi"
            else:
                onaylanan_tutar = mevcut_kalan + self.esik_deger
                self.kalan_butceler[departman][kategori] = 0
                print(f"[BUTCE_ONAY_ESIK_KISMI] Departman: {departman}, Kategori: {kategori}, Onaylanan: {onaylanan_tutar:.2f} (esik ile limitlendi). Butce simdi 0.")
                return onaylanan_tutar, "kismi_odeme_esik_limiti"

        print(f"[BUTCE_RED_ISLENMEDI] Departman: {departman}, Kategori: {kategori}, Tutar: {tutar:.2f}. Islenmeyen butce durumu.")
        return 0.0, "red_bilinmiyor"

    def butceye_iade_et(self, departman, kategori, tutar):
        if departman in self.kalan_butceler and kategori in self.kalan_butceler[departman]:
            self.kalan_butceler[departman][kategori] += tutar
            print(f"[BUTCE_IADE] Departman: {departman}, Kategori: {kategori}, Tutar: {tutar:.2f}. Iade sonrasi kalan butce: {self.kalan_butceler[departman][kategori]:.2f}")
            return True
        print(f"[BUTCE_IADE_HATA] Iade icin gecersiz departman/kategori: {departman}/{kategori}")
        return False

    def butceden_dus(self, departman, kategori, tutar):
        if departman in self.kalan_butceler and kategori in self.kalan_butceler[departman]:
            self.kalan_butceler[departman][kategori] -= tutar
            print(f"[BUTCE_DUSUM] Departman: {departman}, Kategori: {kategori}, Tutar: {tutar:.2f}. Dusum sonrasi kalan butce: {self.kalan_butceler[departman][kategori]:.2f}")
            return True
        print(f"[BUTCE_DUSUM_HATA] Dusum icin gecersiz departman/kategori: {departman}/{kategori}")
        return False

    def kalan_butceyi_getir(self, departman=None, kategori=None):
        if departman and kategori:
            return self.kalan_butceler.get(departman, {}).get(kategori, 0.0)
        if departman:
            return self.kalan_butceler.get(departman, {})
        return self.kalan_butceler

    def baslangic_butceyi_getir(self, departman=None):
        if departman:
            return self.butceler.get(departman, {})
        return self.butceler

    def butce_donem_bayraklarini_sifirla(self):
        self.donem_icin_asim_tetiklendi = False
        print("[BUTCE] Butce donemi bayraklari (ornegin, asim tetikleyicisi) sifirlandi.")
