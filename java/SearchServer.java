import java.io.*;
import java.net.*;
import java.nio.file.*;

import com.google.gson.*;
import com.sun.net.httpserver.*;

import org.apache.lucene.analysis.*;
import org.apache.lucene.document.*;
import org.apache.lucene.index.*;
import org.apache.lucene.queryparser.classic.*;
import org.apache.lucene.search.*;
import org.apache.lucene.search.similarities.*;
import org.apache.lucene.store.*;

public class SearchServer {

    private static DirectoryReader reader;
    private static IndexSearcher searcher;
    private static Analyzer analyzer;
    private static String webDir = "web";

    public static void main(String[] args) throws Exception {
        String indexPath = "index";
        String similarityType = "classic";
        String analyzerType = "standard";
        int port = 8080;

        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--index":      indexPath = args[++i]; break;
                case "--similarity": similarityType = args[++i]; break;
                case "--analyzer":   analyzerType = args[++i]; break;
                case "--port":       port = Integer.parseInt(args[++i]); break;
                case "--web":        webDir = args[++i]; break;
            }
        }

        Similarity similarity = AnalyzerUtil.buildSimilarity(similarityType);
        analyzer = AnalyzerUtil.buildAnalyzer(analyzerType, null);

        Directory dir = FSDirectory.open(Path.of(indexPath));
        reader = DirectoryReader.open(dir);
        searcher = new IndexSearcher(reader);
        searcher.setSimilarity(similarity);

        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);
        server.createContext("/", SearchServer::handleStatic);
        server.createContext("/search", SearchServer::handleSearch);
        server.setExecutor(null);
        server.start();

        System.out.println("Search server running at http://localhost:" + port);
        System.out.println("Index: " + Path.of(indexPath).toAbsolutePath());
        System.out.println("Similarity: " + similarityType);
        System.out.println("Analyzer: " + analyzerType);
        System.out.println("Press Ctrl+C to stop.");
    }

    private static void handleSearch(HttpExchange exchange) throws IOException {
        if (!"GET".equals(exchange.getRequestMethod())) {
            exchange.sendResponseHeaders(405, -1);
            return;
        }

        exchange.getResponseHeaders().add("Content-Type", "application/json; charset=utf-8");
        exchange.getResponseHeaders().add("Access-Control-Allow-Origin", "*");

        String rawQuery = exchange.getRequestURI().getRawQuery();
        String queryStr = "";
        int limit = 10;
        boolean explain = false;
        String field = "body";

        if (rawQuery != null) {
            for (String param : rawQuery.split("&")) {
                String[] kv = param.split("=", 2);
                if (kv.length == 2) {
                    String key = kv[0];
                    String val = URLDecoder.decode(kv[1], "UTF-8");
                    switch (key) {
                        case "q":       queryStr = val; break;
                        case "limit":
                            try { limit = Integer.parseInt(val); } catch (NumberFormatException ignored) {}
                            break;
                        case "explain": explain = "true".equals(val) || "1".equals(val); break;
                        case "field":   field = val; break;
                    }
                }
            }
        }

        JsonObject output = new JsonObject();

        if (queryStr.isEmpty()) {
            output.addProperty("error", "Parameter 'q' diperlukan. Contoh: /search?q=pemerintah");
            sendJson(exchange, 400, output);
            return;
        }

        try {
            QueryParser parser = new QueryParser(field, analyzer);
            Query query = parser.parse(queryStr);

            long startTime = System.currentTimeMillis();
            TopDocs topDocs = searcher.search(query, limit);
            long elapsed = System.currentTimeMillis() - startTime;

            output.addProperty("query", queryStr);
            output.addProperty("field", field);
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
                if (body != null && body.length() > 300) {
                    body = body.substring(0, 300) + "...";
                }
                item.addProperty("snippet", body);

                if (explain) {
                    Explanation exp = searcher.explain(query, scoreDoc.doc);
                    item.addProperty("explain", exp.toString());
                }

                results.add(item);
            }

            output.add("results", results);
            sendJson(exchange, 200, output);

        } catch (ParseException e) {
            output.addProperty("error", "Query tidak valid: " + e.getMessage());
            sendJson(exchange, 400, output);
        }
    }

    private static void handleStatic(HttpExchange exchange) throws IOException {
        String path = exchange.getRequestURI().getPath();
        if ("/".equals(path)) path = "/index.html";

        Path webRoot = Path.of(webDir).normalize().toAbsolutePath();
        Path filePath = Path.of(webDir, path.substring(1)).normalize().toAbsolutePath();

        if (!filePath.startsWith(webRoot) || !Files.exists(filePath) || !Files.isRegularFile(filePath)) {
            String msg = "404 Not Found";
            exchange.sendResponseHeaders(404, msg.length());
            exchange.getResponseBody().write(msg.getBytes());
            exchange.getResponseBody().close();
            return;
        }

        String contentType = "text/html; charset=utf-8";
        if (path.endsWith(".css")) contentType = "text/css; charset=utf-8";
        if (path.endsWith(".js")) contentType = "application/javascript; charset=utf-8";

        byte[] content = Files.readAllBytes(filePath);
        exchange.getResponseHeaders().add("Content-Type", contentType);
        exchange.sendResponseHeaders(200, content.length);
        exchange.getResponseBody().write(content);
        exchange.getResponseBody().close();
    }

    private static void sendJson(HttpExchange exchange, int code, JsonObject json) throws IOException {
        byte[] body = new Gson().toJson(json).getBytes("UTF-8");
        exchange.sendResponseHeaders(code, body.length);
        exchange.getResponseBody().write(body);
        exchange.getResponseBody().close();
    }
}
