FROM rust:1.90-bookworm AS builder
WORKDIR /source
COPY rust ./rust
RUN --mount=type=cache,target=/usr/local/cargo/registry \
    --mount=type=cache,target=/source/rust/target \
    cargo build --locked --release --manifest-path rust/Cargo.toml -p continuum-worker \
    && cp rust/target/release/continuum-worker /tmp/continuum-worker

FROM debian:bookworm-slim
RUN useradd --system --uid 10001 continuum
COPY --from=builder /tmp/continuum-worker /usr/local/bin/continuum-worker
USER continuum
EXPOSE 8391
ENTRYPOINT ["/usr/local/bin/continuum-worker"]
