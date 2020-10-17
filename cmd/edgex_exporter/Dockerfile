FROM quay.io/prometheus/busybox:latest

COPY edgex_exporter /bin/edgex_exporter

EXPOSE 9410
ENTRYPOINT ["/bin/edgex_exporter"]
