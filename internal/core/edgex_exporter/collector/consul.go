package collector

import (
	"net/url"

	"github.com/hashicorp/consul/api"
	"github.com/prometheus/client_golang/prometheus"
)

type consulCollector struct {
	client *api.Client

	totalServices *prometheus.Desc
}

func init() {
	registerCollector("consul", defaultConsulUrl, newConsulCollector)
}

func newConsulCollector(uri string) (collector, error) {
	u, err := url.Parse(uri)
	if err != nil {
		return nil, err
	}

	config := api.DefaultConfig()
	config.Address = u.Host
	config.Scheme = u.Scheme

	c, err := api.NewClient(config)
	if err != nil {
		return nil, err
	}

	return &consulCollector{
		client: c,
		totalServices: prometheus.NewDesc(
			prometheus.BuildFQName(namespace, "", "total_services"),
			"Total number of services connected to Consul",
			nil,
			nil,
		),
	}, nil
}

func (c *consulCollector) collect(ch chan<- prometheus.Metric) error {
	ret, _, err := c.client.Catalog().Services(&api.QueryOptions{}) // TODO
	if err != nil {
		return err
	}

	ch <- prometheus.MustNewConstMetric(c.totalServices, prometheus.GaugeValue, float64(len(ret)))

	return nil
}

func (c *consulCollector) describe(ch chan<- *prometheus.Desc) {
	ch <- c.totalServices
}
