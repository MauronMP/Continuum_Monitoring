package org.continuum.engine;

import java.io.ByteArrayInputStream;
import java.util.ArrayList;
import java.util.List;
import org.apache.jena.query.Query;
import org.apache.jena.query.QueryExecution;
import org.apache.jena.query.QueryExecutionFactory;
import org.apache.jena.query.QueryFactory;
import org.apache.jena.query.ResultSet;
import org.apache.jena.rdf.model.InfModel;
import org.apache.jena.rdf.model.Model;
import org.apache.jena.rdf.model.ModelFactory;
import org.apache.jena.reasoner.ReasonerRegistry;
import org.apache.jena.riot.Lang;
import org.apache.jena.riot.RDFDataMgr;

final class JenaAdapter implements EngineAdapter {
    private InfModel model;

    @Override
    public String name() {
        return "jena";
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
    public PrepareResult prepare(byte[] ntriples) {
        close();
        long allStarted = System.nanoTime();
        Model base = ModelFactory.createDefaultModel();
        long loadStarted = System.nanoTime();
        RDFDataMgr.read(
            base,
            new ByteArrayInputStream(ntriples),
            Lang.NTRIPLES
        );
        double loadMs = elapsedMs(loadStarted);
        long inputTriples = base.size();

        long reasoningStarted = System.nanoTime();
        model = ModelFactory.createInfModel(
            ReasonerRegistry.getRDFSReasoner(),
            base
        );
        model.prepare();
        long outputTriples = model.size();
        double reasoningMs = elapsedMs(reasoningStarted);
        return new PrepareResult(
            name(),
            inferenceProfile(),
            inputTriples,
            outputTriples,
            outputTriples - inputTriples,
            loadMs,
            reasoningMs,
            elapsedMs(allStarted)
        );
    }

    @Override
    public List<QueryMeasurement> execute(List<QueryInput> queries) {
        if (model == null) {
            throw new IllegalStateException("Jena engine is not prepared");
        }
        List<QueryMeasurement> output = new ArrayList<>();
        for (QueryInput input : queries) {
            long started = System.nanoTime();
            Query query = QueryFactory.create(input.text());
            long count;
            Boolean ask = null;
            try (QueryExecution execution =
                     QueryExecutionFactory.create(query, model)) {
                if (query.isAskType()) {
                    ask = execution.execAsk();
                    count = ask ? 1 : 0;
                } else {
                    ResultSet results = execution.execSelect();
                    count = 0;
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
        return output;
    }

    @Override
    public void close() {
        if (model != null) {
            model.close();
            model = null;
        }
    }

    private static double elapsedMs(long started) {
        return (System.nanoTime() - started) / 1_000_000.0;
    }
}
