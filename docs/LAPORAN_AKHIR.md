# Laporan Akhir

## 1. Hasil evaluasi

Tempel keluaran `python evaluate.py` setelah `data/ground_truth.csv` dilengkapi.

```text
Dievaluasi: audit.sql, campuran_error.sql, laporan_penjualan.sql, pemeliharaan.sql (27 triple)

Metode   Precision  Recall     F1
parser        1.00    0.93   0.96
regex         0.65    0.81   0.72

[parser]
  terlewat (FN):       ('pemeliharaan.sql', 3, 'crm.alamat', 'R')
  terlewat (FN):       ('pemeliharaan.sql', 3, 'crm.pelanggan', 'R')

[regex]
  salah ditemukan (FP): ('audit.sql', 16, 'sesi', 'R')
  salah ditemukan (FP): ('campuran_error.sql', 4, 'pesanan', 'R')
  salah ditemukan (FP): ('campuran_error.sql', 8, 'keranjang', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pelanggan', 'D')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pelanggan', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'pesanan', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 2, 'rahasia', 'R')
  salah ditemukan (FP): ('laporan_penjualan.sql', 15, 'pesanan', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'crm.alamat', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'crm.pelanggan', 'R')
  salah ditemukan (FP): ('pemeliharaan.sql', 2, 'pelanggan_lama', 'U')
  salah ditemukan (FP): ('pemeliharaan.sql', 15, 'crm.alamat', 'R')
  terlewat (FN):       ('audit.sql', 2, 'pesanan', 'R')
  terlewat (FN):       ('laporan_penjualan.sql', 3, 'pelanggan', 'R')
  terlewat (FN):       ('laporan_penjualan.sql', 3, 'pesanan', 'R')
  terlewat (FN):       ('pemeliharaan.sql', 3, 'crm.alamat', 'R')
  terlewat (FN):       ('pemeliharaan.sql', 3, 'crm.pelanggan', 'R')
```

## 2. Tiga kasus di mana regex salah

Untuk tiap kasus: SQL-nya, kesalahan regex, dan mengapa parser benar (kaitkan dengan konsep
lexing, parsing, atau resolusi).

1. Komentar atau String yang Menyerupai Keyword SQL.
SQL: SELECT * FROM pelanggan WHERE catatan LIKE '%SELECT%FROM%';
Pendekatan regex berbasis pencocokan pattern matching akan keliru oleh teks di dalam string atau komentar, sehingga mengira kata SELECT atau FROM di dalam string SELECT sebagai awal statement baru atau tabel tambahan, yang berujung pada ekstraksi operasi CRUD yang salah. Melalui tahapan lexing, token string dipisahkan secara ketat dengan tipe T.STRING dan diabaikan dari token keyword, serta parsing membangun pohon sintaks (AST) yang memperlakukan isi string murni sebagai  data, bukan instruksi struktur bahasa.
2. Subquery Kor-relasi dengan Nama Alias Tabel yang Sama (Shadowing)
SQL: SELECT p.id FROM pelanggan p WHERE p.id IN (SELECT p.id FROM pesanan p WHERE p.total > 10);
Regex tidak memiliki pemahaman tentang scope atau batasan blok kueri. Regex akan menganggap kedua alias p merujuk ke tabel yang sama atau mencampuradukkan kolom tanpa melihat hierarki subquery. Melalui tahapan resolusi scope, parser dan resolver membangun hierarki scope yang berantai. Resolver memastikan penelusuran qualifier dimulai dari scope terdalam ke luar (shadowing), sehingga kolom p.id di dalam subquery dengan tepat terhubung ke tabel pesanan (p), sedangkan di luar terhubung ke pelanggan.
3. Kompleksitas Operator Logika dengan Presedensi Tertentu (AND vs OR)
SQL: SELECT * FROM produk WHERE a = 1 OR b = 2 AND c = 3;
Regex membaca baris teks secara linier rata kiri-kanan tanpa struktur hierarki, sehingga sering kali gagal menentukan kelompok operasi mana yang harus dievaluasi lebih dahulu. Parser menggunakan tata bahasa recursive descent terstruktur (dibagi menjadi fungsi bertingkat _or(), _and(), dan _not()) yang membentuk pohon AST sesuai aturan presedensi operator, memastikan b = 2 AND c = 3 diikat dan dikelompokkan lebih dahulu sebelum di-OR-kan dengan a = 1.

## 3. Batas pendekatan kami

Minimal tiga hal yang **tidak bisa** ditangani dengan benar oleh tool ini meskipun semua bug
sudah diperbaiki. Untuk tiap batas: contoh SQL atau situasinya, akibatnya pada CRUD matrix,
dan informasi apa yang dibutuhkan untuk mengatasinya.

1.
2.
3.

## 4. Pembagian kerja
Siapa mengerjakan apa, dan bagaimana kalian memastikan keduanya memahami seluruh kode.
-
-Julfi al Fikri Abdillah: Berfokus pada pengerjaan awal bagian-bagian TODO dan perbaikan modul Parser dan Resolver (implementasi hierarki presedensi operator AND/OR/NOT, penanganan resolusi kolom tanpa qualifier berdasarkan jumlah entri scope, perbaikan bug derived table pada kolom tanpa qualifier, serta penyusunan rangkaian unit-unit test tambahan di test_tambahan.py).

Pemastian pemahamai dilakukan dengan melakukan review setiap kali bagian kode diselesaikan dan di-commit



