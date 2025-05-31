import sqlite3
from tkinter import *
from tkinter import messagebox
from tkcalendar import DateEntry  # Takvim kütüphanesini ekleyin


# Veritabanı bağlantısı ve tabloların oluşturulması
def initialize_db():
    conn = sqlite3.connect("hospital_system_gui.db")
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        surname TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT CHECK(role IN ('Hasta', 'Doktor', 'Yonetici')) NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        doctor TEXT NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        status TEXT DEFAULT 'Aktif',
        FOREIGN KEY(patient_id) REFERENCES Users(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        department_id INTEGER,
        working_hours TEXT,
        email TEXT UNIQUE NOT NULL,
        FOREIGN KEY(department_id) REFERENCES Departments(id)
    )
    ''')

    conn.commit()
    return conn, cursor


# Gölgelendirme ve kenar yuvarlama için özel buton fonksiyonu
def rounded_button(parent, text, command):
    button = Button(parent, text=text, command=command, relief=RAISED,
                    bg="#4CAF50", fg="white", font=("Arial", 12),
                    bd=0, highlightthickness=0)
    button.pack(pady=10, padx=5)

    # Gölgelendirme efekti
    button.bind("<Enter>", lambda e: button.config(bg="#45a049"))
    button.bind("<Leave>", lambda e: button.config(bg="#4CAF50"))

    return button


# Kullanıcı kaydı
def register_user(cursor, conn, entry_name, entry_surname, entry_email, entry_password, entry_password_confirm):
    name = entry_name.get()
    surname = entry_surname.get()
    email = entry_email.get()
    password = entry_password.get()
    password_confirm = entry_password_confirm.get()

    if not all([name, surname, email, password, password_confirm]):
        messagebox.showerror("Hata", "Tüm alanları doldurun!")
        return

    if password != password_confirm:
        messagebox.showerror("Hata", "Şifreler eşleşmiyor!")
        return

    try:
        cursor.execute("INSERT INTO Users (name, surname, email, password, role) VALUES (?, ?, ?, ?, 'Hasta')",
                       (name, surname, email, password))
        conn.commit()
        messagebox.showinfo("Başarılı", f"Kayıt başarılı! Hoş geldiniz, {name}")
        entry_name.master.destroy()
    except sqlite3.IntegrityError:
        messagebox.showerror("Hata", "E-posta zaten kayıtlı!")


# Giriş yapma
def login_user(cursor, entry_login_email, entry_login_password):
    email = entry_login_email.get()
    password = entry_login_password.get()

    cursor.execute("SELECT * FROM Users WHERE email = ? AND password = ?", (email, password))
    user = cursor.fetchone()

    if user:
        messagebox.showinfo("Başarılı", f"Hoş geldiniz, {user[1]}!")
        entry_login_email.master.destroy()
        if user[5] == "Hasta":
            patient_dashboard(user)
        elif user[5] == "Doktor":
            doctor_dashboard(user)
        elif user[5] == "Yonetici":
            admin_dashboard(user)
    else:
        messagebox.showerror("Hata", "Geçersiz giriş bilgileri!")


# Hasta Dashboard
def patient_dashboard(user):
    patient_window = Toplevel()
    patient_window.title("Hasta Paneli")
    patient_window.configure(bg="white")

    Label(patient_window, text="Hasta Paneli", font=("Arial", 16), bg="white").pack(pady=10)

    rounded_button(patient_window, "Randevu Al", lambda: book_appointment(user))
    rounded_button(patient_window, "Randevularımı Gör", lambda: view_appointments(user))


# Randevu alma
def book_appointment(user):
    appointment_window = Toplevel()
    appointment_window.title("Randevu Al")
    appointment_window.configure(bg="white")

    Label(appointment_window, text="Doktor Seçimi", font=("Arial", 14), bg="white").pack(pady=10)

    # Doktorları listele
    doctors = []
    cursor.execute("SELECT name FROM Doctors")
    for row in cursor.fetchall():
        doctors.append(row[0])

    selected_doctor = StringVar(value=doctors[0])
    OptionMenu(appointment_window, selected_doctor, *doctors).pack(pady=10)

    Label(appointment_window, text="Tarih:", bg="white").pack()
    entry_date = DateEntry(appointment_window, date_pattern='yyyy-mm-dd')
    entry_date.pack(pady=5)

    Label(appointment_window, text="Saat (HH:MM):", bg="white").pack()
    entry_time = Entry(appointment_window)
    entry_time.pack(pady=5)

    rounded_button(appointment_window, "Randevu Al",
                   lambda: confirm_appointment(user, selected_doctor.get(), entry_date.get_date(), entry_time.get()))


# Randevu onayı
def confirm_appointment(user, doctor, date, time):
    cursor.execute("INSERT INTO Appointments (patient_id, doctor, date, time) VALUES (?, ?, ?, ?)",
                   (user[0], doctor, date, time))
    conn.commit()
    messagebox.showinfo("Başarılı", "Randevunuz başarıyla alındı!")


# Randevuların görüntülenmesi
def view_appointments(user):
    cursor.execute("SELECT doctor, date, time, status FROM Appointments WHERE patient_id = ?", (user[0],))
    appointments = cursor.fetchall()

    if not appointments:
        messagebox.showinfo("Bilgi", "Hiç randevunuz yok.")
    else:
        result = "\n".join([f"{appt[0]} - {appt[1]} {appt[2]} ({appt[3]})" for appt in appointments])
        messagebox.showinfo("Randevularınız", result)


# Doktor Dashboard
def doctor_dashboard(user):
    doctor_window = Toplevel()
    doctor_window.title("Doktor Paneli")
    doctor_window.configure(bg="white")

    Label(doctor_window, text="Doktor Paneli", font=("Arial", 16), bg="white").pack(pady=10)

    rounded_button(doctor_window, "Randevularım", lambda: view_doctor_appointments(user))
    rounded_button(doctor_window, "Profilim", lambda: edit_doctor_profile(user))


# Doktor randevuları
def view_doctor_appointments(user):
    cursor.execute("SELECT Users.name, date, time, status FROM Appointments "
                   "JOIN Users ON Appointments.patient_id = Users.id "
                   "WHERE doctor = ?", (user[1],))
    appointments = cursor.fetchall()

    if not appointments:
        messagebox.showinfo("Bilgi", "Hiç randevunuz yok.")
    else:
        result = "\n".join([f"{appt[0]} - {appt[1]} {appt[2]} ({appt[3]})" for appt in appointments])
        messagebox.showinfo("Randevularınız", result)


# Doktor profili düzenleme
def edit_doctor_profile(user):
    profile_window = Toplevel()
    profile_window.title("Profilim")
    profile_window.configure(bg="white")

    Label(profile_window, text="Çalışma Saatleri:", bg="white").pack()
    entry_working_hours = Entry(profile_window)
    entry_working_hours.pack(pady=5)

    Label(profile_window, text="Uzmanlık:", bg="white").pack()
    entry_specialty = Entry(profile_window)
    entry_specialty.pack(pady=5)

    rounded_button(profile_window, "Güncelle",
                   lambda: update_doctor_profile(user, entry_working_hours.get(), entry_specialty.get()))


# Doktor profil güncelleme
def update_doctor_profile(user, working_hours, specialty):
    cursor.execute("UPDATE Doctors SET working_hours = ?, specialty = ? WHERE email = ?",
                   (working_hours, specialty, user[2]))
    conn.commit()
    messagebox.showinfo("Başarılı", "Profil güncellendi!")


# Yönetici Dashboard
def admin_dashboard(user):
    admin_window = Toplevel()
    admin_window.title("Yönetici Paneli")
    admin_window.configure(bg="white")

    Label(admin_window, text="Yönetici Paneli", font=("Arial", 16), bg="white").pack(pady=10)

    rounded_button(admin_window, "Randevu Yönetimi", lambda: manage_appointments())
    rounded_button(admin_window, "Doktor Yönetimi", lambda: manage_doctors())
    rounded_button(admin_window, "Departman Yönetimi", lambda: manage_departments())


# Randevu yönetimi
def manage_appointments():
    manage_window = Toplevel()
    manage_window.title("Randevu Yönetimi")
    manage_window.configure(bg="white")

    cursor.execute("SELECT * FROM Appointments")
    appointments = cursor.fetchall()

    if not appointments:
        messagebox.showinfo("Bilgi", "Hiç randevu yok.")
    else:
        result = "\n".join([
                               f"ID: {appt[0]}, Hasta ID: {appt[1]}, Doktor: {appt[2]}, Tarih: {appt[3]}, Saat: {appt[4]}, Durum: {appt[5]}"
                               for appt in appointments])
        messagebox.showinfo("Tüm Randevular", result)


# Doktor yönetimi
def manage_doctors():
    manage_window = Toplevel()
    manage_window.title("Doktor Yönetimi")
    manage_window.configure(bg="white")

    Label(manage_window, text="Yeni Doktor Ekle", bg="white").pack(pady=10)

    Label(manage_window, text="Doktor Adı:", bg="white").pack()
    entry_doctor_name = Entry(manage_window)
    entry_doctor_name.pack(pady=5)

    Label(manage_window, text="E-posta:", bg="white").pack()
    entry_doctor_email = Entry(manage_window)
    entry_doctor_email.pack(pady=5)

    Label(manage_window, text="Departman:", bg="white").pack()
    entry_doctor_department = Entry(manage_window)
    entry_doctor_department.pack(pady=5)

    Label(manage_window, text="Çalışma Saatleri:", bg="white").pack()
    entry_doctor_working_hours = Entry(manage_window)
    entry_doctor_working_hours.pack(pady=5)

    rounded_button(manage_window, "Ekle",
                   lambda: add_doctor(entry_doctor_name.get(), entry_doctor_email.get(), entry_doctor_department.get(),
                                      entry_doctor_working_hours.get()))


# Doktor ekleme
def add_doctor(name, email, department, working_hours):
    cursor.execute("INSERT INTO Doctors (name, email, department_id, working_hours) VALUES (?, ?, ?, ?)",
                   (name, email, department, working_hours))
    conn.commit()
    messagebox.showinfo("Başarılı", "Doktor başarıyla eklendi!")


# Departman yönetimi
def manage_departments():
    manage_window = Toplevel()
    manage_window.title("Departman Yönetimi")
    manage_window.configure(bg="white")

    Label(manage_window, text="Yeni Departman Ekle", bg="white").pack(pady=10)

    Label(manage_window, text="Departman Adı:", bg="white").pack()
    entry_department_name = Entry(manage_window)
    entry_department_name.pack(pady=5)

    rounded_button(manage_window, "Ekle", lambda: add_department(entry_department_name.get()))


# Departman ekleme
def add_department(name):
    cursor.execute("INSERT INTO Departments (name) VALUES (?)", (name,))
    conn.commit()
    messagebox.showinfo("Başarılı", "Departman başarıyla eklendi!")


# Kayıt ekranı
def open_register_window(cursor, conn):
    register_window = Toplevel()
    register_window.title("Kayıt Ol")
    register_window.configure(bg="white")

    Label(register_window, text="Ad:", bg="white").pack()
    entry_name = Entry(register_window)
    entry_name.pack(fill=X, padx=5, pady=5)

    Label(register_window, text="Soyad:", bg="white").pack()
    entry_surname = Entry(register_window)
    entry_surname.pack(fill=X, padx=5, pady=5)

    Label(register_window, text="E-posta:", bg="white").pack()
    entry_email = Entry(register_window)
    entry_email.pack(fill=X, padx=5, pady=5)

    Label(register_window, text="Şifre:", bg="white").pack()
    entry_password = Entry(register_window, show="*")
    entry_password.pack(fill=X, padx=5, pady=5)

    Label(register_window, text="Şifre Onayı:", bg="white").pack()
    entry_password_confirm = Entry(register_window, show="*")
    entry_password_confirm.pack(fill=X, padx=5, pady=5)

    rounded_button(register_window, "Kayıt Ol",
                   lambda: register_user(cursor, conn, entry_name, entry_surname, entry_email, entry_password,
                                         entry_password_confirm))


# Giriş ekranı
def open_login_window(cursor):
    login_window = Toplevel()
    login_window.title("Giriş Yap")
    login_window.configure(bg="white")

    Label(login_window, text="E-posta:", bg="white").pack()
    entry_login_email = Entry(login_window)
    entry_login_email.pack(fill=X, padx=5, pady=5)

    Label(login_window, text="Şifre:", bg="white").pack()
    entry_login_password = Entry(login_window, show="*")
    entry_login_password.pack(fill=X, padx=5, pady=5)

    rounded_button(login_window, "Giriş Yap", lambda: login_user(cursor, entry_login_email, entry_login_password))


# Ana pencere
if __name__ == "__main__":
    conn, cursor = initialize_db()

    root = Tk()
    root.title("Hastane Randevu Sistemi")
    root.configure(bg="white")

    rounded_button(root, "Kayıt Ol", lambda: open_register_window(cursor, conn))
    rounded_button(root, "Giriş Yap", lambda: open_login_window(cursor))

    root.mainloop()
    conn.close()