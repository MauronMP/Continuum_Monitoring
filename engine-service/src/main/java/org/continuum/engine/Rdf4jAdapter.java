package org.continuum.engine;

import java.io.ByteArrayInputStream;
import java.util.ArrayList;
import java.util.List;
import org.eclipse.rdf4j.query.BooleanQuery;
import org.eclipse.rdf4j.query.QueryLanguage;
import org.eclipse.rdf4j.query.TupleQuery;
import org.eclipse.rdf4j.query.TupleQueryResult;
import org.eclipse.rdf4j.repository.RepositoryConnection;
import org.eclipse.rdf4j.repository.sail.SailRepository;
import org.eclipse.rdf4j.rio.RDFFormat;
import org.eclipse.rdf4j.sail.inferencer.fc.SchemaCachingRDFSInferencer;
import org.eclipse.rdf4j.sail.memory.MemoryStore;

final class Rdf4jAdapter implements EngineAdapter {
    private SailRepository repository;

    @Override
    public String name() {
        return "rdf4j";
    }

    @Override
    public String version() {
        return "6.0.0";
    }

    @Override
    public String inferenceProfile() {
        return "rdfs";
    }

    @Override
    public PrepareResult prepare(byte[] ntriples) throws Exception {
        close();
        long allStarted = System.nanoTime();
        repository = new SailRepository(
            new SchemaCachingRDFSInferencer(new MemoryStore())
        );
        repository.init();
        long loadStarted = System.nanoTime();
        long inputTriples;
        long outputTriples;
        try (RepositoryConnection connection = repository.getConnection()) {
            connection.begin();
            connection.add(
                new ByteArrayInputStream(ntriples),
                "urn:continuum:dataset",
                RDFFormat.NTRIPLES
            );
            connection.commit();
            inputTriples = connection
                .getStatements(null, null, null, false)
                .stream()
                .count();
            outputTriples = connection
                .getStatements(null, null, null, true)
                .stream()
                .count();
        }
        double loadAndReasoningMs = elapsedMs(loadStarted);
        return new PrepareResult(
            name(),
            inferenceProfile(),
            inputTriples,
            outputTriples,
            outputTriples - inputTriples,
            0.0,
            loadAndReasoningMs,
            elapsedMs(allStarted)
        );
    }

    @Override
    public List<QueryMeasurement> execute(List<QueryInput> queries) {
        if (repository == null) {
            throw new IllegalStateException("RDF4J engine is not prepared");
        }
        List<QueryMeasurement> output = new ArrayList<>();
        try (RepositoryConnection connection = repository.getConnection()) {
            for (QueryInput input : queries) {
                long started = System.nanoTime();
                long count;
                Boolean ask = null;
                if ("ask".equals(input.kind())) {
                    BooleanQuery query = connection.prepareBooleanQuery(
                        QueryLanguage.SPARQL,
                        input.text()
                    );
                    ask = query.evaluate();
                    count = ask ? 1 : 0;
                } else {
                    TupleQuery query = connection.prepareTupleQuery(
                        QueryLanguage.SPARQL,
                        input.text()
                    );
                    count = 0;
                    try (TupleQueryResult results = query.evaluate()) {
                        while (results.hasNext()) {
                            results.next();
                            count++;
                        }
                    }
                }
                output.add(
                    new QueryMeasurement(
                        input.id(),
                        input.category(),
                        input.tier(),
                        elapsedMs(started),
                        count,
                        ask
                    )
                );
            }
        }
        return output;
    }

    @Override
    public void close() {
        if (repository != null) {
            repository.shutDown();
            repository = null;
        }
    }

    private static double elapsedMs(long started) {
        return (System.nanoTime() - started) / 1_000_000.0;
    }
}
