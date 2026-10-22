"""
05_eksperimen_analyzer.py — Bandingkan efek Analyzer terhadap hasil pencarian

Skrip ini membangun tiga index terpisah dengan analyzer berbeda,
lalu menjalankan query yang sama pada ketiganya untuk melihat perbedaan.

Jalankan:
    python 05_eksperimen_analyzer.py

Prasyarat:
    python 02_setup_lucene.py  (sudah dijalankan)
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
JAVA_DIR = BASE_DIR / "java"
LIB_DIR = JAVA_DIR / "lib"
DATA_FILE = BASE_DIR / "data" / "dokumen_antara.json"

CLASSPATH = str(LIB_DIR / "*") + os.pathsep + str(JAVA_DIR)

ANALYZERS = [
    {
        "name": "standard",
        "label": "StandardAnalyzer",
        "desc": "Tokenisasi + lowercase + stopword English",
        "index_dir": BASE_DIR / "index_standard",
    },
    {
        "name": "whitespace",
        "label": "WhitespaceAnalyzer",
        "desc": "Split spasi saja, tanpa preprocessing lain",
        "index_dir": BASE_DIR / "index_whitespace",
    },
    {
        "name": "indonesian",
        "label": "Custom Indonesian",
        "desc": "StandardTokenizer + lowercase + stopword Indonesia",
        "index_dir": BASE_DIR / "index_indonesian",
    },
]

TEST_QUERIES = [
    ("pemerintah", "body"),
    ("Indonesia", "body"),
    ("yang dan untuk", "body"),
    ("pendidikan", "title"),
]


def print_header():
    print()
    print("=" * 62)
    print("  Tahap 5 — Eksperimen Analyzer")
    print("=" * 62)
    print()
    print("  Analyzer menentukan bagaimana teks diproses sebelum masuk")
    print("  inverted index. Ini adalah padanan langsung dari pipeline")
    print("  preprocessing yang sudah dipelajari (tokenisasi, stopword, dll).")
    print()
    print("  Eksperimen ini membandingkan tiga analyzer:")
    print()
    for a in ANALYZERS:
        print(f"    {a['label']:25s} — {a['desc']}")
    print()


def check_prerequisites():
    if not LIB_DIR.exists() or not list(LIB_DIR.glob("*.jar")):
        print("  ERROR: JAR belum di-download. Jalankan dulu:")
        print("    python 02_setup_lucene.py")
        sys.exit(1)


def build_indexes():
    print("-" * 62)
    print("  Membangun tiga index dengan analyzer berbeda ...")
    print()

    for a in ANALYZERS:
        idx = a["index_dir"]
        if idx.exists():
            shutil.rmtree(idx)

        cmd = [
            "java", "-cp", CLASSPATH, "Indexer",
            "--json", str(DATA_FILE),
            "--index", str(idx),
            "--similarity", "classic",
            "--analyzer", a["name"],
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"  GAGAL index [{a['label']}]: {result.stderr.strip()}")
            sys.exit(1)

        try:
            out = json.loads(result.stdout)
            print(f"  [{a['label']:25s}] {out['documents_indexed']} dokumen, {out['elapsed_ms']} ms")
        except json.JSONDecodeError:
            print(f"  [{a['label']:25s}] selesai")

    print()


def run_search(index_dir, query, field="body", limit=5, analyzer="standard"):
    cmd = [
        "java", "-cp", CLASSPATH, "Searcher",
        "--index", str(index_dir),
        "--query", query,
        "--field", field,
        "--limit", str(limit),
        "--similarity", "classic",
        "--analyzer", analyzer,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        return None

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def compare_queries():
    print("-" * 62)
    print("  Perbandingan hasil pencarian per query")
    print("-" * 62)

    for query, field in TEST_QUERIES:
        print()
        print(f"  Query: \"{query}\"  (field: {field})")
        print(f"  {'Analyzer':<25s} {'Hits':>6s}   Top-3 skor")
        print(f"  {'─' * 25} {'─' * 6}   {'─' * 28}")

        for a in ANALYZERS:
            data = run_search(a["index_dir"], query, field=field, limit=3, analyzer=a["name"])
            if data is None:
                print(f"  {a['label']:<25s}  ERROR")
                continue

            hits = data.get("total_hits", 0)
            results = data.get("results", [])
            scores = [f"{r['score']:.3f}" for r in results[:3]]

            print(f"  {a['label']:<25s} {hits:>6d}   {', '.join(scores) if scores else '-'}")

        print()
        for a in ANALYZERS:
            data = run_search(a["index_dir"], query, field=field, limit=1, analyzer=a["name"])
            if data and data.get("results"):
                top = data["results"][0]
                print(f"    [{a['label']}] top-1: {top['title'][:60]}")

    print()


def show_discussion():
    print("=" * 62)
    print("  Diskusi")
    print("=" * 62)
    print()
    print("  Pertanyaan untuk didiskusikan:")
    print()
    print("  1. Kenapa WhitespaceAnalyzer menghasilkan jumlah hit berbeda")
    print("     dari StandardAnalyzer untuk query yang sama?")
    print("     Hint: apa yang terjadi dengan huruf besar/kecil?")
    print()
    print("  2. Kenapa query \"yang dan untuk\" menghasilkan hit berbeda")
    print("     di setiap analyzer?")
    print("     Hint: kata-kata tersebut adalah stopword.")
    print()
    print("  3. Hubungkan dengan praktikum preprocessing:")
    print("     - StandardAnalyzer ≈ tokenisasi + lowercase + stopword removal")
    print("     - WhitespaceAnalyzer ≈ tokenisasi saja (split spasi)")
    print("     - Custom Indonesian ≈ tokenisasi + lowercase + stopword Indonesia")
    print()
    print("  4. Mana yang paling cocok untuk dokumen berita bahasa Indonesia? Kenapa?")
    print()


def show_summary():
    print("=" * 62)
    print("  Ringkasan Peta Konsep Lengkap")
    print("=" * 62)
    print()
    print("  ┌─────────────────────────────────┬───────────────────────────────┐")
    print("  │ Praktikum sebelumnya            │ Komponen Apache Lucene        │")
    print("  ├─────────────────────────────────┼───────────────────────────────┤")
    print("  │ Tokenisasi, stopword, stemming  │ Analyzer                      │")
    print("  │ Inverted index                  │ IndexWriter + Document/Field  │")
    print("  │ TF-IDF scoring                  │ ClassicSimilarity             │")
    print("  │ Query → ranking                 │ QueryParser + IndexSearcher   │")
    print("  │ BM25 (nanti)                    │ BM25Similarity (default)      │")
    print("  └─────────────────────────────────┴───────────────────────────────┘")
    print()


def show_tugas():
    print("=" * 62)
    print("  Tugas (dikerjakan di rumah)")
    print("=" * 62)
    print()
    print("  1. Bandingkan ranking Lucene (ClassicSimilarity/TF-IDF) dengan")
    print("     implementasi TF-IDF + cosine similarity manual kalian untuk")
    print("     3–5 query. Analisis perbedaannya dan jelaskan penyebabnya.")
    print()
    print("  2. Ganti similarity ke BM25Similarity, jalankan query yang sama,")
    print("     bandingkan hasilnya dengan TF-IDF. Gunakan --explain untuk")
    print("     melihat perbedaan perhitungan skor.")
    print("     Contoh:")
    print("       python 04_searching.py \"pemerintah\" --explain")
    print("     (ubah similarity di 03_indexing.py dan 04_searching.py)")
    print()
    print("  3. (Opsional) Perbaiki custom analyzer bahasa Indonesia:")
    print("     tambahkan lebih banyak stopword, atau tambahkan stemmer.")
    print()


def show_web_interface():
    print("=" * 62)
    print("  Web Interface")
    print("=" * 62)
    print()
    print("  Untuk menjalankan search server dengan web interface:")
    print()
    print("    java -cp \"java/lib/*:java\" SearchServer --index index")
    print()
    print("  Lalu buka http://localhost:8080 di browser.")
    print("  Ketik query di kotak pencarian, lihat hasilnya.")
    print("  Centang 'Tampilkan explain' untuk melihat breakdown skor.")
    print()


def cleanup_experiment_indexes():
    for a in ANALYZERS:
        idx = a["index_dir"]
        if idx.exists():
            shutil.rmtree(idx)


if __name__ == "__main__":
    print_header()
    check_prerequisites()
    build_indexes()
    compare_queries()
    show_discussion()
    show_summary()
    show_tugas()
    show_web_interface()

    try:
        answer = input("  Hapus index eksperimen (index_standard, index_whitespace, index_indonesian)? (y/n): ").strip().lower()
        if answer in ("y", "yes"):
            cleanup_experiment_indexes()
            print("  Index eksperimen dihapus.")
    except (EOFError, KeyboardInterrupt):
        cleanup_experiment_indexes()
    print()
