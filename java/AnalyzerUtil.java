import java.io.*;
import java.nio.file.*;
import java.util.*;

import org.apache.lucene.analysis.*;
import org.apache.lucene.analysis.core.*;
import org.apache.lucene.analysis.standard.*;
import org.apache.lucene.search.similarities.*;

public class AnalyzerUtil {

    public static final List<String> STOPWORDS_ID = Arrays.asList(
        "yang", "dan", "di", "ini", "itu", "dengan", "untuk", "pada",
        "adalah", "dari", "dalam", "tidak", "akan", "juga", "atau",
        "ke", "oleh", "saya", "kami", "kita", "mereka", "dia", "ia",
        "telah", "sudah", "bisa", "ada", "saat", "secara", "lebih",
        "antara", "bahwa", "sebagai", "setelah", "masih", "tersebut",
        "kata", "namun", "hingga", "karena", "seperti", "harus",
        "serta", "menjadi", "dapat", "sedang", "maupun", "agar",
        "beberapa", "ketika", "lalu", "pun", "meski", "tetapi"
    );

    public static Analyzer buildAnalyzer(String type, String stopwordsFile) throws Exception {
        switch (type == null ? "standard" : type.toLowerCase()) {
            case "whitespace":
                return new WhitespaceAnalyzer();

            case "indonesian":
                List<String> words = new ArrayList<>(STOPWORDS_ID);
                if (stopwordsFile != null) {
                    words = Files.readAllLines(Path.of(stopwordsFile));
                }
                CharArraySet stopSet = new CharArraySet(words, true);
                
                return new Analyzer() {
                    @Override
                    protected TokenStreamComponents createComponents(String fieldName) {
                        Tokenizer source = new StandardTokenizer();
                        TokenStream result = new org.apache.lucene.analysis.core.LowerCaseFilter(source);
                        result = new org.apache.lucene.analysis.core.StopFilter(result, stopSet);
                        return new TokenStreamComponents(source, result);
                    }
                };

            case "standard":
            default:
                return new StandardAnalyzer();
        }
    }

    public static Similarity buildSimilarity(String type) {
        switch (type == null ? "classic" : type.toLowerCase()) {
            case "bm25":  return new BM25Similarity();
            case "classic":
            default:      return new ClassicSimilarity();
        }
    }
}
