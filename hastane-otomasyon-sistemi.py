
# -*- coding: utf-8 -*-

from tkcalendar import DateEntry
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import smtplib
from email.mime.text import MIMEText

def veritabani_baglan():
    conn = sqlite3.connect("hastane.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kullanicilar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kullanici_adi TEXT NOT NULL UNIQUE,
        sifre TEXT NOT NULL,
        rol TEXT NOT NULL
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS randevular (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tc TEXT,
        ad TEXT NOT NULL,
        soyad TEXT NOT NULL,
        email TEXT NOT NULL,
        bolum TEXT NOT NULL,
        doktor TEXT NOT NULL,
        tarih TEXT NOT NULL,
        saat TEXT NOT NULL
    )
    """)
    cursor.execute("INSERT OR IGNORE INTO kullanicilar VALUES (1, 'admin', '1234', 'admin')")
    cursor.execute("INSERT OR IGNORE INTO kullanicilar VALUES (2, 'sekreter', '1234', 'sekreter')")
    cursor.execute("INSERT OR IGNORE INTO kullanicilar VALUES (3, 'draydin', '1234', 'doktor')")
    conn.commit()
    conn.close()

def eposta_gonder(email, ad, doktor, tarih, saat):
    try:
        gonderen = "sizinmail@gmail.com"
        sifre = "uygulama_sifreniz"
        konu = "Randevu Onayı"
        mesaj_metni = f"Sayın {ad},\n\nRandevunuz başarıyla oluşturulmuştur.\n\nDoktor: {doktor}\nTarih: {tarih} Saat: {saat}\n\nSağlıklı günler dileriz."
        mesaj = MIMEText(mesaj_metni)
        mesaj['Subject'] = konu
        mesaj['From'] = gonderen
        mesaj['To'] = email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gonderen, sifre)
            server.send_message(mesaj)
    except Exception as e:
        print("E-posta gönderilemedi:", e)

def kullanici_dogrula(kadi, sifre):
    conn = sqlite3.connect("hastane.db")
    cursor = conn.cursor()
    cursor.execute("SELECT kullanici_adi, rol FROM kullanicilar WHERE kullanici_adi=? AND sifre=?", (kadi, sifre))
    sonuc = cursor.fetchone()
    conn.close()
    return sonuc

def randevu_ekle(tc, ad, soyad, email, bolum, doktor, tarih, saat):
    conn = sqlite3.connect("hastane.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM randevular WHERE doktor=? AND tarih=? AND saat=?", (doktor, tarih, saat))
    if cursor.fetchone():
        conn.close()
        return False
    cursor.execute("INSERT INTO randevular (tc, ad, soyad, email, bolum, doktor, tarih, saat) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                   (tc, ad, soyad, email, bolum, doktor, tarih, saat))
    conn.commit()
    conn.close()
    eposta_gonder(email, ad, doktor, tarih, saat)
    return True

def randevulari_getir(rol, kullanici_adi):
    conn = sqlite3.connect("hastane.db")
    cursor = conn.cursor()
    if rol == "doktor":
        cursor.execute("SELECT id, ad, soyad, email, bolum, doktor, tarih, saat FROM randevular WHERE doktor=?", (kullanici_adi,))
    else:
        cursor.execute("SELECT id, ad, soyad, email, bolum, doktor, tarih, saat FROM randevular")
    veriler = cursor.fetchall()
    conn.close()
    return veriler

def giris_ekrani():
    def giris():
        kadi = entry_kadi.get()
        sifre = entry_sifre.get()
        sonuc = kullanici_dogrula(kadi, sifre)
        if sonuc:
            giris_pencere.destroy()
            uygulama_ekrani(sonuc[0], sonuc[1])
        else:
            messagebox.showerror("Hata", "Kullanıcı adı veya şifre hatalı!")

    giris_pencere = tk.Tk()
    giris_pencere.title("Giriş")
    tk.Label(giris_pencere, text="Kullanıcı Adı").grid(row=0, column=0)
    entry_kadi = tk.Entry(giris_pencere)
    entry_kadi.grid(row=0, column=1)
    tk.Label(giris_pencere, text="Şifre").grid(row=1, column=0)
    entry_sifre = tk.Entry(giris_pencere, show="*")
    entry_sifre.grid(row=1, column=1)
    tk.Button(giris_pencere, text="Giriş Yap", command=giris).grid(row=2, column=0, columnspan=2)
    giris_pencere.mainloop()

def uygulama_ekrani(kullanici_adi, rol):
    def filtrele(*args):
        sorgu = entry_ara.get().lower()
        for item in tree.get_children():
            tree.delete(item)
        for r in randevulari_getir(rol, kullanici_adi):
            if any(sorgu in str(deger).lower() for deger in r):
                tree.insert("", "end", values=r)

    def kaydet():
        tc = entry_tc.get()
        ad = entry_ad.get()
        soyad = entry_soyad.get()
        email = entry_email.get()
        bolum = combo_bolum.get()
        doktor = combo_doktor.get()
        tarih = entry_tarih.get()
        saat = combo_saat.get()
        if tc and ad and soyad and email and bolum and doktor and tarih and saat:
            if randevu_ekle(tc, ad, soyad, email, bolum, doktor, tarih, saat):
                messagebox.showinfo("Başarılı", "Randevu kaydedildi ve e-posta gönderildi.")
                guncelle_liste()
            else:
                messagebox.showerror("Çakışma", "Bu tarih ve saatte randevu mevcut.")
        else:
            messagebox.showwarning("Eksik", "Tüm alanları doldurunuz.")

    def randevu_sil():
        secilen = tree.selection()
        if not secilen:
            messagebox.showwarning("Seçim Yok", "Silmek için bir randevu seçin.")
            return
        randevu_id = tree.item(secilen[0])["values"][0]
        conn = sqlite3.connect("hastane.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM randevular WHERE id=?", (randevu_id,))
        conn.commit()
        conn.close()
        guncelle_liste()

    def randevu_guncelle():
        secilen = tree.selection()
        if not secilen:
            messagebox.showwarning("Seçim Yok", "Güncellemek için bir randevu seçin.")
            return
        randevu_id = tree.item(secilen[0])["values"][0]
        conn = sqlite3.connect("hastane.db")
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE randevular SET ad=?, soyad=?, email=?, bolum=?, doktor=?, tarih=?, saat=? WHERE id=?
        """, (
            entry_ad.get(), entry_soyad.get(), entry_email.get(), combo_bolum.get(),
            combo_doktor.get(), entry_tarih.get(), combo_saat.get(), randevu_id
        ))
        conn.commit()
        conn.close()
        guncelle_liste()

    def kullanici_paneli():
        panel = tk.Toplevel(pencere)
        panel.title("Kullanıcı Paneli")

        def kullanici_ekle():
            yeni_kadi = entry_yeni_kadi.get()
            yeni_sifre = entry_yeni_sifre.get()
            yeni_rol = combo_rol.get()
            if yeni_kadi and yeni_sifre and yeni_rol:
                try:
                    conn = sqlite3.connect("hastane.db")
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO kullanicilar (kullanici_adi, sifre, rol) VALUES (?, ?, ?)",
                                   (yeni_kadi, yeni_sifre, yeni_rol))
                    conn.commit()
                    conn.close()
                    messagebox.showinfo("Başarılı", "Yeni kullanıcı eklendi.")
                except sqlite3.IntegrityError:
                    messagebox.showerror("Hata", "Bu kullanıcı adı zaten var!")
            else:
                messagebox.showwarning("Eksik Bilgi", "Tüm alanları doldurun.")

        def sifre_degistir():
            mevcut_kadi = entry_mevcut_kadi.get()
            yeni_sifre = entry_yeni_sifre_degistir.get()
            if mevcut_kadi and yeni_sifre:
                conn = sqlite3.connect("hastane.db")
                cursor = conn.cursor()
                cursor.execute("UPDATE kullanicilar SET sifre=? WHERE kullanici_adi=?", (yeni_sifre, mevcut_kadi))
                if cursor.rowcount == 0:
                    messagebox.showerror("Hata", "Kullanıcı bulunamadı!")
                else:
                    conn.commit()
                    messagebox.showinfo("Başarılı", "Şifre değiştirildi.")
                conn.close()
            else:
                messagebox.showwarning("Eksik Bilgi", "Tüm alanları doldurun.")

        tk.Label(panel, text="Yeni Kullanıcı Adı").grid(row=0, column=0)
        entry_yeni_kadi = tk.Entry(panel)
        entry_yeni_kadi.grid(row=0, column=1)

        tk.Label(panel, text="Yeni Şifre").grid(row=1, column=0)
        entry_yeni_sifre = tk.Entry(panel)
        entry_yeni_sifre.grid(row=1, column=1)

        tk.Label(panel, text="Rol").grid(row=2, column=0)
        combo_rol = ttk.Combobox(panel, values=["admin", "doktor", "sekreter"])
        combo_rol.grid(row=2, column=1)

        tk.Button(panel, text="Kullanıcı Ekle", command=kullanici_ekle).grid(row=3, column=0, columnspan=2)

        tk.Label(panel, text="Mevcut Kullanıcı Adı").grid(row=4, column=0)
        entry_mevcut_kadi = tk.Entry(panel)
        entry_mevcut_kadi.grid(row=4, column=1)

        tk.Label(panel, text="Yeni Şifre").grid(row=5, column=0)
        entry_yeni_sifre_degistir = tk.Entry(panel)
        entry_yeni_sifre_degistir.grid(row=5, column=1)

        tk.Button(panel, text="Şifre Değiştir", command=sifre_degistir).grid(row=6, column=0, columnspan=2)

    def tema_degistir():
        tema = pencere.cget('bg')
        if tema == "SystemButtonFace":
            pencere.configure(bg="black")
            for child in pencere.winfo_children():
                try:
                    child.configure(bg="black", fg="white")
                except:
                    pass
        else:
            pencere.configure(bg="SystemButtonFace")
            for child in pencere.winfo_children():
                try:
                    child.configure(bg="SystemButtonFace", fg="black")
                except:
                    pass

    def guncelle_liste():
        for i in tree.get_children():
            tree.delete(i)
        for r in randevulari_getir(rol, kullanici_adi):
            tree.insert("", "end", values=r)

    pencere = tk.Tk()
    pencere.title("Randevu Paneli")

    tk.Label(pencere, text="TC").grid(row=0, column=0)
    entry_tc = tk.Entry(pencere)
    entry_tc.grid(row=0, column=1)

    tk.Label(pencere, text="Ad").grid(row=1, column=0)
    entry_ad = tk.Entry(pencere)
    entry_ad.grid(row=1, column=1)

    tk.Label(pencere, text="Soyad").grid(row=2, column=0)
    entry_soyad = tk.Entry(pencere)
    entry_soyad.grid(row=2, column=1)

    tk.Label(pencere, text="E-posta").grid(row=3, column=0)
    entry_email = tk.Entry(pencere)
    entry_email.grid(row=3, column=1)

    tk.Label(pencere, text="Bölüm").grid(row=4, column=0)
    combo_bolum = ttk.Combobox(pencere, values=["Dahiliye", "Kardiyoloji", "Göz", "Ortopedi"])
    combo_bolum.grid(row=4, column=1)

    tk.Label(pencere, text="Doktor").grid(row=5, column=0)
    combo_doktor = ttk.Combobox(pencere, values=["draydin", "Dr. Bilge", "Dr. Can", "Dr. Deniz"])
    combo_doktor.grid(row=5, column=1)

    tk.Label(pencere, text="Tarih").grid(row=6, column=0)
    entry_tarih = DateEntry(pencere, date_pattern="yyyy-mm-dd")
    entry_tarih.grid(row=6, column=1)

    tk.Label(pencere, text="Saat").grid(row=7, column=0)
    combo_saat = ttk.Combobox(pencere, values=["09:00", "10:00", "11:00", "13:00", "14:00", "15:00"])
    combo_saat.grid(row=7, column=1)

    tk.Button(pencere, text="Randevu Kaydet", command=kaydet).grid(row=8, column=0, columnspan=2)
    tk.Button(pencere, text="Randevu Sil", command=randevu_sil).grid(row=9, column=0)
    tk.Button(pencere, text="Randevu Güncelle", command=randevu_guncelle).grid(row=9, column=1)
    tk.Button(pencere, text="Kullanıcı Paneli", command=kullanici_paneli).grid(row=10, column=0)
    tk.Button(pencere, text="Tema Değiştir", command=tema_degistir).grid(row=10, column=1)

    tree = ttk.Treeview(pencere, columns=("ID", "Ad", "Soyad", "E-posta", "Bölüm", "Doktor", "Tarih", "Saat"), show="headings")
    for col in tree["columns"]:
        tree.heading(col, text=col)
    tree.grid(row=11, column=0, columnspan=2)

    tk.Label(pencere, text="Ara:").grid(row=12, column=0)
    entry_ara = tk.Entry(pencere)
    entry_ara.grid(row=12, column=1)
    entry_ara.bind("<KeyRelease>", filtrele)

    guncelle_liste()
    pencere.mainloop()

veritabani_baglan()
giris_ekrani()
