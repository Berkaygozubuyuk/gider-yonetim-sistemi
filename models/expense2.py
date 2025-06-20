import uuid
from datetime import datetime

class Harcama:
    def __init__(self, calisan, tutar, kategori, tarih, aciklama="", belge_referansi="", receipt_id=None):
        self.calisan = calisan
        self.tutar = tutar
        self.kategori = kategori
        self.tarih = tarih
        self.aciklama = aciklama
        self.belge_referansi = belge_referansi
        self.receipt_id = receipt_id if receipt_id is not None else str(uuid.uuid4())
        self.onaylandi = False
        self.odendi = False
        self.odenen_tutar = 0.0
        self.odeme_sonrasi_durum = ""

    def __repr__(self):
        calisan_isim_str = self.calisan.isim if hasattr(self.calisan, 'isim') else str(self.calisan)
        tarih_str = self.tarih.strftime("%Y-%m-%d") if isinstance(self.tarih, datetime) else str(self.tarih)
        return (f"Harcama(receipt_id='{self.receipt_id}', calisan={calisan_isim_str}, tutar={self.tutar}, "
                f"kategori='{self.kategori}', tarih='{tarih_str}', onaylandi={self.onaylandi}, "
                f"odendi={self.odendi}, belge_ref='{self.belge_referansi}')")