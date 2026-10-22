import java.io.*;
import java.nio.file.*;
import java.util.*;

import com.google.gson.*;
import com.google.gson.reflect.*;

import org.apache.lucene.analysis.*;
import org.apache.lucene.document.*;
import org.apache.lucene.index.*;
import org.apache.lucene.search.similarities.*;
import org.apache.lucene.store.*;

public class Indexer {

    public static void main(String[] args) throws Exception {
        String jsonPath = "data/dokumen_antara.json";
        String indexPath = "index";
        String similarityType = "classic";
        String analyzerType = "standard";
        String stopwordsFile = null;

        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--json":       jsonPath = args[++i]; break;
                case "--index":      indexPath = args[++i]; break;
                case "--similarity": similarityType = args[++i]; break;
                case "--analyzer":   analyzerType = args[++i]; break;
                case "--stopwords":  stopwordsFile = args[++i]; break;
            }
        }

        String jsonContent = Files.readString(Path.of(jsonPath));
        List<Map<String, String>> documents = new Gson().fromJson(
            jsonContent, new TypeToken<List<Map<String, String>>>(){}.getType()
        );

        Analyzer analyzer = AnalyzerUtil.buildAnalyzer(analyzerType, stopwordsFile);
        Similarity similarity = AnalyzerUtil.buildSimilarity(similarityType);

        IndexWriterConfig config = new IndexWriterConfig(analyzer);
        config.setSimilarity(similarity);
        config.setOpenMode(IndexWriterConfig.OpenMode.CREATE);

        Path idxPath = Path.of(indexPath);
        long startTime = System.currentTimeMillis();

        try (Directory dir = FSDirectory.open(idxPath);
             IndexWriter writer = new IndexWriter(dir, config)) {

            for (Map<String, String> doc : documents) {
                Document luceneDoc = new Document();
                luceneDoc.add(new StringField("id", doc.getOrDefault("id", ""), Field.Store.YES));
                luceneDoc.add(new TextField("title", doc.getOrDefault("title", ""), Field.Store.YES));
                luceneDoc.add(new TextField("body", doc.getOrDefault("body", ""), Field.Store.YES));
                luceneDoc.add(new StoredField("url", doc.getOrDefault("url", "")));
                luceneDoc.add(new StoredField("published_at", doc.getOrDefault("published_at", "")));
                writer.addDocument(luceneDoc);
            }

            writer.commit();
        }

        long elapsed = System.currentTimeMillis() - startTime;

        long indexSize = Files.walk(idxPath)
            .filter(Files::isRegularFile)
            .mapToLong(p -> { try { return Files.size(p); } catch (IOException e) { return 0; } })
            .sum();

        JsonObject result = new JsonObject();
        result.addProperty("status", "ok");
        result.addProperty("documents_indexed", documents.size());
        result.addProperty("index_path", idxPath.toAbsolutePath().toString());
        result.addProperty("index_size_bytes", indexSize);
        result.addProperty("elapsed_ms", elapsed);
        result.addProperty("analyzer", analyzerType);
        result.addProperty("similarity", similarityType);

        System.out.println(new Gson().toJson(result));
    }
}
