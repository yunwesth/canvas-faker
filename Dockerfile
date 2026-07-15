# syntax=docker/dockerfile:1

# ---- Stage 1: build the wheel ----
FROM python:3.12-slim AS builder

WORKDIR /build

# Build tooling for producing a wheel
RUN pip install --no-cache-dir build

# Copy only what's needed to build the package
COPY pyproject.toml README.md ./
COPY canvas_faker ./canvas_faker
COPY tests ./tests

# Produce a wheel in /build/dist
RUN python -m build --wheel --outdir /build/dist


# ---- Stage 2: slim runtime ----
FROM python:3.12-slim AS runtime

# Non-root user for safety
RUN useradd --create-home --uid 1000 canvas

# Install the built wheel (pulls in faker), then discard build artifacts
COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl

# /data is the mount point for generated databases
RUN mkdir -p /data && chown canvas:canvas /data
VOLUME ["/data"]

USER canvas
WORKDIR /data

# Default: write the dataset into the mounted volume.
# Override any flag at `docker run` time, e.g.:
#   docker run --rm -v $PWD/out:/data canvas-faker --scale medium --seed 99
ENTRYPOINT ["canvas-faker"]
CMD ["--out", "/data/cd2.db", "--scale", "small", "--seed", "42"]
