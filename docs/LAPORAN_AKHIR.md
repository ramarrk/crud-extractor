# Laporan Akhir

## 1. Hasil evaluasi

Tempel keluaran `python evaluate.py` setelah `data/ground_truth.csv` dilengkapi.

```text
Dievaluasi: audit.sql, campuran_error.sql, laporan_penjualan.sql, pemeliharaan.sql (27 triple)

Metode   Precision  Recall     F1
parser        1.00    1.00   1.00
regex         0.65    0.81   0.72

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
Pendekatan regex berbasis pencocokan pattern matching akan keliru oleh teks di dalam string atau komentar sehingga mengira kata SELECT atau FROM di dalam string SELECT sebagai awal statement baru atau tabel tambahan, yang berujung pada ekstraksi operasi CRUD yang salah. Melalui tahapan lexing, token string dipisahkan secara ketat dengan tipe T.STRING dan diabaikan dari token keyword, serta parsing membangun pohon sintaks (AST) yang memperlakukan isi string murni sebagai  data, bukan instruksi struktur bahasa.
2. Subquery Kor-relasi dengan Nama Alias Tabel yang Sama (Shadowing)
SQL: SELECT p.id FROM pelanggan p WHERE p.id IN (SELECT p.id FROM pesanan p WHERE p.total > 10);
Regex tidak memiliki pemahaman tentang scope atau batasan blok kueri. Regex akan menganggap kedua alias p merujuk ke tabel yang sama atau mencampuradukkan kolom tanpa melihat hierarki subquery. Melalui tahapan resolusi scope, parser dan resolver membangun hierarki scope yang berantai. Resolver memastikan penelusuran qualifier dimulai dari scope terdalam ke luar (shadowing) sehingga kolom p.id di dalam subquery dengan tepat terhubung ke tabel pesanan (p), sedangkan di luar terhubung ke pelanggan.
3. Kompleksitas Operator Logika dengan Presedensi Tertentu (AND vs OR)
SQL: SELECT * FROM produk WHERE a = 1 OR b = 2 AND c = 3;
Regex membaca baris teks secara linier rata kiri-kanan tanpa struktur hierarki sehingga sering kali gagal menentukan kelompok operasi mana yang harus dievaluasi lebih dahulu. Parser menggunakan tata bahasa recursive descent terstruktur (dibagi menjadi fungsi bertingkat _or(), _and(), dan _not()) yang membentuk pohon AST sesuai aturan presedensi operator, memastikan b = 2 AND c = 3 diikat dan dikelompokkan lebih dahulu sebelum di-OR-kan dengan a = 1.

## 3. Batas pendekatan kami

Minimal tiga hal yang **tidak bisa** ditangani dengan benar oleh tool ini meskipun semua bug
sudah diperbaiki. Untuk tiap batas: contoh SQL atau situasinya, akibatnya pada CRUD matrix,
dan informasi apa yang dibutuhkan untuk mengatasinya.

**Batas 1. Kolom tanpa qualifier pada query dengan lebih dari satu tabel.**
Contoh.

```sql
SELECT nama FROM pelanggan p JOIN pesanan o ON o.pid = p.id;
```

Resolver hanya melihat teks query dan tidak mengetahui kolom apa yang dimiliki tiap tabel. Kolom `nama` tidak dapat dipetakan ke `pelanggan` atau `pesanan` sehingga resolver mengeluarkan warning ambigu dan membiarkan `resolved` bernilai `None`. CRUD matrix tidak berubah karena dihitung dari klausa `FROM` dan `JOIN`, tetapi keluaran `--kolom` tidak memuat kolom `nama` untuk tabel mana pun. Informasi yang dibutuhkan adalah skema database, yaitu daftar kolom setiap tabel.

**Batas 2. Nama tabel yang ditulis dengan dan tanpa skema.**
Contoh.

```sql
SELECT 1 FROM pelanggan;
SELECT 1 FROM crm.pelanggan;
```

Tool memakai nama persis seperti yang tertulis sehingga `pelanggan` dan `crm.pelanggan` menjadi dua kolom berbeda di CRUD matrix. Jika database memiliki search_path (urutan skema default untuk nama tanpa skema) yang menunjuk ke `crm`, kedua nama itu adalah tabel yang sama dan operasi R seharusnya digabung. Informasi yang dibutuhkan adalah search_path dan daftar tabel per skema.

**Batas 3. Objek yang efeknya tidak tampak pada teks query.**
Contoh.

```sql
SELECT 1 FROM v_pelanggan_aktif;
```

Jika `v_pelanggan_aktif` adalah view (query tersimpan yang diperlakukan seperti tabel), tool mencatat R pada nama view itu dan bukan pada tabel dasar yang dibaca view tersebut. Hal serupa berlaku untuk trigger dan fungsi tersimpan. Sebuah `DELETE FROM pesanan` yang memicu trigger untuk menambah baris ke `log_pesanan` hanya tercatat sebagai D pada `pesanan`, sedangkan C pada `log_pesanan` tidak tercatat. Informasi yang dibutuhkan adalah definisi view, trigger, dan fungsi dari katalog database.

**Batas 4. Sintaks di luar grammar.**
Contoh.

```sql
WITH x AS (SELECT * FROM a) SELECT * FROM x;
SELECT 1 FROM a UNION SELECT 1 FROM b;
```

Kedua statement menghasilkan error sintaks (`WITH` ditolak di awal statement dan `UNION` ditolak karena parser mengharapkan `;`) sehingga tidak dihitung. Tabel `a` dan `b` yang sebenarnya dibaca tidak muncul di CRUD matrix. Informasi yang dibutuhkan adalah perluasan grammar untuk `WITH` dan `UNION`, serta resolver yang menambahkan scope untuk nama CTE.

## 4. Pembagian kerja
Pekerjaan dibagi berdasarkan bug yang ditemukan dan bukan berdasarkan modul. Rotasi driver dan navigator setiap 30 menit yang disarankan pada deskripsi tugas tidak kami pakai karena sulit dijalankan. Anggota berpindah antara lexer, parser, resolver, dan analyzer sesuai bug yang sedang ditemukan. Pembagian di bawah disusun dari riwayat commit.

- M. Ramadhan Kurniawan: Berfokus pada perbaikan bug pada modul Lexer, Resolver, Analyzer, dan Parser. Pada Lexer, pekerjaan meliputi penanganan operator <> menggunakan prinsip maximal munch, penanganan dua kutip tunggal berturut-turut di dalam string, serta pengenalan keyword yang tidak peka terhadap huruf besar dan kecil. Pada Resolver, pekerjaan meliputi perbaikan urutan pencarian alias pada scope bersarang (shadowing), penutupan scope pada statement DELETE agar tidak terbawa ke statement berikutnya, serta penyelesaian T2 untuk resolusi kolom tanpa qualifier. Pada Analyzer, dilakukan perbaikan agar tabel yang hanya dibaca melalui subquery pada statement UPDATE mendapatkan status R, bukan U. Pada Parser, perbaikan _synchronize agar membuang token sampai ; berikutnya, serta penerimaan bentuk LEFT OUTER JOIN.


- Julfi al Fikri Abdillah: Berfokus pada pengerjaan awal bagian-bagian TODO dan perbaikan modul Parser dan Resolver (implementasi hierarki presedensi operator AND/OR/NOT, penanganan resolusi kolom tanpa qualifier berdasarkan jumlah entri scope, perbaikan bug derived table pada kolom tanpa qualifier, serta penyusunan rangkaian unit-unit test tambahan di test_tambahan.py).

Pemahaman terhadap seluruh kode dijaga melalui pull request yang digabungkan oleh anggota lain, pembahasan perubahan melalui chat setiap kali suatu bagian selesai dikerjakan, serta dokumentasi internal yang disusun sebagai pegangan bersama. Hasil gabungan diperiksa dengan menjalankan seluruh test sebelum di-merge.



