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

**Peran AI.** Ketidaksesuaian ini saya temukan ketika memeriksa penanganan operator pada lexer dan mencocokkannya dengan SPESIFIKASI.md bagian 2.5. Saya kemudian meminta AI mengonfirmasi apakah operator <> belum dapat dikenali sebagai satu token karena belum memiliki aturan khusus, serta apakah hal tersebut berbeda dengan operator !=. AI mengonfirmasi bahwa != sudah memiliki aturan eksplisit, sedangkan <> belum, sehingga belum sesuai dengan prinsip maximal munch. Hasil perbaikan diverifikasi menggunakan test regresi yang gagal sebelum perbaikan dan lulus sesudahnya.



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

**Peran AI.** Setelah menemukan masalah pada penanganan tanda kutip di dalam string, saya menggunakan contoh 'Rif''q' untuk menguji perilaku lexer. Saya juga menanyakan kepada AI apakah nama yang mengandung titik, seperti Alif M. Kakak, atau tanda hubung, seperti Arif F-sa, perlu diuji sebagai bagian dari kasus ini. AI mengonfirmasi bahwa titik dan tanda hubung tidak berkaitan dengan masalah yang ditemukan karena bug terletak pada penanganan tanda kutip tunggal. Contoh nama tersebut, bersama contoh Rif'q, kemudian dijalankan untuk memeriksa perilaku lexer. Test regresi dibuat menggunakan contoh yang secara khusus mengandung tanda kutip dan diverifikasi gagal sebelum perbaikan serta lulus sesudahnya.

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

**Peran AI.** Bug ini saya temukan ketika test dosen test_keyword_huruf_kecil gagal. Saya kemudian memeriksa fungsi _word() dan mencocokkan proses pencocokan keyword dengan SPESIFIKASI.md bagian 2.2. Dari pemeriksaan tersebut, saya menemukan bahwa pencocokan keyword masih membedakan huruf besar dan kecil, sedangkan aturan SQL tidak demikian. Saya menggunakan AI untuk mengonfirmasi apakah hal tersebut memang menjadi penyebab kegagalan test. Setelah analisis dikonfirmasi, perbaikan dilakukan dengan menormalisasi teks sebelum dicocokkan dengan KEYWORDS. Hasilnya diverifikasi menggunakan test regresi dengan bentuk campuran huruf (Select), serta memastikan kata selection dan fromage tetap dikenali sebagai IDENT.

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

**Peran AI.** Saya memahami bahwa scope pada query SQL yang bersarang dapat memiliki alias tabel dengan nama yang sama, sehingga perlu ada aturan untuk menentukan alias mana yang digunakan. Untuk memastikan pemahaman tersebut, saya meminta AI mengonfirmasi apakah kondisi ini dapat dianalogikan dengan nested if pada pemrograman. AI membenarkan bahwa alias pada subquery dapat menggunakan nama yang sama dengan alias pada query luar, tetapi keduanya merujuk ke tabel yang berbeda sesuai scope masing-masing. Pengujian regresi kemudian dibuat menggunakan contoh SQL sendiri dengan alias p pada tabel pelanggan di query luar dan tabel pesanan di subquery. Hasilnya diperiksa sebelum dan sesudah perbaikan, dari ketiga referensi p.id yang awalnya terhubung ke pelanggan menjadi pelanggan, pelanggan, dan pesanan.

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

**Peran AI.** Setelah menemukan bahwa fungsi _delete() tidak menutup scope yang sebelumnya dibuka, saya menanyakan kepada AI maksud dari kondisi DELETE tidak melakukan pop dan apakah masalah tersebut berkaitan dengan shadowing. AI menjelaskan bahwa keduanya merupakan masalah yang berbeda: shadowing berkaitan dengan urutan pencarian alias pada scope, sedangkan bug pada DELETE terjadi karena scope tidak ditutup setelah proses resolusi selesai. Penjelasan tersebut membantu memperjelas perbedaan kedua masalah. Hasil perbaikan diverifikasi menggunakan test regresi yang memeriksa bahwa Resolver.scope kembali kosong, hanya satu error muncul, dan pesan diagnostiknya menyebut alias s.

---

---

## Bug 6: Subquery di UPDATE dihitung sebagai operasi U

**Ditemukan oleh:** M. Ramadhan Kurniawan · **Diperbaiki oleh:** M. Ramadhan Kurniawan

**Gejala.** Menurut SPESIFIKASI.md bagian 5, pada statement UPDATE hanya tabel target yang berstatus U, sedangkan tabel lain yang muncul lewat subquery, baik di SET maupun di WHERE, berstatus R. Aturan itu berlaku umum: membaca tabel lewat subquery selalu R, apa pun jenis statement luarnya. Analyzer sebelumnya memberi U pada semua tabel di statement UPDATE, termasuk tabel yang hanya dibaca di dalam subquery. Hasilnya, tabel yang tidak pernah diubah tercatat sebagai tabel yang diubah. Dampak ini terlihat pada laporan_penjualan.sql, ketika test_matrix_laporan_penjualan menghasilkan pesanan: RUD padahal seharusnya RD. Bug ini awalnya tertutup oleh kegagalan lain karena file yang sama memuat INSERT ... SELECT yang belum bisa di-parse sebelum T1 selesai.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
UPDATE a SET x = 1 WHERE id IN (SELECT id FROM b);
Hasil sebelum perbaikan: a bernilai U dan b juga bernilai U. Hasil yang diharapkan: a bernilai U dan b bernilai R.
```

**Akar masalah.** Akar masalahnya ada pada cabang UPDATE di fungsi analyze_statement(). Analyzer bekerja di atas pohon sintaks (AST), yaitu representasi program sebagai pohon node yang dibahas di Bab 5 (Representing Code) buku Crafting Interpreters, dan aturan operasinya diterapkan per jenis node. Fungsi _collect() menerima parameter op yang menentukan operasi apa yang ditempelkan ke setiap tabel di dalam subquery. Pada cabang UPDATE, kedua pemanggilan _collect() untuk ekspresi di SET dan di WHERE meneruskan nilai "U", sehingga seluruh tabel di dalam subquery ikut diberi U. Padahal operasi U hanya berlaku untuk tabel target yang sudah dicatat pada baris pertama cabang tersebut. Cabang DELETE yang letaknya tepat di bawahnya sudah memakai "R", sehingga kesalahan hanya terjadi pada UPDATE.

**Perbaikan.** Perbaikannya dilakukan di file crud/analyzer.py, pada fungsi analyze_statement(), cabang UPDATE. Argumen op pada kedua pemanggilan _collect() diganti dari "U" menjadi "R". Baris usage[stmt.table.name].add("U") tidak diubah karena tabel target memang berstatus U. Dengan begitu, tabel di dalam subquery hanya dibaca dan statement UPDATE menghasilkan U untuk target saja.

Alternatif yang dipertimbangkan adalah membiarkan analyzer seperti semula, lalu menambah langkah sesudahnya yang menghapus operasi U dari semua tabel selain target. Alternatif ini tidak dipilih karena hanya menutupi gejalanya, menambah satu langkah pemrosesan, dan sumber kesalahannya tetap ada di argumen yang diteruskan ke _collect(). Mengganti dua argumen langsung di sumbernya lebih sederhana dan mudah diperiksa.

**Test regresi.** test_regresi_update_subquery_dibaca_bukan_diubah. Test ini memeriksa bahwa hasil analyze_statement() untuk UPDATE dengan subquery di SET dan di WHERE adalah a bernilai U, serta b dan c bernilai R.

**Peran AI.** AI membantu menemukan bug ini ketika memeriksa hasil CRUD matrix pada laporan_penjualan.sql, ketika tabel pesanan mendapatkan status RUD padahal seharusnya RD. AI menunjukkan bahwa kemungkinan masalahnya terdapat pada cabang UPDATE di fungsi analyze_statement(), khususnya pada operasi yang diteruskan melalui _collect(). Setelah memeriksa bagian tersebut, saya menemukan bahwa pemanggilan _collect() untuk ekspresi SET dan WHERE sama-sama menggunakan operasi "U", padahal tabel di dalam subquery hanya seharusnya mendapatkan operasi "R". Perbaikan diterapkan dengan mengubah kedua argumen tersebut, kemudian diverifikasi menggunakan test regresi yang memastikan tabel target mendapatkan U, sedangkan tabel yang digunakan dalam subquery mendapatkan R.

---

---

## Bug 7: LEFT OUTER JOIN ditolak oleh parser

**Ditemukan oleh:** M. Ramadhan Kurniawan · **Diperbaiki oleh:** M. Ramadhan Kurniawan

**Gejala.** Grammar pada SPESIFIKASI.md bagian 3 menyatakan bahwa join memiliki bentuk [ "INNER" | "LEFT" [ "OUTER" ] ] "JOIN", sehingga kata OUTER boleh muncul setelah LEFT. Parser sebelumnya menolak bentuk tersebut dan melaporkan error Baris 1, kolom 25: diharapkan JOIN, ditemukan 'OUTER'. Statement yang valid menurut grammar menjadi gagal di-parse dan tidak ikut dihitung dalam CRUD matrix, sehingga tabel pada statement itu hilang dari hasil.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT a.id FROM a LEFT OUTER JOIN b ON b.a_id = a.id;
```

**Akar masalah.** Akar masalahnya ada pada fungsi _join() di parser. Di Bab 6 (Parsing Expressions) buku Crafting Interpreters, parser recursive descent dibuat dengan menerjemahkan setiap aturan grammar menjadi kode, dan bagian opsional pada grammar diterjemahkan menjadi pengecekan yang boleh tidak cocok. Pada grammar join, OUTER adalah bagian opsional setelah LEFT, tetapi kode lama langsung menuntut token JOIN setelah mengenali LEFT, sehingga bagian opsional itu tidak pernah diterjemahkan. Kata OUTER sendiri sudah dikenali lexer sebagai KEYWORD, jadi kesalahannya baru terlihat di parser. Test join yang ada sebelumnya hanya memakai LEFT JOIN dan INNER JOIN tanpa OUTER, sehingga bug ini tidak pernah terpicu.

**Perbaikan.** Perbaikannya dilakukan di file crud/parser.py, pada fungsi _join(), dengan menambahkan self._match_kw("OUTER") di dalam cabang LEFT, tepat setelah kind = "LEFT". Fungsi _match_kw() mengonsumsi OUTER apabila ada dan tidak melakukan apa pun apabila tidak ada, sehingga LEFT JOIN biasa tetap diterima. Pengecekan sengaja diletakkan di dalam cabang LEFT agar INNER OUTER JOIN tetap ditolak karena grammar hanya mengizinkan OUTER setelah LEFT.

Ada dua alternatif yang dipertimbangkan. Alternatif pertama adalah menerima OUTER setelah INNER maupun LEFT. Alternatif ini tidak dipilih karena parser menjadi menerima lebih banyak daripada yang diizinkan grammar. Alternatif kedua adalah menyimpan jenis join LEFT OUTER sebagai nilai kind tersendiri. Alternatif ini tidak dipilih karena LEFT JOIN dan LEFT OUTER JOIN bermakna sama sehingga satu nilai LEFT sudah cukup.

**Test regresi.** test_regresi_left_outer_join_diterima. Test ini memeriksa bahwa SELECT a.id FROM a LEFT OUTER JOIN b ON b.a_id = a.id tidak menghasilkan error parse dan bahwa jenis join-nya adalah LEFT.

**Peran AI.** AI membantu menemukan bug ini ketika membandingkan grammar join pada SPESIFIKASI.md bagian 3 dengan implementasi fungsi _join() pada parser. AI menunjukkan bahwa grammar memperbolehkan penggunaan OUTER setelah LEFT, tetapi parser sebelumnya langsung mengharapkan JOIN setelah menemukan LEFT. Setelah memeriksa bagian tersebut, saya memahami bahwa parser belum menangani OUTER sebagai bagian opsional dari grammar. Saya kemudian menerapkan pengecekan OUTER pada cabang LEFT agar LEFT JOIN dan LEFT OUTER JOIN sama-sama dapat diterima, tanpa membuat INNER OUTER JOIN ikut diterima. Hasil perbaikan diverifikasi menggunakan test regresi yang gagal sebelum perbaikan dan lulus sesudahnya.

---

## Bug 8: Resolusi kolom tanpa qualifier pada derived table menghasilkan nilai None

**Ditemukan oleh:** Julfi al Fikri Abdillah · Diperbaiki oleh: Julfi al Fikri Abdillah

**Gejala.** Menurut spesifikasi, kolom tanpa qualifier yang merujuk ke tabel virtual dari derived table (subquery di FROM yang memiliki alias) harus di-resolve ke nama alias subquery tersebut (misalnya "<subquery sub>"). Sebelumnya, resolver mengembalikan nilai None untuk kolom tanpa qualifier pada derived table, sehingga analyzer gagal mendeteksi penggunaan kolom tersebut secara akurat.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT nama FROM (SELECT nama, id FROM pelanggan) AS sub;
```

**Akar masalah.** Akar masalahnya ada pada fungsi _column() di modul resolver.py. Ketika mengevaluasi kolom tanpa qualifier, pengecekan lingkup scope hanya memeriksa tabel fisik biasa dan belum menangani string format penamaan khusus virtual (derived table) yang menggunakan format pembungkus <subquery alias>, sehingga kolom dari subquery dianggap tidak teretensi ke target yang benar.

**Perbaikan.** Perbaikannya dilakukan di file crud/resolver.py, dengan menambahkan fungsi pembantu _target_of() serta menyesuaikan penanganan resolusi pada _column() agar mengenali entri subquery bertipe virtual di dalam scope entries, sehingga col.resolved terisi string <subquery alias> dengan benar.

**Test regresi.** test_resolver_derived_table_kolom_tanpa_qualifier.

**Peran AI.** AI membantu mengidentifikasi dan merumuskan perbaikan bug terkait resolusi kolom tanpa qualifier pada derived table ketika ditemukan bahwa kolom dari subquery di klausa FROM menghasilkan nilai None. Saya berdiskusi dengan AI mengenai bagaimana struktur entri scope virtual disimpan pada Resolver, lalu AI memberikan saran implementasi fungsi pembantu _target_of() agar format string virtual <subquery alias> dapat dikenali dengan benar. Perbaikan tersebut kemudian diverifikasi menggunakan unit test regresi dan dipastikan lulus.

## Bug 9: Kesalahan Penanganan Presedensi Operator Logika AND dan OR (Digabungkan dalam Satu Loop)

**Ditemukan oleh:** Julfi al Fikri Abdillah · Diperbaiki oleh: Julfi al Fikri Abdillah

**Gejala.** Berdasarkan spesifikasi, operator OR berada pada tingkat presedensi 1 (terendah) dan AND pada tingkat 2, yang berarti AND harus dievaluasi lebih dahulu dibandingkan OR. Pada implementasi awal parser, logika pemrosesan AND dan OR digabung ke dalam satu perulangan linier yang sama. Akibatnya, ekspresi seperti a = 1 OR b = 2 AND c = 3 dibaca keliru dari kiri ke kanan menjadi (a = 1 OR b = 2) AND c = 3, sehingga prioritas evaluasi logika menjadi salah.

**Reproduksi minimal.** SQL terpendek yang memicu bug:

```sql
SELECT * FROM produk WHERE a = 1 OR b = 2 AND c = 3;
```

**Akar masalah.** Akar masalahnya terletak pada struktur fungsi recursive descent di modul parser. Dalam buku Crafting Interpreters Bab 6, tata bahasa yang memiliki tingkat prioritas berbeda harus dipisahkan ke dalam fungsi atau lapisan aturan turunan yang berbeda. Menggabungkan AND dan OR dalam satu tingkat perulangan menghilangkan efek hierarki prioritas, sehingga asosiatif dan presedensi operator gagal dijaga.

**Perbaikan.** Perbaikan dilakukan di file parser dengan memecah fungsi ekspresi logika menjadi hierarki bertingkat yang terpisah secara tegas, yaitu _or() memanggil _or_expr dan _and() memanggil _and_expr. Dengan pemisahan fungsi ini, operator yang ikatannya lebih lemah (OR) berada di lapisan luar, memastikan AND dikelompokkan dan dievaluasi terlebih dahulu.

**Test regresi.** test_parser_presedensi_and_or.

**Peran AI.** AI membantu mengidentifikasi akar permasalahan mengapa ekspresi logika berantai AND dan OR dievaluasi keliru akibat digabung ke dalam satu perulangan linier yang sama. AI menjelaskan lebih dalam mengenai konsep pemisahan fungsi recursive descent bertingkat per tingkat prioritas operator berdasarkan buku Crafting Interpreters Bab 6, serta membantu memvalidasi aturan hierarki presedensi sesuai dengan SPESIFIKASI.md bagian 3.1. Perbaikan kemudian diuji dan diverifikasi menggunakan unit test regresi
