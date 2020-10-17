# EdgeX Foundry Exporter for Prometheus

Export EdgeX Foundry stats to Prometheus.

To run it:

```bash
$ go get github.com/ohmk/edgex_exporter
$ cd $GOPATH/src/github.com/ohmk/edgex_exporter
$ make
$ ./edgex_exporter [flags]
$ curl http://localhost:9410/metrics
```

## Exported Metrics

| Metric | Meaning | Labels |
| ------ | ------- | ------ |
| edgex_requests_total | Total of edgex_exporter scrapes. | |
| edgex_scrape_duration_seconds | Duration of edgex_exporter scrapes. | |
| edgex_total_devices | Total number devices connected to EdgeX Foundry. | |
| edgex_total_events | Total number of events. | |
| edgex_total_readings | Total number of readings. | |
| edgex_total_services | Total number of services connected to Consul | |


## Using Docker

TO run the EdgeX exporter as a Docker container:

```bash
$ cd $GOPATH/src/github.com/ohmk/edgex_exporter
$ make docker
$ docker run --rm -it -p 9410:9410 edgex-exporter:master \
    --coredata.server=http://172.17.0.1:48080/api/v1 \
    --metadata.server=http://172.17.0.1:48081/api/v1 \
    --consul.server=http://172.17.0.1:8500
```

## Using Docker Compose

To run the EdgeX Exporter and Prometheus as Docker containers:

```bash
$ cd $GOPATH/src/github.com/ohmk/edgex_exporter/examples
$ ls
docker-compose.yml  prometheus.yml
$ docker-compose up
```

You can access to http://localhost:9090.