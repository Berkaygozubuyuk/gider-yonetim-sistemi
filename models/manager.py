import uuid
from models.employee import Calisan
from models.expense2 import Harcama

class Yonetici(Calisan):
    def __init__(self, isim, departman, manager_id=None):
        super().__init__(isim, departman)
        self.manager_id = manager_id if manager_id is not None else str(uuid.uuid4())
        self.onaylanan_harcamalar = []

    def harcama_onayla(self, harcama: Harcama):
        if harcama.tutar > 0 :
            harcama.onaylandi = True
            print(f"[BILGI] Yonetici {self.isim} tarafindan {harcama.calisan.isim} icin harcama onaylandi (Tutar: {harcama.tutar}, Kategori: {harcama.kategori})")
        else:
            print(f"[HATA] Yonetici {self.isim}, {harcama.calisan.isim} icin pozitif olmayan tutarda harcamayi onaylayamaz.")

    def __repr__(self):
        return f"Yonetici(manager_id='{self.manager_id}', isim='{self.isim}', departman='{self.departman}')"