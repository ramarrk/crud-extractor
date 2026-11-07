# Laporan Bug

Salin blok di bawah untuk setiap bug. Bagian **Akar masalah** wajib ditulis dengan kata-kata
sendiri dan memakai konsep dari *Crafting Interpreters* (sebutkan bab). Bagian ini diuji lisan.

---

## Bug 1: Operator <> terbaca sebagai dua token

**Ditemukan oleh:** M. Ramadhan Kurniawan · **Diperbaiki oleh:** M. Ramadhan Kurniawan

**Gejala.** Di SQL, operator <> digunakan untuk menandakan operasi not equal. Namun, lexer sebelumnya masih membaca operator tersebut sebagai dua token terpisah, yaitu < dan >. Padahal, menurut SPESIFIKASI.md bagian 2.5, lexer harus menggunakan prinsip maximal munch, yaitu mengambil operator terpanjang yang cocok. Karena itu, lexer diperbaiki agar <> dikenali sebagai satu token OP. Test regresi tambahan juga dibuat untuk memastikan operator tersebut terbaca dengan benar.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```
SELECT id FROM pelanggan WHERE id <> 1;
```

**Akar masalah.** Akar masalahnya itu ada di proses pembacaan token pada lexer. Di Bab 4 (Scanning) buku Crafting Interpreters dijelaskan bagaimana sebuah scanner membaca suatu karakter dan mengenalinya sebagai sebuah token. Di lexer proyek ini, operator < dan > sudah memiliki pengecekan masing-masing, tetapi belum ada pengecekan yang menggabungkan keduanya menjadi operator <> yang berakibar operator <> terbaca sebagai dua token terpisah. Hal ini juga belum sesuai dengan ketentuan maximal munch di SPESIFIKASI.md bagian 2.5.  

**Perbaikan.** Perbaikannya dilakukan di file crud/lexer.py, tepatnya pada fungsi _scan_token(), dengan menambahkan pengecekan terhadap operator <> sebelum lexer menghasilkan token < secara terpisah. Jadi, saat menemukan karakter <, lexer akan memeriksa karakter berikutnya menggunakan _match(). Pertama, lexer mengecek apakah karakter berikutnya adalah =. Jika cocok, keduanya dibaca sebagai operator <=. Jika tidak, lexer akan mengecek apakah karakter berikutnya adalah >. Jika cocok, keduanya dibaca sebagai operator <>. Apabila kedua pengecekan tersebut tidak menemukan pasangan yang cocok, lexer baru menghasilkan operator < sebagai satu token. Dengan begitu, operator <=, <>, dan < bisa dikenali dengan benar.

Cara ini menggunakan konsep lookahead dalam proses scanning yang dibahas di Bab 4 (Scanning) buku Crafting Interpreters, sekaligus mengikuti prinsip maximal munch di SPESIFIKASI.md bagian 2.5.

**Test regresi.** test_regresi_operator_tidak_sama_satu_token — memeriksa token dari a <> 1 agar nilainya menjadi a, <>, dan 1.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?

---

## Bug 2: Dua kutip di dalam string memecah token

**Ditemukan oleh:** M. Ramadhan Kurniawan · **Diperbaiki oleh:** M. Ramadhan Kurniawan

**Gejala.** Menurut SPESIFIKASI.md bagian 2.4, dua kutip berturut-turut di dalam string ('') mewakili satu karakter kutip sehingga 'Rif''q' seharusnya menjadi satu token STRING bernilai Rif'q. Lexer sebelumnya menghasilkan dua token STRING, yaitu Rif dan q. Akibatnya, parser menganggap token q sebagai sisa yang tidak dikenal dan melaporkan error Baris 1, kolom 44: diharapkan ';' di akhir statement, ditemukan 'q'. Statement yang sebenarnya valid menjadi gagal di-parse dan tidak masuk ke CRUD matrix.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT id FROM pelanggan WHERE nama = 'Rif''q';
```

**Akar masalah.**  Akar masalahnya ada pada aturan penutup string di fungsi _string(). Di Bab 4 (Scanning) buku Crafting Interpreters, scanner membaca sebuah string dengan terus maju sampai menemukan tanda kutip penutup, lalu seluruh isi di antaranya menjadi nilai token. Pada bahasa Lox tidak ada aturan escape sehingga satu kali pengecekan kutip sudah cukup. Di lexer proyek ini kode lama memakai logika yang sama, yaitu setiap kutip tunggal langsung dianggap penutup. Pada SQL, kutip yang diikuti kutip lagi adalah karakter kutip biasa di dalam string sehingga keputusan apakah sebuah kutip merupakan penutup baru dapat diambil setelah melihat karakter sesudahnya. Karena lexer tidak melakukan pengecekan tersebut, batas string ditentukan terlalu cepat dan satu lexeme terpecah menjadi dua.

**Perbaikan.** Perbaikannya dilakukan di file crud/lexer.py, pada fungsi _string(). Ketika lexer menemukan karakter ', lexer memanggil _peek() untuk melihat karakter berikutnya tanpa mengonsumsinya. Jika karakter berikutnya juga ', lexer mengonsumsi kutip kedua, menambahkan satu karakter ' ke isi string, lalu melanjutkan pembacaan. Jika karakter berikutnya bukan ', kutip tersebut dibaca sebagai penutup dan string selesai. Dengan begitu, '' di dalam string menjadi satu karakter kutip, dan string yang tidak ditutup tetap menghasilkan LexError seperti sebelumnya.

Alternatif yang dipertimbangkan adalah membaca isi string sampai kutip pertama yang ditemukan, lalu mengganti '' menjadi ' dengan replace(). Alternatif ini tidak dipilih karena batas akhir string sudah terlanjur salah ditentukan sebelum penggantian dilakukan sehingga pengecekan karakter berikutnya tetap diperlukan di dalam perulangan.

**Test regresi.** test_regresi_kutip_ganda_dalam_string. Test ini memeriksa bahwa 'Rif''q' menghasilkan satu token STRING bernilai Rif'q.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?

---

## Bug 3: Keyword huruf kecil terbaca sebagai identifier

**Ditemukan oleh:** M. Ramadhan Kurniawan · **Diperbaiki oleh:** M. Ramadhan Kurniawan

**Gejala.** Menurut SPESIFIKASI.md bagian 2.2, keyword tidak peka huruf besar atau kecil, dan nilai token keyword selalu dinormalisasi ke huruf besar. Input select Select SELECT seharusnya menghasilkan tiga token KEYWORD bernilai SELECT. Lexer sebelumnya hanya mengenali bentuk huruf besar sehingga hasilnya adalah IDENT select, IDENT Select, dan KEYWORD SELECT. Statement yang ditulis dengan huruf kecil akhirnya ditolak parser dengan pesan Baris 1, kolom 1: diharapkan awal statement (SELECT, INSERT, UPDATE, DELETE), ditemukan 'select', dan tidak ikut dihitung dalam CRUD matrix.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
select id from pelanggan;
```

**Akar masalah.** Akar masalahnya ada di fungsi _word() pada lexer. Di Bab 4 (Scanning) buku Crafting Interpreters, scanner membaca satu kata utuh terlebih dahulu, lalu mencocokkannya dengan tabel reserved words untuk menentukan apakah kata itu keyword atau identifier. Lexer proyek ini sudah mengikuti urutan tersebut, tetapi pencocokannya membandingkan teks apa adanya dengan himpunan KEYWORDS yang seluruh isinya huruf besar. Bahasa Lox peka huruf besar dan kecil sehingga cara itu cukup, sedangkan SQL tidak peka sehingga select dan Select gagal cocok lalu jatuh ke cabang IDENT. Kesalahan ini baru terlihat di parser karena lexer tidak melaporkan error apa pun, dan parser menerima token IDENT di posisi yang seharusnya diisi keyword.

**Perbaikan.** Perbaikannya dilakukan di file crud/lexer.py, pada fungsi _word(). Pencocokan dilakukan dengan text.upper() in KEYWORDS, dan nilai token keyword disimpan sebagai text.upper() sehingga selalu huruf besar sesuai SPESIFIKASI.md bagian 2.2. Cabang IDENT tidak diubah karena normalisasi nama tabel, alias, dan kolom ke huruf kecil dilakukan oleh parser. Kata seperti selection dan fromage tetap menjadi IDENT karena yang dibandingkan adalah seluruh kata dan bukan hanya awalannya.

Ada dua alternatif yang dipertimbangkan. Alternatif pertama adalah menambahkan versi huruf kecil ke dalam KEYWORDS. Alternatif ini tidak dipilih karena bentuk campuran seperti Select tetap gagal dikenali dan nilai token tetap tidak ternormalisasi. Alternatif kedua adalah mengubah seluruh teks sumber menjadi huruf besar sebelum scanning. Alternatif ini tidak dipilih karena isi string dan nama identifier ikut berubah, padahal isi string harus dipertahankan apa adanya.

**Test regresi.** test_regresi_keyword_campuran_huruf. Test ini memeriksa bahwa select Select SELECT menghasilkan tiga token bertipe KEYWORD dengan nilai SELECT.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?

---

## Bug 4: Alias di subquery tidak menutupi alias dengan nama sama di luar

**Ditemukan oleh:** M. Ramadhan Kurniawan · **Diperbaiki oleh:** M. Ramadhan Kurniawan

**Gejala.** Menurut SPESIFIKASI.md bagian 4.3, qualifier dicari mulai dari scope terdalam ke luar, dan yang pertama ditemukan dipakai sehingga alias di subquery menutupi alias yang sama di luar (shadowing). Pada query di bawah, p.id di dalam subquery seharusnya di-resolve ke pesanan sehingga hasil resolusi ketiga p.id adalah pelanggan, pelanggan, dan pesanan. Resolver sebelumnya menghasilkan pelanggan untuk ketiganya. Bug ini tidak menimbulkan error dan tidak mengubah CRUD matrix karena yang dihitung adalah tabel di klausa FROM. Dampaknya terlihat pada analisis kolom, yang hanya mencatat id milik pelanggan dan kehilangan id milik pesanan.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT p.id FROM pelanggan p WHERE p.id IN (SELECT p.id FROM pesanan p);
```

**Akar masalah.** Akar masalahnya ada pada urutan pencarian di fungsi _lookup(). Di Bab 8 (Statements and State), bagian nesting dan shadowing, dijelaskan bahwa environment memiliki penunjuk ke environment luarnya (enclosing), dan pencarian sebuah nama dimulai dari environment saat ini lalu naik ke luar sampai ditemukan. Bab 11 (Resolving and Binding), bagian resolving variable expressions, menerapkan aturan yang sama pada resolver, yaitu menelusuri scope dari yang terdalam. Di proyek ini rantai scope sudah dibentuk dengan benar, tetapi kode lama mengumpulkan scope ke sebuah list dari yang terdalam ke yang terluar, lalu menelusurinya dengan reversed(). Akibatnya scope terluar yang diperiksa lebih dahulu, entri p milik pelanggan ditemukan lebih awal, dan scope subquery yang berisi p milik pesanan tidak pernah dilihat.

**Perbaikan.** Perbaikannya dilakukan di file crud/resolver.py, pada fungsi _lookup(). Fungsi ini sekarang mulai dari self.scope, memeriksa apakah nama ada di entries scope tersebut, dan jika belum ada berpindah ke scope.parent sampai habis. Entri pertama yang cocok langsung dikembalikan sehingga scope yang paling dalam selalu menang.

Alternatif yang dipertimbangkan adalah mempertahankan list chain dan hanya menghapus pemanggilan reversed(). Hasilnya sama, tetapi alternatif ini tidak dipilih karena list tambahan tidak diperlukan, dan penelusuran langsung melalui parent lebih sederhana serta mengikuti cara Environment di Bab 8 menelusuri enclosing.

**Test regresi.** test_regresi_alias_subquery_menutupi_alias_luar. Test ini memeriksa bahwa hasil resolusi ketiga p.id berturut-turut adalah pelanggan, pelanggan, dan pesanan.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?

---

## Bug 5: Scope milik DELETE tidak ditutup dan 'bocor' ke statement berikutnya

**Ditemukan oleh:** M. Ramadhan Kurniawan · **Diperbaiki oleh:** M. Ramadhan Kurniawan

**Gejala.** Menurut SPESIFIKASI.md bagian 4.5, setiap statement berdiri sendiri, dan setelah satu statement selesai di-resolve tidak boleh ada scope tersisa sehingga alias dari statement sebelumnya tidak boleh terlihat oleh statement berikutnya. Pada SQL di bawah, alias s milik DELETE tidak boleh dikenali oleh SELECT sesudahnya sehingga s.id seharusnya menghasilkan satu error alias 's' tidak terdefinisi sesuai bagian 4.3. Resolver sebelumnya tidak menghasilkan diagnostik apa pun, dan setelah seluruh statement selesai Resolver.scope masih berisi scope sisa. Alias yang seharusnya tidak ada dianggap ada sehingga s.id di-resolve ke tabel sesi secara diam-diam.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
DELETE FROM sesi s WHERE s.a = 1;
SELECT s.id FROM pengguna u;
```

**Akar masalah.** Akar masalahnya ada pada fungsi _delete() yang membuka scope dengan _push() tetapi tidak pernah menutupnya dengan _pop(). Di Bab 11 (Resolving and Binding), bagian resolving blocks, setiap blok dibuka dengan beginScope() dan ditutup dengan endScope() sehingga tumpukan scope selalu kembali ke keadaan semula setelah blok selesai. Fungsi _select() dan _update() di proyek ini sudah menjaga pasangan tersebut, sedangkan _delete() tidak. Akibatnya scope milik DELETE tetap menjadi self.scope setelah statement selesai, lalu menjadi induk dari scope SELECT berikutnya. Ketika s tidak ditemukan di scope SELECT, pencarian naik ke induk dan menemukan s milik DELETE. Bug ini tidak terlihat oleh test terlihat karena test tersebut hanya memproses satu statement dalam satu script, sedangkan kebocoran baru berdampak ketika ada statement lain setelahnya.

**Perbaikan.** Perbaikannya dilakukan di file crud/resolver.py, pada fungsi _delete(), dengan menambahkan self._pop() di akhir fungsi setelah kondisi WHERE selesai di-resolve. Dengan begitu _delete() memiliki pasangan _push() dan _pop() seperti _select() dan _update(), dan tidak ada scope tersisa setelah statement selesai.

Alternatif yang dipertimbangkan adalah mengosongkan scope di resolve_script() setiap kali satu statement selesai. Alternatif ini tidak dipilih karena hanya menutupi gejalanya, sedangkan pasangan _push() dan _pop() yang tidak seimbang tetap ada di dalam _delete(), dan kesalahan serupa dapat muncul lagi di fungsi lain.

**Test regresi.** test_regresi_alias_delete_tidak_bocor_ke_statement_berikutnya. Test ini memeriksa bahwa setelah dua statement selesai tidak ada scope tersisa, bahwa diagnostik yang muncul hanya satu dengan level error, dan bahwa pesannya menyebut alias s.

**Peran AI.** Apakah AI membantu menemukan atau memperbaiki bug ini? Bagaimana kalian
memverifikasinya?

---