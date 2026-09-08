package org.continuum.engine;

import java.util.List;

interface EngineAdapter extends AutoCloseable {
    record PrepareResult(
        String engine,
        String inference_profile,
        long input_triples,
        long output_triples,
        long inferred_triples,
        double load_ms,
        double reasoning_ms,
        double prepare_ms
    ) {}

    record QueryInput(
        String id,
        String category,
        String tier,
        String kind,
        String text
    ) {}

    record QueryMeasurement(
        String query_id,
        String category,
        String tier,
        double duration_ms,
        long result_count,
        Boolean ask_result
    ) {}

    String name();

    String version();

    String inferenceProfile();

    PrepareResult prepare(byte[] ntriples) throws Exception;

    List<QueryMeasurement> execute(List<QueryInput> queries) throws Exception;

    @Override
    void close() throws Exception;
}
