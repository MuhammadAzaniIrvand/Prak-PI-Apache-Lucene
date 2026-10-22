"""
04_searching.py — Pencarian dan Explain skor TF-IDF

Skrip ini menjalankan Searcher.java untuk mencari dokumen di index Lucene
dan menampilkan breakdown skor TF-IDF menggunakan explain().

Jalankan:
    python 04_searching.py                        # mode interaktif
    python 04_searching.py "pemerintah"            # satu query
    python 04_searching.py "pemerintah" --explain  # dengan explain

Prasyarat:
    python 03_indexing.py  (sudah dijalankan)
"""

import json
import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
JAVA_DIR = BASE_DIR / "java"
LIB_DIR = JAVA_DIR / "lib"
INDEX_DIR = BASE_DIR / "index"

CLASSPATH = str(LIB_DIR / "*") + os.pathsep + str(JAVA_DIR)


def print_header():
    print()
    print("=" * 62)
    print("  Tahap 3 — Searching: Query dan Ranking")
    print("=" * 62)
    print()
    print("  Peta konsep:")
    print("  ┌─────────────────────────────────┬───────────────────────────────┐")
    print("  │ Praktikum sebelumnya            │ Komponen Lucene               │")
    print("  ├─────────────────────────────────┼───────────────────────────────┤")
    print("  │ TF-IDF scoring                  │ ClassicSimilarity             │")
    print("  │ Query → ranking dokumen         │ QueryParser + IndexSearcher   │")
    print("  └─────────────────────────────────┴───────────────────────────────┘")
    print()


def check_prerequisites():
    if not INDEX_DIR.exists() or not list(INDEX_DIR.iterdir()):
        print("  ERROR: Index belum dibuat. Jalankan dulu:")
        print("    python 03_indexing.py")
        sys.exit(1)


def run_search(query, field="body", limit=10, explain=False, similarity="classic"):
    cmd = [
        "java", "-cp", CLASSPATH, "Searcher",
        "--index", str(INDEX_DIR),
        "--query", query,
        "--field", field,
        "--limit", str(limit),
        "--similarity", similarity,
    ]
    if explain:
        cmd.append("--explain")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  ERROR: {result.stderr.strip()}")
        return None

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  ERROR parsing output: {result.stdout[:200]}")
        return None


def display_results(data, show_explain=False):
    print(f"  Query      : {data['query']}")
    print(f"  Field      : {data['field']}")
    print(f"  Similarity : {data['similarity']}")
    print(f"  Total hits : {data['total_hits']}")
    print(f"  Waktu      : {data['elapsed_ms']} ms")
    print()

    results = data.get("results", [])
    if not results:
        print("  Tidak ada hasil ditemukan.")
        return

    for r in results:
        print(f"  #{r['rank']}  skor: {r['score']:.4f}")
        print(f"      {r['title']}")

        snippet = r.get("snippet", "")
        if snippet and len(snippet) > 100:
            snippet = snippet[:100] + "..."
        print(f"      {snippet}")

        if show_explain and r.get("explain"):
            print()
            print("      --- Explain (breakdown skor TF-IDF) ---")
            for line in r["explain"].split("\n"):
                print(f"      {line}")
            print("      --- end explain ---")

        print()


def run_demo_queries():
    demo_queries = [
        ("pemerintah", "body"),
        ("pertandingan sepak bola", "body"),
        ("pendidikan", "title"),
    ]

    for query, field in demo_queries:
        print("-" * 62)
        data = run_search(query, field=field)
        if data:
            display_results(data)
        print()

    print("=" * 62)
    print("  Explain: Rincian Perhitungan Skor")
    print("=" * 62)
    print()
    print("  Berikut adalah breakdown skor TF-IDF dari Lucene untuk query 'pemerintah'.")
    print("  Perhatikan komponen: tf (term frequency), idf (inverse document frequency),")
    print("  dan fieldNorm (normalisasi panjang dokumen).")
    print()

    data = run_search("pemerintah", explain=True, limit=3)
    if data:
        display_results(data, show_explain=True)

    print("  Penjelasan komponen explain:")
    print("    tf(freq=N)    : berapa kali term muncul di dokumen ini")
    print("    idf(docFreq=N): semakin jarang term muncul di seluruh koleksi, semakin tinggi")
    print("    fieldNorm     : normalisasi berdasarkan panjang field (dokumen pendek → bobot lebih tinggi)")
    print()


def interactive_mode():
    print("  Mode interaktif. Ketik query, atau perintah khusus:")
    print("    :explain <query>  — tampilkan breakdown skor")
    print("    :title <query>    — cari di field title")
    print("    :limit N          — ubah jumlah hasil (default: 10)")
    print("    :quit             — keluar")
    print()

    limit = 10

    while True:
        try:
            raw = input("  query> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not raw:
            continue
        if raw == ":quit":
            break

        if raw.startswith(":limit "):
            try:
                limit = int(raw.split()[1])
                print(f"  Limit diubah ke {limit}")
            except ValueError:
                print("  Gunakan: :limit N")
            continue

        explain = False
        field = "body"

        if raw.startswith(":explain "):
            explain = True
            raw = raw[len(":explain "):]
        if raw.startswith(":title "):
            field = "title"
            raw = raw[len(":title "):]

        data = run_search(raw, field=field, limit=limit, explain=explain)
        if data:
            display_results(data, show_explain=explain)


def show_next_step():
    print("  Lanjut ke:")
    print("    python 05_eksperimen_analyzer.py")
    print()


if __name__ == "__main__":
    print_header()
    check_prerequisites()

    args = sys.argv[1:]

    if not args:
        run_demo_queries()
        show_next_step()

        answer = input("  Masuk mode interaktif? (y/n): ").strip().lower()
        if answer in ("y", "yes"):
            interactive_mode()
    else:
        query = args[0]
        explain = "--explain" in args
        field = "body"
        limit = 10

        for i, a in enumerate(args):
            if a == "--field" and i + 1 < len(args):
                field = args[i + 1]
            if a == "--limit" and i + 1 < len(args):
                limit = int(args[i + 1])

        data = run_search(query, field=field, limit=limit, explain=explain)
        if data:
            display_results(data, show_explain=explain)
