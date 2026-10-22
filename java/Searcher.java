import java.io.*;
import java.nio.file.*;

import com.google.gson.*;

import org.apache.lucene.analysis.*;
import org.apache.lucene.document.*;
import org.apache.lucene.index.*;
import org.apache.lucene.queryparser.classic.*;
import org.apache.lucene.search.*;
import org.apache.lucene.search.similarities.*;
import org.apache.lucene.store.*;

public class Searcher {

    public static void main(String[] args) throws Exception {
        String indexPath = "index";
        String queryStr = null;
        String field = "body";
        String similarityType = "classic";
        String analyzerType = "standard";
        int limit = 10;
        boolean explain = false;

        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--index":      indexPath = args[++i]; break;
                case "--query":      queryStr = args[++i]; break;
                case "--field":      field = args[++i]; break;
                case "--similarity": similarityType = args[++i]; break;
                case "--analyzer":   analyzerType = args[++i]; break;
                case "--limit":      limit = Integer.parseInt(args[++i]); break;
                case "--explain":    explain = true; break;
                default:
                    if (queryStr == null) queryStr = args[i];
            }
        }

        if (queryStr == null || queryStr.isEmpty()) {
            System.err.println("Usage: java Searcher <query> [--index path] [--field body|title] [--similarity classic|bm25] [--analyzer standard|whitespace|indonesian] [--limit N] [--explain]");
            System.exit(1);
        }

        Similarity similarity = AnalyzerUtil.buildSimilarity(similarityType);
        Analyzer analyzer = AnalyzerUtil.buildAnalyzer(analyzerType, null);

        try (Directory dir = FSDirectory.open(Path.of(indexPath));
             DirectoryReader reader = DirectoryReader.open(dir)) {

            IndexSearcher searcher = new IndexSearcher(reader);
            searcher.setSimilarity(similarity);

            QueryParser parser = new QueryParser(field, analyzer);
            Query query = parser.parse(queryStr);

            long startTime = System.currentTimeMillis();
            TopDocs topDocs = searcher.search(query, limit);
            long elapsed = System.currentTimeMillis() - startTime;

            JsonObject output = new JsonObject();
            output.addProperty("query", queryStr);
            output.addProperty("field", field);
            output.addProperty("similarity", similarityType);
            output.addProperty("analyzer", analyzerType);
            output.addProperty("total_hits", topDocs.totalHits.value);
            output.addProperty("elapsed_ms", elapsed);

            JsonArray results = new JsonArray();
            for (ScoreDoc scoreDoc : topDocs.scoreDocs) {
                Document doc = searcher.storedFields().document(scoreDoc.doc);
                JsonObject item = new JsonObject();
                item.addProperty("rank", results.size() + 1);
                item.addProperty("score", scoreDoc.score);
                item.addProperty("id", doc.get("id"));
                item.addProperty("title", doc.get("title"));
                item.addProperty("url", doc.get("url"));

                String body = doc.get("body");
                if (body != null && body.length() > 200) {
                    body = body.substring(0, 200) + "...";
                }
                item.addProperty("snippet", body);

                if (explain) {
                    Explanation exp = searcher.explain(query, scoreDoc.doc);
                    item.addProperty("explain", exp.toString());
                }

                results.add(item);
            }

            output.add("results", results);
            System.out.println(new GsonBuilder().setPrettyPrinting().create().toJson(output));
        }
    }
}
