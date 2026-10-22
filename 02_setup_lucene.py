"""
02_setup_lucene.py — Persiapan lingkungan Lucene

Skrip ini:
1. Download JAR Apache Lucene dan Gson dari Maven Central
2. Compile semua file Java (Indexer, Searcher, SearchServer)

Jalankan sekali sebelum skrip-skrip berikutnya:
    python 02_setup_lucene.py
"""

import subprocess
import sys
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
JAVA_DIR = BASE_DIR / "java"
LIB_DIR = JAVA_DIR / "lib"

LUCENE_VERSION = "9.12.0"
GSON_VERSION = "2.11.0"

JARS = [
    {
        "name": f"lucene-core-{LUCENE_VERSION}.jar",
        "url": f"https://repo1.maven.org/maven2/org/apache/lucene/lucene-core/{LUCENE_VERSION}/lucene-core-{LUCENE_VERSION}.jar",
    },
    {
        "name": f"lucene-queryparser-{LUCENE_VERSION}.jar",
        "url": f"https://repo1.maven.org/maven2/org/apache/lucene/lucene-queryparser/{LUCENE_VERSION}/lucene-queryparser-{LUCENE_VERSION}.jar",
    },
    {
        "name": f"lucene-analysis-common-{LUCENE_VERSION}.jar",
        "url": f"https://repo1.maven.org/maven2/org/apache/lucene/lucene-analysis-common/{LUCENE_VERSION}/lucene-analysis-common-{LUCENE_VERSION}.jar",
    },
    {
        "name": f"lucene-sandbox-{LUCENE_VERSION}.jar",
        "url": f"https://repo1.maven.org/maven2/org/apache/lucene/lucene-sandbox/{LUCENE_VERSION}/lucene-sandbox-{LUCENE_VERSION}.jar",
    },
    {
        "name": f"gson-{GSON_VERSION}.jar",
        "url": f"https://repo1.maven.org/maven2/com/google/code/gson/gson/{GSON_VERSION}/gson-{GSON_VERSION}.jar",
    },
]

JAVA_FILES = ["AnalyzerUtil.java", "Indexer.java", "Searcher.java", "SearchServer.java"]


def download_jars():
    LIB_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 60)
    print("  Download JAR files")
    print("=" * 60)

    for jar in JARS:
        dest = LIB_DIR / jar["name"]
        if dest.exists():
            print(f"  [ada]  {jar['name']}")
            continue

        print(f"  [download] {jar['name']} ...")
        try:
            urllib.request.urlretrieve(jar["url"], dest)
            size_mb = dest.stat().st_size / (1024 * 1024)
            print(f"           OK ({size_mb:.1f} MB)")
        except Exception as e:
            print(f"           GAGAL: {e}")
            sys.exit(1)

    print()


def compile_java():
    print("=" * 60)
    print("  Compile file Java")
    print("=" * 60)

    classpath = str(LIB_DIR / "*")
    java_files = [str(JAVA_DIR / f) for f in JAVA_FILES]

    cmd = [
        "javac",
        "-cp", classpath,
        "-d", str(JAVA_DIR),
        "--release", "21",
    ] + java_files

    print(f"  javac {' '.join(JAVA_FILES)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("  GAGAL kompilasi:\n")
        print(result.stderr)
        sys.exit(1)

    print("  OK — semua file berhasil dikompilasi")
    print()


def verify():
    print("=" * 60)
    print("  Verifikasi")
    print("=" * 60)

    jar_count = len(list(LIB_DIR.glob("*.jar")))
    class_files = list(JAVA_DIR.glob("*.class"))

    print(f"  JAR files   : {jar_count}")
    print(f"  Class files : {len(class_files)}")
    for cf in sorted(class_files):
        print(f"    {cf.name}")

    print()
    print("  Semua siap. Lanjut ke:")
    print("    python 03_indexing.py")
    print()


if __name__ == "__main__":
    download_jars()
    compile_java()
    verify()
