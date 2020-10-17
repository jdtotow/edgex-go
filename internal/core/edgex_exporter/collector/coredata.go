package collector

import (
	"github.com/ohmk/edgex_exporter/api"
	"github.com/prometheus/client_golang/prometheus"
)

type coreDataCollector struct {
	client *api.CoreData

	totalEvents   *prometheus.Desc
	totalReadings *prometheus.Desc
}

func init() {
	registerCollector("coredata", defaultCoreDataUrl, newCoreDataCollector)
}

func newCoreDataCollector(url string) (collector, error) {
	c := api.NewCoreDataClient(url)

	return &coreDataCollector{
		client: c,
		totalEvents: prometheus.NewDesc(
			prometheus.BuildFQName(namespace, "", "total_events"),
			"Total number of events.",
			nil,
			nil,
		),
		totalReadings: prometheus.NewDesc(
			prometheus.BuildFQName(namespace, "", "total_readings"),
			"Total number of readings.",
			nil,
			nil,
		),
	}, nil
}

func (c *coreDataCollector) collect(ch chan<- prometheus.Metric) error {
	nEvents, err := c.client.GetEventCount()
	if err != nil {
		return err
	}

	nReadings, err := c.client.GetReadingCount()
	if err != nil {
		return err
	}

	ch <- prometheus.MustNewConstMetric(c.totalEvents, prometheus.GaugeValue, float64(nEvents))
	ch <- prometheus.MustNewConstMetric(c.totalReadings, prometheus.GaugeValue, float64(nReadings))

	return nil
}

func (c *coreDataCollector) describe(ch chan<- *prometheus.Desc) {
	ch <- c.totalEvents
	ch <- c.totalReadings
}
