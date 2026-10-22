"""
03_indexing.py — Indexing dokumen JSON ke Lucene index

Skrip ini menjalankan Indexer.java untuk membaca dokumen hasil scraping
dan membangun inverted index menggunakan Apache Lucene.

Jalankan:
    python 03_indexing.py

Prasyarat:
    python 02_setup_lucene.py  (sudah dijalankan)
"""

import json
import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
JAVA_DIR = BASE_DIR / "java"
LIB_DIR = JAVA_DIR / "lib"
DATA_FILE = BASE_DIR / "data" / "dokumen_antara.json"
INDEX_DIR = BASE_DIR / "index"

CLASSPATH = str(LIB_DIR / "*") + os.pathsep + str(JAVA_DIR)


def print_header():
    print()
    print("=" * 62)
    print("  Tahap 2 — Indexing: Dari JSON ke Inverted Index Lucene")
    print("=" * 62)
    print()
    print("  Peta konsep:")
    print("  ┌─────────────────────────────────┬───────────────────────────────┐")
    print("  │ Praktikum sebelumnya            │ Komponen Lucene               │")
    print("  ├─────────────────────────────────┼───────────────────────────────┤")
    print("  │ Tokenisasi, stopword, stemming  │ Analyzer (StandardAnalyzer)   │")
    print("  │ Bangun inverted index           │ IndexWriter + Document/Field  │")
    print("  └─────────────────────────────────┴───────────────────────────────┘")
    print()


def check_prerequisites():
    if not LIB_DIR.exists() or not list(LIB_DIR.glob("*.jar")):
        print("  ERROR: JAR belum di-download. Jalankan dulu:")
        print("    python 02_setup_lucene.py")
        sys.exit(1)

    if not (JAVA_DIR / "Indexer.class").exists():
        print("  ERROR: Indexer.class belum ada. Jalankan dulu:")
        print("    python 02_setup_lucene.py")
        sys.exit(1)

    if not DATA_FILE.exists():
        print(f"  ERROR: File data tidak ditemukan: {DATA_FILE}")
        sys.exit(1)


def show_data_summary():
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    print(f"  Data sumber : {DATA_FILE.name}")
    print(f"  Jumlah dokumen : {len(data)}")

    if data:
        avg_len = sum(len(d.get("body", "")) for d in data) / len(data)
        print(f"  Rata-rata panjang body : {avg_len:.0f} karakter")

    print()
    print("  Field mapping:")
    print("    id           → StringField (disimpan, tidak di-index untuk pencarian)")
    print("    title        → TextField   (disimpan, di-tokenisasi, bisa dicari)")
    print("    body         → TextField   (disimpan, di-tokenisasi, bisa dicari)")
    print("    url          → StoredField  (disimpan saja, tidak bisa dicari)")
    print("    published_at → StoredField  (disimpan saja, tidak bisa dicari)")
    print()


def run_indexer():
    print("  Menjalankan Indexer ...")
    print(f"    Similarity : ClassicSimilarity (TF-IDF)")
    print(f"    Analyzer   : StandardAnalyzer")
    print()

    cmd = [
        "java", "-cp", CLASSPATH, "Indexer",
        "--json", str(DATA_FILE),
        "--index", str(INDEX_DIR),
        "--similarity", "classic",
        "--analyzer", "standard",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("  GAGAL menjalankan Indexer:\n")
        print(result.stderr)
        sys.exit(1)

    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("  Output Indexer:")
        print(result.stdout)
        return

    print(f"  Hasil indexing:")
    print(f"    Dokumen ter-index : {output.get('documents_indexed', '?')}")
    print(f"    Waktu             : {output.get('elapsed_ms', '?')} ms")

    size_bytes = output.get("index_size_bytes", 0)
    if size_bytes > 1024 * 1024:
        print(f"    Ukuran index      : {size_bytes / (1024*1024):.1f} MB")
    else:
        print(f"    Ukuran index      : {size_bytes / 1024:.0f} KB")

    print(f"    Lokasi            : {output.get('index_path', '?')}")
    print()


def show_index_files():
    if INDEX_DIR.exists():
        files = sorted(INDEX_DIR.iterdir())
        print(f"  File-file dalam folder index/ ({len(files)} file):")
        for f in files:
            size = f.stat().st_size
            print(f"    {f.name:40s} {size:>8,} bytes")
        print()


def show_next_step():
    print("  Penjelasan:")
    print("    StandardAnalyzer melakukan: lowercase → tokenisasi → hapus stopword English.")
    print("    Setiap dokumen menjadi Document Lucene dengan Field yang masing-masing")
    print("    punya tipe berbeda. TextField di-tokenisasi dan bisa dicari,")
    print("    sedangkan StoredField hanya disimpan untuk ditampilkan di hasil pencarian.")
    print()
    print("  Lanjut ke:")
    print("    python 04_searching.py")
    print()


if __name__ == "__main__":
    print_header()
    check_prerequisites()
    show_data_summary()
    run_indexer()
    show_index_files()
    show_next_step()
