package collector

import (
	"github.com/ohmk/edgex_exporter/api"
	"github.com/prometheus/client_golang/prometheus"
)

type metadataCollector struct {
	client *api.Metadata

	totalDevices *prometheus.Desc
}

func init() {
	registerCollector("metadata", defaultMetadataUrl, newMetadataCollector)
}

func newMetadataCollector(url string) (collector, error) {
	c := api.NewMetadataClient(url)

	return &metadataCollector{
		client: c,
		totalDevices: prometheus.NewDesc(
			prometheus.BuildFQName(namespace, "", "total_devices"),
			"Total number of devices connected to EdgeX Foundry.",
			nil,
			nil,
		),
	}, nil
}

func (m *metadataCollector) collect(ch chan<- prometheus.Metric) error {
	ret, err := m.client.GetDeviceCount()
	if err != nil {
		return err
	}

	ch <- prometheus.MustNewConstMetric(m.totalDevices, prometheus.GaugeValue, float64(ret))

	return nil
}

func (m *metadataCollector) describe(ch chan<- *prometheus.Desc) {
	ch <- m.totalDevices
}
