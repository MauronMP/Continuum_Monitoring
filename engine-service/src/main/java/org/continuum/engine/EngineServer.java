package org.continuum.engine;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Executors;

public final class EngineServer {
    private static final ObjectMapper JSON = new ObjectMapper();
    private final EngineAdapter adapter;

    private EngineServer(EngineAdapter adapter) {
        this.adapter = adapter;
    }

    public static void main(String[] args) throws Exception {
        String engine = System.getenv().getOrDefault(
            "CONTINUUM_ENGINE",
            "jena"
        );
        int port = Integer.parseInt(
            System.getenv().getOrDefault("CONTINUUM_PORT", "8080")
        );
        EngineAdapter adapter = switch (engine) {
            case "jena" -> new JenaAdapter();
            case "rdf4j" -> new Rdf4jAdapter();
            default -> throw new IllegalArgumentException(
                "Unknown Java engine: " + engine
            );
        };
        EngineServer application = new EngineServer(adapter);
        HttpServer server = HttpServer.create(
            new InetSocketAddress("0.0.0.0", port),
            0
        );
        server.createContext("/health", application::health);
        server.createContext("/prepare", application::prepare);
        server.createContext("/queries", application::queries);
        server.setExecutor(Executors.newFixedThreadPool(4));
        Runtime.getRuntime().addShutdownHook(
            new Thread(() -> {
                try {
                    adapter.close();
                } catch (Exception ignored) {
                    // Best-effort shutdown.
                }
            })
        );
        server.start();
        System.out.printf(
            "[java-engine] engine=%s inference=%s port=%d%n",
            adapter.name(),
            adapter.inferenceProfile(),
            port
        );
    }

    private void health(HttpExchange exchange) throws IOException {
        if (!"GET".equals(exchange.getRequestMethod())) {
            send(exchange, 405, Map.of("error", "method not allowed"));
            return;
        }
        send(
            exchange,
            200,
            Map.of(
                "status",
                "ok",
                "engine",
                adapter.name(),
                "version",
                adapter.version(),
                "inference_profile",
                adapter.inferenceProfile()
            )
        );
    }

    private synchronized void prepare(HttpExchange exchange)
        throws IOException {
        if (!"POST".equals(exchange.getRequestMethod())) {
            send(exchange, 405, Map.of("error", "method not allowed"));
            return;
        }
        try {
            JsonNode payload = JSON.readTree(exchange.getRequestBody());
            byte[] ntriples = payload
                .get("data_ntriples")
                .asText()
                .getBytes(StandardCharsets.UTF_8);
            send(exchange, 200, adapter.prepare(ntriples));
        } catch (Exception error) {
            send(
                exchange,
                500,
                Map.of(
                    "error",
                    error.getClass().getSimpleName()
                        + ": "
                        + error.getMessage()
                )
            );
        }
    }

    private synchronized void queries(HttpExchange exchange)
        throws IOException {
        if (!"POST".equals(exchange.getRequestMethod())) {
            send(exchange, 405, Map.of("error", "method not allowed"));
            return;
        }
        try {
            JsonNode payload = JSON.readTree(exchange.getRequestBody());
            List<EngineAdapter.QueryInput> queries = JSON.convertValue(
                payload.get("queries"),
                new TypeReference<>() {}
            );
            long started = System.nanoTime();
            List<EngineAdapter.QueryMeasurement> measurements =
                adapter.execute(queries);
            Map<String, Object> response = new LinkedHashMap<>();
            response.put("engine", adapter.name());
            response.put(
                "inference_profile",
                adapter.inferenceProfile()
            );
            response.put(
                "query_wall_ms",
                (System.nanoTime() - started) / 1_000_000.0
            );
            response.put("measurements", measurements);
            send(exchange, 200, response);
        } catch (Exception error) {
            send(
                exchange,
                500,
                Map.of(
                    "error",
                    error.getClass().getSimpleName()
                        + ": "
                        + error.getMessage()
                )
            );
        }
    }

    private static void send(
        HttpExchange exchange,
        int status,
        Object payload
    ) throws IOException {
        byte[] data = JSON
            .writeValueAsString(payload)
            .getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().set(
            "Content-Type",
            "application/json; charset=utf-8"
        );
        exchange.sendResponseHeaders(status, data.length);
        exchange.getResponseBody().write(data);
        exchange.close();
    }
}
