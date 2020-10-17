package main

import (
	"fmt"
	"net/url"
	"os"

	consul_api "github.com/hashicorp/consul/api"
	"github.com/ohmk/edgex_exporter/api"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/push"
	"github.com/prometheus/common/log"
	"gopkg.in/alecthomas/kingpin.v2"
)

const (
	namespace = "edgex"
)

var (
	pushgatewayUrl = kingpin.Flag(
		"pushgateway.server",
		"HTTP API address of a pushgateway server",
	).Default("http://localhost:9091").String()
	coreDataUrl = kingpin.Flag(
		"coredata.server",
		"HTTP API address of a coredata server",
	).Default("http://localhost:48080/api/v1").String()
	metadataUrl = kingpin.Flag(
		"metadata.server",
		"HTTP API address of a metadata server",
	).Default("http://localhost:48081/api/v1").String()
	consulUrl = kingpin.Flag(
		"consul.server",
		"HTTP API address of a consul server",
	).Default("http://localhost:8500").String()
)

func pushCoreData() error {
	totalEvents := prometheus.NewGauge(prometheus.GaugeOpts{
		Name: fmt.Sprintf("%s_total_events", namespace),
		Help: "Total number of events.",
	})
	totalReadings := prometheus.NewGauge(prometheus.GaugeOpts{
		Name: fmt.Sprintf("%s_total_readings", namespace),
		Help: "Total number of readings",
	})

	client := api.NewCoreDataClient(*coreDataUrl)

	nEvents, err := client.GetEventCount()
	if err != nil {
		return err
	}
	totalEvents.Set(float64(nEvents))

	nReadings, err := client.GetReadingCount()
	if err != nil {
		return err
	}
	totalReadings.Set(float64(nReadings))

	err = push.AddCollectors(
		namespace,
		push.HostnameGroupingKey(),
		*pushgatewayUrl,
		totalEvents,
		totalReadings,
	)
	if err != nil {
		return err
	}

	return nil
}

func pushMetadata() error {
	totalDevices := prometheus.NewGauge(prometheus.GaugeOpts{
		Name: fmt.Sprintf("%s_total_devices", namespace),
		Help: "Total number of devices connected to EdgeX Foundry.",
	})

	client := api.NewMetadataClient(*metadataUrl)

	nDevices, err := client.GetDeviceCount()
	if err != nil {
		return err
	}
	totalDevices.Set(float64(nDevices))

	err = push.AddCollectors(
		namespace,
		push.HostnameGroupingKey(),
		*pushgatewayUrl,
		totalDevices,
	)
	if err != nil {
		return err
	}

	return nil
}

func pushConsul() error {
	totalServices := prometheus.NewGauge(prometheus.GaugeOpts{
		Name: fmt.Sprintf("%s_total_services", namespace),
		Help: "Total number of services connected to Consul",
	})

	u, err := url.Parse(*consulUrl)
	if err != nil {
		return err
	}

	config := consul_api.DefaultConfig()
	config.Address = u.Host
	config.Scheme = u.Scheme

	client, err := consul_api.NewClient(config)
	if err != nil {
		return err
	}

	nServices, _, err := client.Catalog().Services(&consul_api.QueryOptions{}) //TODO
	if err != nil {
		return err
	}
	totalServices.Set(float64(len(nServices)))

	err = push.AddCollectors(
		namespace,
		push.HostnameGroupingKey(),
		*pushgatewayUrl,
		totalServices,
	)
	if err != nil {
		return err
	}

	return nil
}

func pushMetrics() error {
	// TODO: use goroutine
	err := pushCoreData()
	if err != nil {
		return err
	}

	err = pushMetadata()
	if err != nil {
		return err
	}

	err = pushConsul()
	if err != nil {
		return err
	}

	return nil
}

func main() {
	log.AddFlags(kingpin.CommandLine)
	kingpin.HelpFlag.Short('h')
	kingpin.Parse()

	log.Infoln("Starting edgex_forwarder")

	// TODO: loop
	err := pushMetrics()
	if err != nil {
		log.Fatal("Failed to push metrics to pushgateway", err)
		os.Exit(-1)
	}
}
