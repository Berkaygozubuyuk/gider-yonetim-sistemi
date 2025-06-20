import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import collections
import json
import traceback

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from models.employee import Calisan
from models.manager import Yonetici
from models.expense2 import Harcama
from models.accounting2 import Muhasebe
from models.budget2 import ButceYoneticisi


class hareketli_ortalama_hesapla:
    @staticmethod
    def hareketli_ortalama(veri, pencere_boyutu):
        if not veri or pencere_boyutu <= 0 or len(veri) < pencere_boyutu:
            return None
        return sum(veri[-pencere_boyutu:]) / pencere_boyutu


VERI_DOSYASI = "harcama_verileri.json"
calisanlar = {}
yoneticiler = {}
harcamalar = {}


def verileri_kaydet():
    global calisanlar, yoneticiler, harcamalar
    kaydedilecek_veri = {
        "calisanlar": {calisan.employee_id: calisan.__dict__ for calisan in calisanlar.values()},
        "yoneticiler": {yonetici.manager_id: yonetici.__dict__ for yonetici in yoneticiler.values()},
        "harcamalar": []
    }
    for harcama_obj in harcamalar.values():
        harcama_dict = harcama_obj.__dict__.copy()
        if isinstance(harcama_dict.get('calisan'), (Calisan, Yonetici)):
            harcama_dict['calisan_id'] = harcama_dict['calisan'].employee_id
            del harcama_dict['calisan']
        if isinstance(harcama_dict.get('tarih'), datetime):
            harcama_dict['tarih'] = harcama_dict['tarih'].strftime("%Y-%m-%d")
        kaydedilecek_veri["harcamalar"].append(harcama_dict)

    try:
        with open(VERI_DOSYASI, 'w', encoding='utf-8') as f:
            json.dump(kaydedilecek_veri, f, indent=4)
        print(f"[BILGI] Veriler '{VERI_DOSYASI}' dosyasina basariyla kaydedildi.")
    except Exception as e:
        print(f"[HATA] Veriler kaydedilirken hata olustu: {e}")


def verileri_yukle():
    global calisanlar, yoneticiler, harcamalar
    try:
        with open(VERI_DOSYASI, 'r', encoding='utf-8') as f:
            yuklenen_veri = json.load(f)

        calisanlar.clear()
        for emp_id, calisan_dict in yuklenen_veri.get("calisanlar", {}).items():
            calisan_obj = Calisan(
                isim=calisan_dict['isim'],
                departman=calisan_dict['departman'],
                employee_id=calisan_dict['employee_id']
            )
            calisanlar[emp_id] = calisan_obj

        yoneticiler.clear()
        for mgr_id, yonetici_dict in yuklenen_veri.get("yoneticiler", {}).items():
            yonetici_obj = Yonetici(
                isim=yonetici_dict['isim'],
                departman=yonetici_dict['departman'],
                manager_id=yonetici_dict['manager_id']
            )
            yoneticiler[mgr_id] = yonetici_obj

        harcamalar.clear()
        for harcama_dict in yuklenen_veri.get("harcamalar", []):
            calisan_id = harcama_dict.get('calisan_id')
            calisan_obj = calisanlar.get(calisan_id) or yoneticiler.get(calisan_id)

            if not calisan_obj:
                print(f"[UYARI] Harcama {harcama_dict.get('receipt_id')} icin calisan bulunamadi: {calisan_id}. Harcama yuklenmedi.")
                continue

            harcama_obj = Harcama(
                calisan=calisan_obj,
                tutar=harcama_dict['tutar'],
                kategori=harcama_dict['kategori'],
                tarih=datetime.strptime(harcama_dict['tarih'], "%Y-%m-%d") if isinstance(harcama_dict['tarih'], str) else harcama_dict['tarih'],
                aciklama=harcama_dict.get('aciklama', ''),
                belge_referansi=harcama_dict.get('belge_referansi', ''),
                receipt_id=harcama_dict['receipt_id']
            )
            harcama_obj.onaylandi = harcama_dict.get('onaylandi', False)
            harcama_obj.odendi = harcama_dict.get('odendi', False)
            harcama_obj.odenen_tutar = harcama_dict.get('odenen_tutar', 0.0)
            harcama_obj.odeme_sonrasi_durum = harcama_dict.get('odeme_sonrasi_durum', '')
            harcamalar[harcama_obj.receipt_id] = harcama_obj

        print(f"[BILGI] Veriler '{VERI_DOSYASI}' dosyasindan basariyla yuklendi.")
    except FileNotFoundError:
        print(f"[BILGI] '{VERI_DOSYASI}' dosyasi bulunamadi. Yeni bir dosya olusturulacak.")
    except Exception as e:
        print(f"[HATA] Veriler yuklenirken hata olustu: {e}")
        traceback.print_exc()


def butce_baslat():
    root_init = tk.Tk()
    root_init.withdraw()

    departmanlar_str = simpledialog.askstring("Departmanlar", "Departmanlari virgulle ayirarak girin (orn: IT,Pazarlama):", parent=root_init)
    if not departmanlar_str:
        messagebox.showerror("Hata", "En az bir departman tanimlanmalidir!", parent=root_init)
        root_init.destroy()
        raise SystemExit("Departman tanimlamasi yapilmadi.")
    departmanlar_listesi = [d.strip() for d in departmanlar_str.split(',') if d.strip()]

    kategoriler_str = simpledialog.askstring("Kategoriler", "Harcama kategorilerini virgulle ayirarak girin (orn: Ulasim,Konaklama):", parent=root_init)
    if not kategoriler_str:
        messagebox.showerror("Hata", "En az bir kategori tanimlanmalidir!", parent=root_init)
        root_init.destroy()
        raise SystemExit("Kategori tanimlamasi yapilmadi.")
    tanimli_kategoriler = [c.strip() for c in kategoriler_str.split(',') if c.strip()]

    butceler_dict = {}
    for dept in departmanlar_listesi:
        butceler_dict[dept] = {}
        for cat in tanimli_kategoriler:
            tutar_val = simpledialog.askfloat("Butce", f"{dept} - {cat} icin butce tutari (TL):", minvalue=0.0, parent=root_init)
            if tutar_val is None:
                if messagebox.askretrycancel("Butce Girisi Eksik", f"{dept} - {cat} icin butce girilmedi. Tekrar denemek ister misiniz?", parent=root_init):
                    tutar_val = simpledialog.askfloat("Butce", f"{dept} - {cat} icin butce tutari (TL):", minvalue=0.0, parent=root_init)
                    if tutar_val is None:
                         messagebox.showwarning("Uyari", f"{dept} - {cat} icin butce 0.0 TL olarak ayarlandi.", parent=root_init)
                         butceler_dict[dept][cat] = 0.0
                    else:
                        butceler_dict[dept][cat] = tutar_val
                else:
                    messagebox.showwarning("Uyari", f"{dept} - {cat} icin butce 0.0 TL olarak ayarlandi.", parent=root_init)
                    butceler_dict[dept][cat] = 0.0
            else:
                butceler_dict[dept][cat] = tutar_val

    esik_deger_val = simpledialog.askfloat("Butce Asim Esigi", "Butce asim tolerans esigi (TL):", minvalue=0.0, parent=root_init)
    if esik_deger_val is None:
        messagebox.showwarning("Uyari", "Butce asim esigi 0.0 TL olarak ayarlandi.", parent=root_init)
        esik_deger_val = 0.0

    root_init.destroy()
    return ButceYoneticisi(butceler=butceler_dict, esik_deger=esik_deger_val)

class HarcamaUygulamasi(tk.Tk):
    def __init__(self, muhasebe_sistemi: Muhasebe):
        super().__init__()
        self.title("Gider Yonetim Sistemi")
        self.geometry("1200x800")
        self.muhasebe = muhasebe_sistemi
        self.protocol("WM_DELETE_WINDOW", self._kapatirken)

        stil = ttk.Style(self)
        stil.theme_use('clam')

        stil.configure("TFrame", background="#e0e0e0")
        stil.configure("TButton", padding=6, relief="flat", background="#007bff", foreground="white", font=('Segoe UI Variable Text', 10, 'bold'))
        stil.map("TButton", background=[('active', '#0056b3')])
        stil.configure("TLabel", background="#e0e0e0", font=('Segoe UI Variable Text', 10))
        stil.configure("Header.TLabel", font=('Segoe UI Variable Text', 16, 'bold'), background="#e0e0e0")
        stil.configure("Treeview.Heading", font=('Segoe UI Variable Text', 10, 'bold'))
        stil.configure("Treeview", font=('Segoe UI Variable Text', 9), rowheight=25)
        stil.configure("Sidebar.TFrame", background="#f8f9fa")
        stil.configure("Sidebar.TButton", font=('Segoe UI Variable Text', 10), width=30)
        stil.configure("Content.TFrame", background="white", relief="sunken", borderwidth=1)

        self._arayuzu_olustur()
        self.kategori_guncelleme_icin_secili_harcama_id = None
        self.kategori_guncelleme_harcama_agaci = None


    def _kapatirken(self):
        if messagebox.askokcancel("Cikis", "Uygulamadan cikmak istiyor musunuz? Degisiklikler kaydedilecek.", parent=self):
            verileri_kaydet()
            self.destroy()

    def _departman_var_mi(self, dept: str) -> bool:
        return dept in self.muhasebe.butce_yoneticisi.butceler

    def _kategori_var_mi(self, dept: str, cat: str) -> bool:
        return self._departman_var_mi(dept) and cat in self.muhasebe.butce_yoneticisi.butceler[dept]

    def _arayuzu_olustur(self):
        yan_menu = ttk.Frame(self, width=300, style="Sidebar.TFrame")
        yan_menu.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        yan_menu.pack_propagate(False)

        islemler = [
            ("Calisan Ekle", self._calisan_ekle_arayuzu),
            ("Yonetici Ekle", self._yonetici_ekle_arayuzu),
            ("Gider Gonder", self._harcama_gonder_arayuzu),
            ("Gider Onayla", self._harcama_onayla_arayuzu),
            ("Gider Ode", self._harcama_ode_arayuzu),
            ("Gider Kategorisi Guncelle", self._harcama_kategorisi_guncelle_arayuzu),
            ("Listeler", self._listeleri_goster_arayuzu),
            ("Raporlar ve Tahmin", self._rapor_arayuzu),
            ("Butce Donemini Sifirla", self._butce_donemini_sifirla_arayuzu),
            ("Verileri Kaydet", verileri_kaydet)
        ]

        ttk.Label(yan_menu, text="Islemler", font=('Segoe UI Variable Text', 14, 'bold'), background="#f8f9fa", padding=(0,10)).pack(pady=5)
        for (metin, komut) in islemler:
            btn = ttk.Button(yan_menu, text=metin, command=komut, style="Sidebar.TButton")
            btn.pack(fill=tk.X, padx=10, pady=3)

        self.ana_cerceve = ttk.Frame(self, style="Content.TFrame")
        self.ana_cerceve.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=5, pady=5)
        self._hosgeldin_ekranini_goster()

    def _ana_ekrani_temizle(self):
        for widget in self.ana_cerceve.winfo_children():
            widget.destroy()
        self.kategori_guncelleme_icin_secili_harcama_id = None
        self.kategori_guncelleme_harcama_agaci = None


    def _hosgeldin_ekranini_goster(self):
        self._ana_ekrani_temizle()
        ttk.Label(self.ana_cerceve, text="Gider Yonetim Sistemine Hosgeldiniz!", style="Header.TLabel", anchor="center").pack(pady=30, fill=tk.X, padx=2)
        ttk.Label(self.ana_cerceve, text="Lutfen sol menuden bir islem secin.", font=('Segoe UI Variable Text', 12), background="white", anchor="center").pack(pady=10, fill=tk.X, padx=2)

    def _form_alani_olustur(self, parent, etiket_metni, degisken, giris_genisligi=30):
        cerceve = ttk.Frame(parent, style="Content.TFrame")
        cerceve.pack(fill=tk.X, padx=20, pady=5)
        ttk.Label(cerceve, text=etiket_metni, width=20, anchor="w", background="white").pack(side=tk.LEFT)
        giris = ttk.Entry(cerceve, textvariable=degisken, width=giris_genisligi)
        giris.pack(side=tk.LEFT, expand=True, fill=tk.X)
        return giris

    def _calisan_ekle_arayuzu(self):
        self._ana_ekrani_temizle()
        ttk.Label(self.ana_cerceve, text="Yeni Calisan Ekle", style="Header.TLabel").pack(pady=20)
        isim_var = tk.StringVar()
        dept_var = tk.StringVar()

        self._form_alani_olustur(self.ana_cerceve, "Isim Soyisim:", isim_var)
        dept_cerceve = ttk.Frame(self.ana_cerceve, style="Content.TFrame")
        dept_cerceve.pack(fill=tk.X, padx=20, pady=5)
        ttk.Label(dept_cerceve, text="Departman:", width=20, anchor="w", background="white").pack(side=tk.LEFT)
        dept_combobox = ttk.Combobox(dept_cerceve, textvariable=dept_var, values=list(self.muhasebe.butce_yoneticisi.butceler.keys()), state="readonly", width=28)
        dept_combobox.pack(side=tk.LEFT, expand=True, fill=tk.X)

        def calisan_ekle_action():
            isim = isim_var.get().strip()
            dept = dept_var.get().strip()
            if not isim or not dept:
                messagebox.showerror("Hata", "Isim ve departman bos birakilamaz!", parent=self.ana_cerceve)
                return
            if not self._departman_var_mi(dept):
                messagebox.showerror("Hata", f"'{dept}' departmani sistemde tanimli degil!", parent=self.ana_cerceve)
                return
            if any(calisan.isim == isim for calisan in calisanlar.values()):
                 messagebox.showerror("Hata", f"'{isim}' isimli calisan zaten mevcut!", parent=self.ana_cerceve)
                 return

            yeni_calisan = Calisan(isim, dept)
            calisanlar[yeni_calisan.employee_id] = yeni_calisan
            verileri_kaydet()
            messagebox.showinfo("Basarili", f"{isim} adli calisan basariyla eklendi (ID: {yeni_calisan.employee_id}).", parent=self.ana_cerceve)
            self._hosgeldin_ekranini_goster()
        ttk.Button(self.ana_cerceve, text="Calisani Kaydet", command=calisan_ekle_action).pack(pady=20)

    def _yonetici_ekle_arayuzu(self):
        self._ana_ekrani_temizle()
        ttk.Label(self.ana_cerceve, text="Yeni Yonetici Ekle", style="Header.TLabel").pack(pady=20)
        isim_var = tk.StringVar()
        dept_var = tk.StringVar()
        self._form_alani_olustur(self.ana_cerceve, "Isim Soyisim:", isim_var)
        dept_cerceve = ttk.Frame(self.ana_cerceve, style="Content.TFrame")
        dept_cerceve.pack(fill=tk.X, padx=20, pady=5)
        ttk.Label(dept_cerceve, text="Departman:", width=20, anchor="w", background="white").pack(side=tk.LEFT)
        dept_combobox = ttk.Combobox(dept_cerceve, textvariable=dept_var, values=list(self.muhasebe.butce_yoneticisi.butceler.keys()), state="readonly", width=28)
        dept_combobox.pack(side=tk.LEFT, expand=True, fill=tk.X)

        def yonetici_ekle_action():
            isim = isim_var.get().strip()
            dept = dept_var.get().strip()
            if not isim or not dept:
                messagebox.showerror("Hata", "Isim ve departman bos birakilamaz!", parent=self.ana_cerceve)
                return
            if not self._departman_var_mi(dept):
                messagebox.showerror("Hata", f"'{dept}' departmani sistemde tanimli degil!", parent=self.ana_cerceve)
                return
            if any(yonetici.isim == isim for yonetici in yoneticiler.values()):
                messagebox.showerror("Hata", f"'{isim}' isimli yonetici zaten mevcut!", parent=self.ana_cerceve)
                return

            yeni_yonetici = Yonetici(isim, dept)
            yoneticiler[yeni_yonetici.manager_id] = yeni_yonetici
            verileri_kaydet()
            messagebox.showinfo("Basarili", f"{isim} adli yonetici basariyla eklendi (ID: {yeni_yonetici.manager_id}).", parent=self.ana_cerceve)
            self._hosgeldin_ekranini_goster()
        ttk.Button(self.ana_cerceve, text="Yoneticiyi Kaydet", command=yonetici_ekle_action).pack(pady=20)

    def _harcama_gonder_arayuzu(self):
        self._ana_ekrani_temizle()
        ttk.Label(self.ana_cerceve, text="Yeni Gider Talebi Olustur", style="Header.TLabel").pack(pady=20)

        gider_gonderebilecekler = {**calisanlar, **yoneticiler}

        if not gider_gonderebilecekler:
            messagebox.showinfo("Bilgi", "Gider gonderebilmek icin once sisteme calisan veya yonetici eklenmelidir.", parent=self.ana_cerceve)
            self._hosgeldin_ekranini_goster()
            return

        emp_id_var = tk.StringVar()
        emp_isim_var = tk.StringVar()
        tutar_var = tk.DoubleVar()
        cat_var = tk.StringVar()
        tarih_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        aciklama_var = tk.StringVar()
        doc_ref_var = tk.StringVar()

        emp_cerceve = ttk.Frame(self.ana_cerceve, style="Content.TFrame")
        emp_cerceve.pack(fill=tk.X, padx=20, pady=5)
        ttk.Label(emp_cerceve, text="Calisan/Yonetici Adi:", width=20, anchor="w", background="white").pack(side=tk.LEFT)
        emp_combobox = ttk.Combobox(emp_cerceve, textvariable=emp_isim_var, values=[kisi.isim for kisi in gider_gonderebilecekler.values()], state="readonly", width=28)
        emp_combobox.pack(side=tk.LEFT, expand=True, fill=tk.X)

        def secili_kullaniciyi_ayarla(*args):
            secili_isim = emp_isim_var.get()
            for kisi_id, kisi_obj in gider_gonderebilecekler.items():
                if kisi_obj.isim == secili_isim:
                    emp_id_var.set(kisi_id)
                    kategorileri_ve_butce_durumunu_guncelle()
                    break

        emp_isim_var.trace_add("write", secili_kullaniciyi_ayarla)

        self._form_alani_olustur(self.ana_cerceve, "Tutar (TL):", tutar_var)

        cat_cerceve = ttk.Frame(self.ana_cerceve, style="Content.TFrame")
        cat_cerceve.pack(fill=tk.X, padx=20, pady=5)
        ttk.Label(cat_cerceve, text="Kategori:", width=20, anchor="w", background="white").pack(side=tk.LEFT)
        cat_combobox = ttk.Combobox(cat_cerceve, textvariable=cat_var, state="readonly", width=28)
        cat_combobox.pack(side=tk.LEFT, expand=True, fill=tk.X)

        butce_durum_etiketi = ttk.Label(self.ana_cerceve, text="", style="TLabel", background="white", foreground="blue")
        butce_durum_etiketi.pack(fill=tk.X, padx=20, pady=2)

        def kategorileri_ve_butce_durumunu_guncelle(*args):
            secili_kullanici_id = emp_id_var.get()
            secili_cat_yuklenirken = cat_var.get()

            if secili_kullanici_id in gider_gonderebilecekler:
                kullanici_obj = gider_gonderebilecekler[secili_kullanici_id]
                emp_dept = kullanici_obj.departman
                if self._departman_var_mi(emp_dept):
                    mevcut_kategoriler = list(self.muhasebe.butce_yoneticisi.butceler[emp_dept].keys())
                    cat_combobox['values'] = mevcut_kategoriler
                    if secili_cat_yuklenirken in mevcut_kategoriler:
                        cat_var.set(secili_cat_yuklenirken)
                    elif mevcut_kategoriler:
                         cat_combobox.current(0)
                         cat_var.set(cat_combobox.get())
                    else:
                        cat_var.set("")


                    butce_icin_guncel_cat = cat_var.get()
                    if butce_icin_guncel_cat:
                        kalan = self.muhasebe.butce_yoneticisi.kalan_butceyi_getir(emp_dept, butce_icin_guncel_cat)
                        butce_durum_etiketi.config(text=f"Secili Kategori ({butce_icin_guncel_cat}) Kalan Butce: {kalan:.2f} TL")
                        if kalan == 0 and self.muhasebe.butce_yoneticisi.donem_icin_asim_tetiklendi:
                             butce_durum_etiketi.config(text=f"UYARI: {butce_icin_guncel_cat} butcesi tukendi ve esik kullanildi. Yeni harcama reddedilebilir.", foreground="red")
                        elif kalan == 0:
                            butce_durum_etiketi.config(text=f"UYARI: {butce_icin_guncel_cat} butcesi tukendi. Harcama esik ile karsilanabilir.", foreground="orange")
                        else:
                            butce_durum_etiketi.config(foreground="blue")
                    else:
                        butce_durum_etiketi.config(text="Bu departman icin kategori bulunamadi veya secilmedi.")
                else:
                    cat_combobox['values'] = []
                    cat_var.set("")
                    butce_durum_etiketi.config(text=f"'{emp_dept}' departmani icin butce tanimi yok.")
            else:
                cat_combobox['values'] = []
                cat_var.set("")
                butce_durum_etiketi.config(text="")

        cat_var.trace_add("write", kategorileri_ve_butce_durumunu_guncelle)

        if gider_gonderebilecekler:
            ilk_kisi_id = list(gider_gonderebilecekler.keys())[0]
            emp_id_var.set(ilk_kisi_id)
            emp_isim_var.set(gider_gonderebilecekler[ilk_kisi_id].isim)
            kategorileri_ve_butce_durumunu_guncelle()


        self._form_alani_olustur(self.ana_cerceve, "Tarih (YYYY-AA-GG):", tarih_var)
        self._form_alani_olustur(self.ana_cerceve, "Aciklama:", aciklama_var)
        self._form_alani_olustur(self.ana_cerceve, "Belge Referansi:", doc_ref_var)

        def harcama_gonder_action():
            secili_kullanici_id = emp_id_var.get()
            tutar_val = tutar_var.get()
            kategori_val = cat_var.get()
            tarih_str = tarih_var.get()
            aciklama_val = aciklama_var.get().strip()
            doc_ref_val = doc_ref_var.get().strip()

            if not secili_kullanici_id or not kategori_val or tutar_val <= 0:
                messagebox.showerror("Hata", "Calisan/Yonetici, kategori ve pozitif bir tutar girilmelidir!", parent=self.ana_cerceve)
                return

            calisan_obj = gider_gonderebilecekler.get(secili_kullanici_id)
            if not calisan_obj:
                messagebox.showerror("Hata", "Secilen calisan/yonetici bulunamadi!", parent=self.ana_cerceve)
                return

            emp_dept = calisan_obj.departman

            if not self._kategori_var_mi(emp_dept, kategori_val):
                messagebox.showerror("Hata", f"'{kategori_val}' kategorisi '{emp_dept}' departmani icin tanimli degil veya gecerli bir secim yapilmadi!", parent=self.ana_cerceve)
                return
            try:
                harcama_tarih = datetime.strptime(tarih_str, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Hata", "Gecersiz tarih formati. LutfenYYYY-AA-GG formatini kullanin.", parent=self.ana_cerceve)
                return

            yeni_harcama = Harcama(calisan_obj, tutar_val, kategori_val, harcama_tarih, aciklama_val, doc_ref_val)
            harcamalar[yeni_harcama.receipt_id] = yeni_harcama
            verileri_kaydet()
            messagebox.showinfo("Basarili", f"Gider talebi basariyla gonderildi (ID: {yeni_harcama.receipt_id}).", parent=self.ana_cerceve)
            self._hosgeldin_ekranini_goster()
        ttk.Button(self.ana_cerceve, text="Gideri Gonder", command=harcama_gonder_action).pack(pady=20)


    def _harcama_onayla_arayuzu(self):
        self._ana_ekrani_temizle()
        ttk.Label(self.ana_cerceve, text="Bekleyen Gider Onaylari", style="Header.TLabel").pack(pady=20)

        if not yoneticiler:
            messagebox.showinfo("Bilgi", "Gider onayi icin once sisteme yonetici eklenmelidir.", parent=self.ana_cerceve)
            self._hosgeldin_ekranini_goster()
            return

        onay_bekleyen_harcamalar = {hid: h for hid, h in harcamalar.items() if not h.onaylandi}

        if not onay_bekleyen_harcamalar:
            ttk.Label(self.ana_cerceve, text="Onay bekleyen gider bulunmamaktadir.", background="white").pack(pady=10)
            return

        mgr_var = tk.StringVar()
        mgr_cerceve = ttk.Frame(self.ana_cerceve, style="Content.TFrame")
        mgr_cerceve.pack(fill=tk.X, padx=20, pady=5)
        ttk.Label(mgr_cerceve, text="Onaylayan Yonetici:", width=20, anchor="w", background="white").pack(side=tk.LEFT)
        mgr_combobox = ttk.Combobox(mgr_cerceve, textvariable=mgr_var, values=[mgr.isim for mgr in yoneticiler.values()], state="readonly", width=28)
        mgr_combobox.pack(side=tk.LEFT, expand=True, fill=tk.X)
        if yoneticiler: mgr_combobox.current(0)

        sutunlar = ("ID", "Calisan", "Departman", "Tutar", "Kategori", "Tarih", "Belge Ref.", "Aciklama")
        agac = ttk.Treeview(self.ana_cerceve, columns=sutunlar, show='headings', selectmode="browse")
        for sutun in sutunlar:
            agac.heading(sutun, text=sutun)
            agac.column(sutun, width=100, anchor="w")
        agac.column("ID", width=80)
        agac.column("Aciklama", width=150)
        agac.column("Belge Ref.", width=100)


        for harcama_id, harcama_obj in onay_bekleyen_harcamalar.items():
            agac.insert("", tk.END, iid=harcama_id, values=(
                harcama_id,
                harcama_obj.calisan.isim, harcama_obj.calisan.departman,
                f"{harcama_obj.tutar:.2f} TL", harcama_obj.kategori, harcama_obj.tarih.strftime("%Y-%m-%d"),
                harcama_obj.belge_referansi, harcama_obj.aciklama
            ))
        agac.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        def secili_harcamayi_onayla():
            secili_oge_iid = agac.focus()
            if not secili_oge_iid:
                messagebox.showwarning("Uyari", "Lutfen onaylamak icin bir gider secin.", parent=self.ana_cerceve)
                return
            mgr_isim = mgr_var.get()
            if not mgr_isim:
                 messagebox.showerror("Hata", "Lutfen onaylayan yonetici secin.", parent=self.ana_cerceve)
                 return

            yonetici_obj = None
            for mgr in yoneticiler.values():
                if mgr.isim == mgr_isim:
                    yonetici_obj = mgr
                    break

            if not yonetici_obj:
                 messagebox.showerror("Hata", "Secilen yonetici bulunamadi.", parent=self.ana_cerceve)
                 return


            onaylanacak_harcama = harcamalar.get(secili_oge_iid)

            if not onaylanacak_harcama:
                 messagebox.showerror("Hata", "Secili harcama sistemde bulunamadi.", parent=self.ana_cerceve)
                 return


            if yonetici_obj.departman != onaylanacak_harcama.calisan.departman:
                messagebox.showerror("Hata", f"Yonetici {yonetici_obj.isim} ({yonetici_obj.departman}), {onaylanacak_harcama.calisan.isim} adli calisanin ({onaylanacak_harcama.calisan.departman}) giderini onaylayamaz.", parent=self.ana_cerceve)
                return

            yonetici_obj.harcama_onayla(onaylanacak_harcama)
            verileri_kaydet()
            messagebox.showinfo("Basarili", f"{onaylanacak_harcama.calisan.isim} icin gider onaylandi (ID: {onaylanacak_harcama.receipt_id}).", parent=self.ana_cerceve)
            self._harcama_onayla_arayuzu()
        ttk.Button(self.ana_cerceve, text="Secili Gideri Onayla", command=secili_harcamayi_onayla).pack(pady=10)

    def _harcama_ode_arayuzu(self):
        self._ana_ekrani_temizle()
        ttk.Label(self.ana_cerceve, text="Odenecek Giderler", style="Header.TLabel").pack(pady=20)

        odenecekler = {hid: h for hid, h in harcamalar.items() if h.onaylandi and not h.odendi}

        if not odenecekler:
            ttk.Label(self.ana_cerceve, text="Odeme bekleyen onayli gider bulunmamaktadir.", background="white").pack(pady=10)
            return

        sutunlar = ("ID", "Calisan", "Talep Edilen", "Kategori", "Tarih", "Belge Ref.")
        agac = ttk.Treeview(self.ana_cerceve, columns=sutunlar, show='headings', selectmode="browse")
        for sutun in sutunlar: agac.heading(sutun, text=sutun); agac.column(sutun, width=120, anchor="w")
        agac.column("ID", width=80)

        for harcama_id, harcama_obj in odenecekler.items():
            agac.insert("", tk.END, iid=harcama_id, values=(
                harcama_id,
                harcama_obj.calisan.isim, f"{harcama_obj.tutar:.2f} TL",
                harcama_obj.kategori, harcama_obj.tarih.strftime("%Y-%m-%d"), harcama_obj.belge_referansi
            ))
        agac.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        def secili_harcamayi_ode():
            secili_oge_iid = agac.focus()
            if not secili_oge_iid:
                messagebox.showwarning("Uyari", "Lutfen odemek icin bir gider secin.", parent=self.ana_cerceve)
                return

            odenecek_harcama = harcamalar.get(secili_oge_iid)

            if not odenecek_harcama:
                 messagebox.showerror("Hata", "Secili harcama sistemde bulunamadi.", parent=self.ana_cerceve)
                 return

            durum = self.muhasebe.geri_odeme_yap(odenecek_harcama)

            mesaj_basligi = "Odeme Sonucu"
            mesaj_detayi = ""

            if durum == "tam_odeme":
                mesaj_detayi = f"Gider tamamen odendi. Odenen Tutar: {odenecek_harcama.odenen_tutar:.2f} TL."
                messagebox.showinfo(mesaj_basligi, mesaj_detayi, parent=self.ana_cerceve)
            elif durum == "tam_odeme_esik_kullanildi":
                mesaj_detayi = (f"Gider butce ve esik kullanilarak tamamen odendi. "
                              f"Odenen Tutar: {odenecek_harcama.odenen_tutar:.2f} TL.\n"
                              f"Butce asim esigi bu donem icin aktiflesti.")
                messagebox.showwarning(mesaj_basligi, mesaj_detayi, parent=self.ana_cerceve)
            elif durum == "kismi_odeme_esik_limiti":
                mesaj_detayi = (f"Gider kismen odendi (esik ile limitlendi). "
                              f"Odenen Tutar: {odenecek_harcama.odenen_tutar:.2f} TL (Talep: {odenecek_harcama.tutar:.2f} TL).\n"
                              f"Butce asim esigi bu donem icin aktiflesti.")
                messagebox.showwarning(mesaj_basligi, mesaj_detayi, parent=self.ana_cerceve)
            elif durum == "red_butce_sifir_esik_sonrasi":
                 mesaj_detayi = "Odeme reddedildi. Ilgili butce kalemi sifir ve esik mekanizmasi bu donem icin daha once tetiklenmis."
                 messagebox.showerror(mesaj_basligi, mesaj_detayi, parent=self.ana_cerceve)
            elif durum == "hata_onaylanmamis":
                 mesaj_detayi = "Odeme yapilamadi: Gider henuz onaylanmamis."
                 messagebox.showerror(mesaj_basligi, mesaj_detayi, parent=self.ana_cerceve)
            elif durum == "hata_zaten_odenmis":
                 mesaj_detayi = "Odeme yapilamadi: Gider zaten odenmis."
                 messagebox.showerror(mesaj_basligi, mesaj_detayi, parent=self.ana_cerceve)
            elif durum == "red_bilinmiyor" or durum.startswith("hata_"):
                 mesaj_detayi = f"Odeme yapilamadi. Durum: {durum}"
                 messagebox.showerror(mesaj_basligi, mesaj_detayi, parent=self.ana_cerceve)
            else:
                 mesaj_detayi = f"Bilinmeyen odeme durumu: {durum}"
                 messagebox.showerror(mesaj_basligi, mesaj_detayi, parent=self.ana_cerceve)

            verileri_kaydet()
            self._harcama_ode_arayuzu()

        ttk.Button(self.ana_cerceve, text="Secili Gideri Ode", command=secili_harcamayi_ode).pack(pady=10)

    def _harcama_kategorisi_guncelle_arayuzu(self):
        self._ana_ekrani_temizle()
        ttk.Label(self.ana_cerceve, text="Gider Kategorisi Guncelleme (Muhasebe)", style="Header.TLabel").pack(pady=10)

        if not harcamalar:
            ttk.Label(self.ana_cerceve, text="Sistemde guncellenecek gider bulunmamaktadir.", background="white").pack(pady=10)
            return

        secim_cercevesi = ttk.Frame(self.ana_cerceve, style="Content.TFrame")
        secim_cercevesi.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        ttk.Label(secim_cercevesi, text="Guncellenecek Gideri Secin:", background="white", font=('Segoe UI Variable Text', 11, 'bold')).pack(pady=5, anchor="w")

        sutunlar = ("ID", "Calisan", "Departman", "Mevcut Kategori", "Tutar (TL)", "Tarih", "Onay", "Odeme")
        self.kategori_guncelleme_harcama_agaci = ttk.Treeview(secim_cercevesi, columns=sutunlar, show='headings', selectmode="browse", height=10)
        for sutun in sutunlar:
            self.kategori_guncelleme_harcama_agaci.heading(sutun, text=sutun)
            self.kategori_guncelleme_harcama_agaci.column(sutun, width=110, anchor="w", minwidth=60)
        self.kategori_guncelleme_harcama_agaci.column("ID", width=100, anchor="center")
        self.kategori_guncelleme_harcama_agaci.column("Tutar (TL)", width=80, anchor="e")

        self._kategori_guncelleme_harcama_agacini_doldur()
        self.kategori_guncelleme_harcama_agaci.pack(fill=tk.BOTH, expand=True, pady=5)

        form_cercevesi = ttk.Frame(self.ana_cerceve, style="Content.TFrame")
        form_cercevesi.pack(fill=tk.X, padx=10, pady=10)

        self.secili_harcama_etiketi = ttk.Label(form_cercevesi, text="Secili Gider: -", background="white", font=('Segoe UI Variable Text', 10, 'italic'))
        self.secili_harcama_etiketi.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        ttk.Label(form_cercevesi, text="Yeni Kategori:", background="white").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.yeni_kategori_var = tk.StringVar()
        self.yeni_kategori_combobox = ttk.Combobox(form_cercevesi, textvariable=self.yeni_kategori_var, state="disabled", width=30)
        self.yeni_kategori_combobox.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        guncelle_butonu = ttk.Button(form_cercevesi, text="Kategoriyi Guncelle", command=self._kategori_guncelleme_yap, state="disabled")
        guncelle_butonu.grid(row=2, column=0, columnspan=2, pady=10)

        def harcama_secildiginde(event):
            secili_oge_iid = self.kategori_guncelleme_harcama_agaci.focus()
            if not secili_oge_iid:
                self.kategori_guncelleme_icin_secili_harcama_id = None
                self.secili_harcama_etiketi.config(text="Secili Gider: -")
                self.yeni_kategori_combobox.set('')
                self.yeni_kategori_combobox['values'] = []
                self.yeni_kategori_combobox.config(state="disabled")
                guncelle_butonu.config(state="disabled")
                return

            self.kategori_guncelleme_icin_secili_harcama_id = secili_oge_iid
            secili_harcama_obj = harcamalar.get(secili_oge_iid)

            if not secili_harcama_obj:
                 messagebox.showerror("Hata", "Secili harcama sistemde bulunamadi.", parent=self.ana_cerceve)
                 self.kategori_guncelleme_icin_secili_harcama_id = None
                 self.secili_harcama_etiketi.config(text="Secili Gider: -")
                 self.yeni_kategori_combobox.set('')
                 self.yeni_kategori_combobox['values'] = []
                 self.yeni_kategori_combobox.config(state="disabled")
                 guncelle_butonu.config(state="disabled")
                 return


            emp_dept = secili_harcama_obj.calisan.departman
            self.secili_harcama_etiketi.config(text=f"Secili Gider: ID {secili_oge_iid}, Calisan: {secili_harcama_obj.calisan.isim}, Mevcut Kat: {secili_harcama_obj.kategori}")

            if self._departman_var_mi(emp_dept):
                dept_icin_kategoriler = list(self.muhasebe.butce_yoneticisi.butceler[emp_dept].keys())
                self.yeni_kategori_combobox['values'] = dept_icin_kategoriler
                if dept_icin_kategoriler:
                    self.yeni_kategori_combobox.config(state="readonly")
                    self.yeni_kategori_combobox.set('')
                    guncelle_butonu.config(state="normal")
                else:
                    self.yeni_kategori_combobox.set('')
                    self.yeni_kategori_combobox.config(state="disabled")
                    guncelle_butonu.config(state="disabled")
                    messagebox.showwarning("Uyari", f"{emp_dept} departmani icin tanimli kategori bulunamadi.", parent=self.ana_cerceve)
            else:
                self.yeni_kategori_combobox.set('')
                self.yeni_kategori_combobox.config(state="disabled")
                guncelle_butonu.config(state="disabled")
                messagebox.showerror("Hata", f"{emp_dept} departmani icin butce tanimi bulunamadi.", parent=self.ana_cerceve)

        self.kategori_guncelleme_harcama_agaci.bind("<<TreeviewSelect>>", harcama_secildiginde)
        form_cercevesi.columnconfigure(1, weight=1)

    def _kategori_guncelleme_harcama_agacini_doldur(self):
        if not self.kategori_guncelleme_harcama_agaci: return
        for item in self.kategori_guncelleme_harcama_agaci.get_children():
            self.kategori_guncelleme_harcama_agaci.delete(item)
        for harcama_id, harcama_obj in sorted(harcamalar.items()):
            self.kategori_guncelleme_harcama_agaci.insert("", tk.END, iid=harcama_id, values=(
                harcama_id,
                harcama_obj.calisan.isim, harcama_obj.calisan.departman, harcama_obj.kategori,
                f"{harcama_obj.tutar:.2f}", harcama_obj.tarih.strftime("%Y-%m-%d"),
                "Evet" if harcama_obj.onaylandi else "Hayir",
                "Evet" if harcama_obj.odendi else "Hayir"
            ))

    def _kategori_guncelleme_yap(self):
        if not self.kategori_guncelleme_icin_secili_harcama_id:
            messagebox.showerror("Hata", "Lutfen once bir gider secin.", parent=self.ana_cerceve)
            return

        secili_harcama_obj = harcamalar.get(self.kategori_guncelleme_icin_secili_harcama_id)

        if not secili_harcama_obj:
             messagebox.showerror("Hata", "Secili harcama sistemde bulunamadi.", parent=self.ana_cerceve)
             self.kategori_guncelleme_icin_secili_harcama_id = None
             self.secili_harcama_etiketi.config(text="Secili Gider: -")
             self.yeni_kategori_combobox.set('')
             self.yeni_kategori_combobox['values'] = []
             self.yeni_kategori_combobox.config(state="disabled")
             for widget in self.ana_cerceve.winfo_children():
                  if isinstance(widget, ttk.Frame):
                       for sub_widget in widget.winfo_children():
                            if isinstance(sub_widget, ttk.Button) and sub_widget.cget('text') == 'Kategoriyi Guncelle':
                                 sub_widget.config(state="disabled")
                                 break
                       break
             return


        yeni_cat = self.yeni_kategori_var.get()
        if not yeni_cat:
            messagebox.showerror("Hata", "Lutfen yeni bir kategori secin.", parent=self.ana_cerceve)
            return

        if secili_harcama_obj.kategori == yeni_cat:
            messagebox.showinfo("Bilgi", "Secilen yeni kategori mevcut kategori ile ayni.", parent=self.ana_cerceve)
            return

        onay = messagebox.askyesno("Kategori Guncelleme Onayi",
                                      f"Giderin (ID: {self.kategori_guncelleme_icin_secili_harcama_id}) kategorisini "
                                      f"'{secili_harcama_obj.kategori}' -> '{yeni_cat}' olarak guncellemek istediginizden emin misiniz?\n"
                                      f"Eger gider odenmisse, ilgili butceler duzeltilecektir.",
                                      parent=self.ana_cerceve)
        if not onay:
            return

        durum = self.muhasebe.harcama_kategorisi_guncelle(secili_harcama_obj, yeni_cat)

        if durum == "basarili":
            messagebox.showinfo("Basarili", "Gider kategorisi basariyla guncellendi. Butce kayitlari (gerekliyse) duzeltildi.", parent=self.ana_cerceve)
            self._kategori_guncelleme_harcama_agacini_doldur()
            self.kategori_guncelleme_icin_secili_harcama_id = None
            self.secili_harcama_etiketi.config(text="Secili Gider: -")
            self.yeni_kategori_combobox.set('')
            self.yeni_kategori_combobox.config(state="disabled")
            for widget in self.ana_cerceve.winfo_children():
                 if isinstance(widget, ttk.Frame):
                      for sub_widget in widget.winfo_children():
                           if isinstance(sub_widget, ttk.Button) and sub_widget.cget('text') == 'Kategoriyi Guncelle':
                                 sub_widget.config(state="disabled")
                                 break
                      break
            if self.kategori_guncelleme_harcama_agaci:
                 odaklanmis_oge = self.kategori_guncelleme_harcama_agaci.focus()
                 if odaklanmis_oge:
                    self.kategori_guncelleme_harcama_agaci.selection_remove(odaklanmis_oge)


        elif durum == "hata_gecersiz_yeni_kategori":
            messagebox.showerror("Hata", f"Yeni kategori '{yeni_cat}' bu giderin departmani icin gecerli degil.", parent=self.ana_cerceve)
        elif durum == "bilgi_ayni_kategori":
            messagebox.showinfo("Bilgi", "Yeni kategori mevcut kategori ile ayni.", parent=self.ana_cerceve)
        else:
            messagebox.showerror("Hata", f"Kategori guncellenirken bir sorun olustu: {durum}", parent=self.ana_cerceve)


    def _listeleri_goster_arayuzu(self):
        self._ana_ekrani_temizle()
        ttk.Label(self.ana_cerceve, text="Sistem Kayitlari", style="Header.TLabel").pack(pady=20)
        defter = ttk.Notebook(self.ana_cerceve)

        calisan_sekmesi = ttk.Frame(defter, style="Content.TFrame")
        defter.add(calisan_sekmesi, text='Calisanlar')
        sutunlar_calisan = ("ID", "Isim", "Departman")
        agac_calisan = ttk.Treeview(calisan_sekmesi, columns=sutunlar_calisan, show='headings')
        for sutun in sutunlar_calisan: agac_calisan.heading(sutun, text=sutun)
        agac_calisan.column("ID", width=150)
        for calisan_id, calisan_obj in sorted(calisanlar.items()):
             agac_calisan.insert("", tk.END, values=(calisan_id, calisan_obj.isim, calisan_obj.departman))
        agac_calisan.pack(expand=True, fill='both', padx=10, pady=10)

        yonetici_sekmesi = ttk.Frame(defter, style="Content.TFrame")
        defter.add(yonetici_sekmesi, text='Yoneticiler')
        sutunlar_yonetici = ("ID", "Isim", "Departman")
        agac_yonetici = ttk.Treeview(yonetici_sekmesi, columns=sutunlar_yonetici, show='headings')
        for sutun in sutunlar_yonetici: agac_yonetici.heading(sutun, text=sutun)
        agac_yonetici.column("ID", width=150)
        for yonetici_id, yonetici_obj in sorted(yoneticiler.items()):
             agac_yonetici.insert("", tk.END, values=(yonetici_id, yonetici_obj.isim, yonetici_obj.departman))
        agac_yonetici.pack(expand=True, fill='both', padx=10, pady=10)

        harcama_sekmesi = ttk.Frame(defter, style="Content.TFrame")
        defter.add(harcama_sekmesi, text='Tum Giderler')
        sutunlar_harcama = ("ID","Calisan", "Talep Edilen", "Kategori", "Departman", "Tarih", "Belge Ref.", "Onay", "Odeme", "Odenen", "Durum")
        agac_harcama = ttk.Treeview(harcama_sekmesi, columns=sutunlar_harcama, show='headings')
        for sutun_idx, sutun in enumerate(sutunlar_harcama):
            agac_harcama.heading(sutun, text=sutun)
            genislik = 100 if sutun_idx > 0 else 150
            agac_harcama.column(sutun, width=genislik, minwidth=60 if sutun_idx > 0 else 120)
        agac_harcama.column("Durum", width=120)
        agac_harcama.column("Kategori", width=120)
        agac_harcama.column("Departman", width=120)


        for harcama_id, harcama_obj in sorted(harcamalar.items()):
            agac_harcama.insert("", tk.END, values=(
                harcama_id,
                harcama_obj.calisan.isim, f"{harcama_obj.tutar:.2f} TL", harcama_obj.kategori, harcama_obj.calisan.departman,
                harcama_obj.tarih.strftime("%Y-%m-%d"),
                harcama_obj.belge_referansi,
                "Evet" if harcama_obj.onaylandi else "Hayir",
                "Evet" if harcama_obj.odendi else "Hayir",
                f"{harcama_obj.odenen_tutar:.2f} TL" if harcama_obj.odendi else "-",
                harcama_obj.odeme_sonrasi_durum
            ))
        agac_harcama.pack(expand=True, fill='both', padx=10, pady=10)
        defter.pack(expand=True, fill='both', padx=10, pady=10)

    def _rapor_arayuzu(self):
        self._ana_ekrani_temizle()
        ttk.Label(self.ana_cerceve, text="Raporlar ve Analizler", style="Header.TLabel").pack(pady=20)
        self.rapor_defteri_yenileme_icin = ttk.Notebook(self.ana_cerceve)

        tarih_filtre_cercevesi = ttk.Frame(self.ana_cerceve, style="Content.TFrame")
        tarih_filtre_cercevesi.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(tarih_filtre_cercevesi, text="Tarih filtreleme ozelligi henuz aktif degildir. Tum veriler gosterilmektedir.", background="white", foreground="gray").pack(padx=10, pady=5)


        calisan_rapor_sekmesi = ttk.Frame(self.rapor_defteri_yenileme_icin, style="Content.TFrame")
        self.rapor_defteri_yenileme_icin.add(calisan_rapor_sekmesi, text='Calisana Gore Giderler')
        self._gider_rapor_agaci_olustur(calisan_rapor_sekmesi, group_by_key=lambda exp: exp.calisan.isim, baslik_oneki="Calisan", harcama_listesi=list(harcamalar.values()))

        dept_rapor_sekmesi = ttk.Frame(self.rapor_defteri_yenileme_icin, style="Content.TFrame")
        self.rapor_defteri_yenileme_icin.add(dept_rapor_sekmesi, text='Departmana Gore Giderler')
        self._gider_rapor_agaci_olustur(dept_rapor_sekmesi, group_by_key=lambda exp: exp.calisan.departman, baslik_oneki="Departman", harcama_listesi=list(harcamalar.values()))

        cat_rapor_sekmesi = ttk.Frame(self.rapor_defteri_yenileme_icin, style="Content.TFrame")
        self.rapor_defteri_yenileme_icin.add(cat_rapor_sekmesi, text='Kategoriye Gore Giderler')
        self._gider_rapor_agaci_olustur(cat_rapor_sekmesi, group_by_key=lambda exp: exp.kategori, baslik_oneki="Kategori", harcama_listesi=list(harcamalar.values()))

        butce_sekmesi = ttk.Frame(self.rapor_defteri_yenileme_icin, style="Content.TFrame")
        self.rapor_defteri_yenileme_icin.add(butce_sekmesi, text='Kalan Butceler')
        self._kalan_butceleri_goster(butce_sekmesi)

        tahmin_sekmesi = ttk.Frame(self.rapor_defteri_yenileme_icin, style="Content.TFrame")
        self.rapor_defteri_yenileme_icin.add(tahmin_sekmesi, text='Butce Tahmini (Hareketli Ort.)')
        self._butce_tahmini_goster(tahmin_sekmesi)

        grafik_sekmesi = ttk.Frame(self.rapor_defteri_yenileme_icin, style="Content.TFrame")
        self.rapor_defteri_yenileme_icin.add(grafik_sekmesi, text='Grafik Raporlar')
        self._grafik_rapor_goster(grafik_sekmesi)


        self.rapor_defteri_yenileme_icin.pack(expand=True, fill='both', padx=10, pady=10)
        self.rapor_defteri_yenileme_icin.bind("<<NotebookTabChanged>>", self._aktif_rapor_sekmesini_yenile)


    def _aktif_rapor_sekmesini_yenile(self, event=None):
        if not hasattr(self, 'rapor_defteri_yenileme_icin') or not self.rapor_defteri_yenileme_icin:
            return

        try:
            secili_sekme_widget = self.rapor_defteri_yenileme_icin.nametowidget(self.rapor_defteri_yenileme_icin.select())
            secili_sekme_metni = self.rapor_defteri_yenileme_icin.tab(self.rapor_defteri_yenileme_icin.select(), "text")
        except tk.TclError:
            return

        tum_harcamalar_listesi = list(harcamalar.values())

        if secili_sekme_metni == 'Calisana Gore Giderler':
            self._gider_rapor_agaci_olustur(secili_sekme_widget, group_by_key=lambda exp: exp.calisan.isim, baslik_oneki="Calisan", harcama_listesi=tum_harcamalar_listesi)
        elif secili_sekme_metni == 'Departmana Gore Giderler':
            self._gider_rapor_agaci_olustur(secili_sekme_widget, group_by_key=lambda exp: exp.calisan.departman, baslik_oneki="Departman", harcama_listesi=tum_harcamalar_listesi)
        elif secili_sekme_metni == 'Kategoriye Gore Giderler':
            self._gider_rapor_agaci_olustur(secili_sekme_widget, group_by_key=lambda exp: exp.kategori, baslik_oneki="Kategori", harcama_listesi=tum_harcamalar_listesi)
        elif secili_sekme_metni == 'Kalan Butceler':
            self._kalan_butceleri_goster(secili_sekme_widget)
        elif secili_sekme_metni == 'Butce Tahmini (Hareketli Ort.)':
             self._butce_tahmini_goster(secili_sekme_widget)
        elif secili_sekme_metni == 'Grafik Raporlar':
            self._grafik_rapor_goster(secili_sekme_widget)


    def _tarih_filtresi_uygula_ve_raporlari_yenile(self):
        messagebox.showinfo("Filtre", "Tarih filtreleme ozelligi henuz aktif degildir. Tum veriler gosterilmektedir.", parent=self.ana_cerceve)
        self._aktif_rapor_sekmesini_yenile()


    def _gider_rapor_agaci_olustur(self, parent_tab, group_by_key, baslik_oneki, harcama_listesi):
        for widget in parent_tab.winfo_children():
            widget.destroy()

        sutunlar = (baslik_oneki, "Toplam Odenen Gider (TL)", "Gider Sayisi")
        agac = ttk.Treeview(parent_tab, columns=sutunlar, show='headings')
        for sutun in sutunlar:
            agac.heading(sutun, text=sutun)
            agac.column(sutun, width=180, anchor="center")

        gruplanmis_harcamalar = collections.defaultdict(lambda: {"total": 0.0, "count": 0})
        for harcama_obj in harcama_listesi:
            if harcama_obj.odendi :
                anahtar = group_by_key(harcama_obj)
                gruplanmis_harcamalar[anahtar]["total"] += harcama_obj.odenen_tutar
                gruplanmis_harcamalar[anahtar]["count"] += 1

        for anahtar, veri in sorted(gruplanmis_harcamalar.items()):
            agac.insert("", tk.END, values=(anahtar, f"{veri['total']:.2f}", veri["count"]))

        agac.pack(expand=True, fill='both', padx=10, pady=10)

    def _kalan_butceleri_goster(self, parent_tab):
        for widget in parent_tab.winfo_children():
            widget.destroy()

        sutunlar = ("Departman", "Kategori", "Baslangic Butcesi (TL)", "Kalan Butce (TL)")
        agac = ttk.Treeview(parent_tab, columns=sutunlar, show='headings')
        for sutun in sutunlar:
            agac.heading(sutun, text=sutun)
            agac.column(sutun, width=180, anchor="w")

        kalan_butceler_veri = self.muhasebe.butce_yoneticisi.kalan_butceyi_getir()
        baslangic_butceler = self.muhasebe.butce_yoneticisi.baslangic_butceyi_getir()

        for dept, cats in baslangic_butceler.items():
            for cat, baslangic_butce_val in cats.items():
                kalan_val = kalan_butceler_veri.get(dept, {}).get(cat, baslangic_butce_val)
                agac.insert("", tk.END, values=(
                    dept, cat, f"{baslangic_butce_val:.2f}", f"{kalan_val:.2f}"
                ))
        agac.pack(expand=True, fill='both', padx=10, pady=10)


    def _butce_tahmini_goster(self, parent_tab):
        for widget in parent_tab.winfo_children():
            widget.destroy()

        tahmin_cercevesi = ttk.Frame(parent_tab, style="Content.TFrame")
        tahmin_cercevesi.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(tahmin_cercevesi, text="Departman:", style="TLabel", background="white").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        dept_var = tk.StringVar()
        dept_combo = ttk.Combobox(tahmin_cercevesi, textvariable=dept_var, values=list(self.muhasebe.butce_yoneticisi.butceler.keys()), state="readonly", width=20)
        dept_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(tahmin_cercevesi, text="Kategori:", style="TLabel", background="white").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        cat_var = tk.StringVar()
        cat_combo = ttk.Combobox(tahmin_cercevesi, textvariable=cat_var, state="readonly", width=20)
        cat_combo.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        def tahmin_kategorilerini_guncelle(*args):
            secili_dept = dept_var.get()
            if secili_dept and self._departman_var_mi(secili_dept):
                cat_combo['values'] = list(self.muhasebe.butce_yoneticisi.butceler[secili_dept].keys())
                if cat_combo['values']: cat_combo.current(0); cat_var.set(cat_combo.get())
                else: cat_var.set('')
            else:
                cat_combo['values'] = []
                cat_var.set('')
        dept_var.trace_add("write", tahmin_kategorilerini_guncelle)
        if dept_combo['values']:
             dept_combo.current(0)


        ttk.Label(tahmin_cercevesi, text="Pencere Boyutu (Aylik Donem):", style="TLabel", background="white").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        pencere_var = tk.IntVar(value=3)
        pencere_spinbox = ttk.Spinbox(tahmin_cercevesi, from_=1, to=12, textvariable=pencere_var, width=5, state="readonly")
        pencere_spinbox.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        sonuc_etiketi = ttk.Label(parent_tab, text="Tahmin Sonucu: -", font=('Segoe UI Variable Text', 11, 'italic'), style="TLabel", background="white")
        sonuc_etiketi.pack(pady=10, fill=tk.X, padx=10)

        def tahmin_hesapla():
            secili_dept = dept_var.get()
            secili_cat = cat_var.get()
            pencere_boyutu_val = pencere_var.get()

            if not secili_dept or not secili_cat:
                messagebox.showerror("Hata", "Lutfen departman ve kategori secin.", parent=parent_tab)
                return
            if pencere_boyutu_val <= 0:
                messagebox.showerror("Hata", "Pencere boyutu pozitif bir deger olmalidir.", parent=parent_tab)
                return

            aylik_harcamalar_veri = collections.defaultdict(float)
            for harcama_obj in harcamalar.values():
                if harcama_obj.odendi and harcama_obj.calisan.departman == secili_dept and harcama_obj.kategori == secili_cat:
                    ay_yil = harcama_obj.tarih.strftime("%Y-%m")
                    aylik_harcamalar_veri[ay_yil] += harcama_obj.odenen_tutar

            if not aylik_harcamalar_veri:
                sonuc_etiketi.config(text=f"Tahmin Sonucu: {secili_dept} - {secili_cat} icin yeterli gecmiş (odenmiş) veri yok.")
                return

            sirali_aylik_tutarlar = [tutar for _, tutar in sorted(aylik_harcamalar_veri.items())]


            if len(sirali_aylik_tutarlar) < pencere_boyutu_val:
                sonuc_etiketi.config(text=f"Tahmin Sonucu: Yeterli veri yok (en az {pencere_boyutu_val} farkli ayin odenmis gideri gerekli).")
                return

            tahmin_deger = hareketli_ortalama_hesapla.hareketli_ortalama(sirali_aylik_tutarlar, pencere_boyutu_val)

            if tahmin_deger is not None:
                sonraki_donem_tahmini = tahmin_deger
                sonuc_etiketi.config(text=f"Tahmin Sonucu ({secili_dept} - {secili_cat}, {pencere_boyutu_val} Donem HO):\nGelecek Donem Butce Onerisi (Aylik): {sonraki_donem_tahmini:.2f} TL")
            else:
                sonuc_etiketi.config(text="Tahmin Sonucu: Hesaplama yapilamadi (veri yetersiz veya pencere boyutu uygun degil).")


        ttk.Button(tahmin_cercevesi, text="Tahmin Et", command=tahmin_hesapla).grid(row=3, column=0, columnspan=2, pady=10)
        tahmin_cercevesi.columnconfigure(1, weight=1)

    def _grafik_rapor_goster(self, parent_tab):
        for widget in parent_tab.winfo_children():
            widget.destroy()

        odenmis_harcamalar_listesi = [h for h in harcamalar.values() if h.odendi]

        if not odenmis_harcamalar_listesi:
            messagebox.showinfo("Bilgi", "Grafik olusturmak icin yeterli odenmis gider verisi bulunmamaktadir.", parent=parent_tab)
            ttk.Label(parent_tab, text="Grafik olusturmak icin odenmis gider verisi bulunmamaktadir.", style="TLabel", background="white").pack(padx=10, pady=10)
            return

        kategoriye_gore_harcamalar = collections.defaultdict(float)
        for harcama_obj in odenmis_harcamalar_listesi:
            kategoriye_gore_harcamalar[harcama_obj.kategori] += harcama_obj.odenen_tutar

        if not kategoriye_gore_harcamalar:
             ttk.Label(parent_tab, text="Grafik icin veri yok (hic odenmis gider bulunamadi).", style="TLabel", background="white").pack(padx=10, pady=10)
             return


        kategoriler_list = list(kategoriye_gore_harcamalar.keys())
        tutarlar_list = list(kategoriye_gore_harcamalar.values())

        fig = Figure(figsize=(8, 5), dpi=100)
        cizim_alani = fig.add_subplot(111)

        cubuklar = cizim_alani.bar(kategoriler_list, tutarlar_list, color='skyblue')
        cizim_alani.set_xlabel("Kategori", fontsize=10)
        cizim_alani.set_ylabel("Toplam Odenen Tutar (TL)", fontsize=10)
        cizim_alani.set_title("Kategori Bazli Toplam Odenen Giderler", fontsize=12)
        fig.autofmt_xdate(rotation=45, ha='right')
        cizim_alani.tick_params(axis='x', labelsize=8)
        cizim_alani.tick_params(axis='y', labelsize=8)
        cizim_alani.grid(axis='y', linestyle='--', alpha=0.7)

        for cubuk in cubuklar:
            y_degeri = cubuk.get_height()
            cizim_alani.text(cubuk.get_x() + cubuk.get_width()/2.0, y_degeri + (max(tutarlar_list)*0.01), f'{y_degeri:.2f}', ha='center', va='bottom', fontsize=8)


        fig.tight_layout()

        tuval = FigureCanvasTkAgg(fig, master=parent_tab)
        tuval_widget = tuval.get_tk_widget()
        tuval_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        tuval.draw()


    def _butce_donemini_sifirla_arayuzu(self):
        if messagebox.askyesno("Butce Donemini Sifirla",
                               "Bu islem, butce asim uyarilarini sifirlayacak ve yeni bir donem baslatacaktir. Devam etmek istiyor musunuz?",
                               parent=self):
            self.muhasebe.butce_yoneticisi.butce_donem_bayraklarini_sifirla()
            messagebox.showinfo("Basarili", "Butce donemi sifirlandi.", parent=self.ana_cerceve)
            if hasattr(self, 'rapor_defteri_yenileme_icin') and self.rapor_defteri_yenileme_icin:
                 try:
                    guncel_sekme_metni = self.rapor_defteri_yenileme_icin.tab(self.rapor_defteri_yenileme_icin.select(), "text")
                    if guncel_sekme_metni == 'Kalan Butceler':
                        self._aktif_rapor_sekmesini_yenile()
                 except tk.TclError:
                    pass


if __name__ == "__main__":
    butce_yoneticisi_instance = None
    muhasebe_sistemi_instance = None

    try:
        butce_yoneticisi_instance = butce_baslat()

        if butce_yoneticisi_instance:
            muhasebe_sistemi_instance = Muhasebe(butce_yoneticisi_instance)
            print("[BILGI] Butce yoneticisi ve muhasebe sistemi basariyla baslatildi.")

            verileri_yukle()
            print(f"[BILGI] Veriler ({VERI_DOSYASI} dosyasindan) yuklendi.")

        else:
            print("[HATA] ButceYoneticisi ornegi olusturulamadi. Program sonlandiriliyor.")
            exit()
    except NameError:
         print("[HATA] 'Muhasebe' sinifi tanimli degil. models/accounting2.py dosyasini kontrol edin.")
         traceback.print_exc()
         exit()
    except Exception as e:
        print(f"[HATA] Uygulama baslatilirken beklenmedik bir sorun olustu: {e}")
        traceback.print_exc()
        exit()

    if butce_yoneticisi_instance and muhasebe_sistemi_instance:
        app = HarcamaUygulamasi(muhasebe_sistemi_instance)
        app.mainloop()
    else:
        print("[HATA] Gerekli sistem bilesenleri baslatilamadigi icin uygulama calistirilamiyor.")
