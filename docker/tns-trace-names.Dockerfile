# Rebuilds TNS binaries with clearer Jaeger/OTel service names for Tempo (upstream uses "lb", "app", "db").
# Matches commit used previously: grafana/tns:47b160f. Binaries are linux/amd64 to match compose `platform`.
ARG TNS_REF=47b160f

FROM golang:1.23-bookworm AS src
ARG TNS_REF
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
  && rm -rf /var/lib/apt/lists/*
WORKDIR /src
RUN git clone https://github.com/grafana/tns.git . && git checkout "${TNS_REF}"

FROM src AS build-loadgen
RUN sed -i 's/tracing.NewFromEnv("lb")/tracing.NewFromEnv("tns-loadgen")/' loadgen/main.go \
  && CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o /out/loadgen ./loadgen

FROM src AS build-app
RUN sed -i 's/tracing.NewFromEnv("app")/tracing.NewFromEnv("tns-app")/' app/main.go \
  && CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o /out/app ./app

FROM src AS build-db
RUN sed -i 's/tracing.NewFromEnv("db")/tracing.NewFromEnv("tns-db")/' db/main.go \
  && CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o /out/db ./db

FROM alpine:3.19 AS tns-loadgen
COPY --from=build-loadgen /out/loadgen /loadgen
COPY --from=src /src/loadgen/stories.json /stories.json
EXPOSE 80
ENTRYPOINT ["/loadgen"]

FROM alpine:3.19 AS tns-app
COPY --from=build-app /out/app /app
COPY --from=src /src/app/index.html.tmpl /index.html.tmpl
EXPOSE 80
ENTRYPOINT ["/app"]

FROM alpine:3.19 AS tns-db
COPY --from=build-db /out/db /db
EXPOSE 80
ENTRYPOINT ["/db"]
