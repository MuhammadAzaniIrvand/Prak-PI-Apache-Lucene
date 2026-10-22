# Praktikum Penelusuran Informasi — Apache Lucene & Search Interface

Modul praktikum ini membahas transisi dari implementasi manual Information Retrieval (Python, dictionary, postings list, TF-IDF manual) ke mesin pencari industri nyata menggunakan **Apache Lucene**.

---

## 📚 Struktur Modul Praktikum (~90 Menit)

| Sesi | Topik Utama | Berkas Terkait |
| :--- | :--- | :--- |
| **Sesi 1** | Pengantar Teori & Peta Konsep | Konseptual |
| **Sesi 2** | Indexing Dokumen | `java/Indexer.java`, `03_indexing.py` |
| **Sesi 3** | Searching & Scoring dengan `--explain` | `java/Searcher.java`, `04_searching.py` |
| **Sesi 4** | Eksperimen Analyzer | `java/AnalyzerUtil.java`, `05_eksperimen_analyzer.py` |
| **Sesi 5** | Web Interface (Search Server & UI) | `java/SearchServer.java`, `web/index.html` |

---

## 🚀 Cara Menjalankan Praktikum

### 1. Setup Awal (Download JAR & Compile)
```bash
python3 02_setup_lucene.py
```

### 2. Tahap Indexing
Membaca dokumen JSON hasil scraping dan membangun *inverted index*:
```bash
python3 03_indexing.py
```

### 3. Tahap Searching & Explain Skor
Mencari dokumen dan melihat rincian perhitungan rumus TF-IDF:
```bash
python3 04_searching.py "pemerintah" --explain --limit 1
```

### 4. Eksperimen Perbandingan Analyzer
Membandingkan performa dan hasil pencarian dari berbagai jenis *Analyzer*:
```bash
python3 05_eksperimen_analyzer.py
```

### 5. Menjalankan Antarmuka Web
Menghidupkan HTTP server Java dan membuka antarmuka pencarian di browser:
```bash
java -cp "java/lib/*:java" SearchServer --index index
```
Lalu akses **`http://localhost:8080`** di browser.

---

## 🧑🏫 Naskah Penjelasan Dosen / Asisten ke Praktikan

### Sesi 1: Pengantar Teori & Motivasi (15 Menit)
* **Jembatan dari Kelas ke Industri:** 
  > "Di pertemuan sebelumnya, kalian telah membuat mesin pencari dari nol menggunakan struktur data Python (`dict` dan `list`) serta menghitung TF-IDF baris demi baris. Apakah cara itu dipakai di industri nyata? Tidak untuk skala besar. Di sinilah **Apache Lucene** hadir — *core engine* di balik Elasticsearch dan Apache Solr."
* **Peta Konsep:**
  * Preprocessing $\rightarrow$ **`Analyzer`** (`StandardAnalyzer`, `WhitespaceAnalyzer`)
  * Inverted Index $\rightarrow$ **`IndexWriter`, `Document`, `Field`**
  * TF-IDF Scoring $\rightarrow$ **`ClassicSimilarity`**
  * Query & Ranking $\rightarrow$ **`QueryParser`, `IndexSearcher`**

---

### Sesi 2: Indexing Dokumen (20 Menit)
* **Rujukan Kode (`java/Indexer.java` baris 66–74):**
  ```java
  Document luceneDoc = new Document();
  luceneDoc.add(new StringField("id", doc.getOrDefault("id", ""), Field.Store.YES));
  luceneDoc.add(new TextField("title", doc.getOrDefault("title", ""), Field.Store.YES));
  luceneDoc.add(new TextField("body", doc.getOrDefault("body", ""), Field.Store.YES));
  luceneDoc.add(new StoredField("url", doc.getOrDefault("url", "")));
  ```
* **Poin Penjelasan:**
  * **`StringField`**: Disimpan utuh untuk *exact match* (seperti ID berita).
  * **`TextField`**: Dilewatkan ke Analyzer, di-tokenisasi, dan dimasukkan ke *inverted index* untuk *full-text search*.
  * **`StoredField`**: Tidak di-index, hanya disimpan agar URL-nya bisa langsung diambil saat dokumen muncul di hasil pencarian.

---

### Sesi 3: Searching & Scoring dengan `--explain` (20 Menit)
* **Rujukan Kode (`java/Searcher.java` baris 50–55):**
  ```java
  IndexSearcher searcher = new IndexSearcher(reader);
  searcher.setSimilarity(similarity);
  QueryParser parser = new QueryParser(field, analyzer);
  Query query = parser.parse(queryStr);
  TopDocs topDocs = searcher.search(query, limit);
  ```
* **Demonstrasi `--explain`:**
  ```bash
  python3 04_searching.py "pemerintah" --explain --limit 1
  ```
* **Penjelasan Konsep Skor (`tf`, `idf`, `fieldNorm`):**
  * **`tf` (Term Frequency):** Dihitung sebagai akar kuadrat dari frekuensi kemunculan term ($\sqrt{\text{freq}}$). Ini digunakan untuk meredam dominasi term yang muncul terlalu sering agar skor relevansi tidak bias.
  * **`idf` (Inverse Document Frequency):** Menunjukkan seberapa langka term tersebut di seluruh dokumen. Semakin langka term, semakin tinggi bobotnya.
  * **`fieldNorm` (Field Normalization):** Faktor penalti berdasarkan panjang dokumen. Artikel berita yang sangat panjang secara alami memiliki frekuensi kata yang tinggi, sehingga `fieldNorm` bertindak menyeimbangkannya agar adil dengan dokumen pendek.

### Sesi 3b: Eksperimen Similarity (Optional, 10 Menit)
* **Default:** `ClassicSimilarity` (TF-IDF)
* **Switch ke BM25:** Tambahkan argumen `--similarity bm25` pada `Indexer.java` (Sesi 2) dan `Searcher.java` (Sesi 3):
  ```bash
  python3 03_indexing.py      # rebuild index dengan BM25
  python3 04_searching.py "pemerintah" --explain
  ```
* **Perbedaan utama:** BM25 menambahkan saturasi skor TF sehingga frekuensi kata yang sangat tinggi tidak terlalu dominan. Cocok untuk dokumen dengan panjang yang sangat bervariasi.

---

### Sesi 4: Eksperimen Analyzer (15 Menit)
* **Jalankan:** `python3 05_eksperimen_analyzer.py`
* **Apa yang dibandingkan:** Skrip membangun tiga index terpisah dengan analyzer berbeda, lalu menjalankan query yang sama pada ketiganya untuk melihat perbedaan jumlah hit dan ranking:
  * **`index_standard`** — `StandardAnalyzer`: tokenisasi + lowercase + stopword English
  * **`index_indonesian`** — `Custom Indonesian`: `StandardTokenizer` + `LowerCaseFilter` + stopword Indonesia
  * **`index_whitespace`** — `WhitespaceAnalyzer`: split spasi saja, tanpa preprocessing lainnya
* **Output:** Tiap analyzer menghasilkan folder index sendiri (`index_standard/`, `index_indonesian/`, `index_whitespace/`) dan mencetak jumlah hit + top-3 skor per query.
* **Diskusi Interaktif:**
  * *'Kenapa query `"yang dan untuk"` menghasilkan hit berbeda di setiap analyzer?'* (Karena kata-kata tersebut adalah stopword di Indonesian/Standard, tetapi tidak di Whitespace).
  * *'Kenapa huruf kapital berpengaruh pada WhitespaceAnalyzer?'* (Karena tidak ada `LowerCaseFilter`, sehingga "Indonesia" dan "indonesia" dianggap dua token yang berbeda).
  * *'Mana analyzer paling cocok untuk dokumen berita bahasa Indonesia? Kenapa?'*

---

### Sesi 5: Web Interface (10 Menit)
* **Poin Penjelasan:** Lucene sangat fleksibel dan mudah di-embed ke dalam REST API / Web Server menggunakan `HttpServer` bawaan Java tanpa perlu framework yang berat. Praktikan dapat mengetik query di **`http://localhost:8080`**, melihat cuplikan berita, dan mencentang opsi *explain* untuk melihat rincian skor secara visual.
