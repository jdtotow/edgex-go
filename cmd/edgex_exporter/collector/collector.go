// This source code is based on
// "github.com/prometheus/node_exporter/collector/collector.go"
package collector

import (
	"fmt"
	"sync"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/common/log"
	"gopkg.in/alecthomas/kingpin.v2"
)

const namespace = "edgex"

var (
	factories     = make(map[string]func(string) (collector, error))
	collectorUrls = make(map[string]*string)
)

type collector interface {
	collect(ch chan<- prometheus.Metric) error
}

func registerCollector(collector, defaultUrl string, factory func(string) (collector, error)) {
	flagName := fmt.Sprintf("%s.server", collector)
	flagHelp := fmt.Sprintf("HTTP API address of a %s server.", defaultUrl)

	flag := kingpin.Flag(flagName, flagHelp).Default(defaultUrl).String()
	collectorUrls[collector] = flag

	factories[collector] = factory
}

type edgexCollector struct {
	collectors map[string]collector

	scrapeDuration *prometheus.Desc
	totalScrapes   prometheus.Counter
}

func NewEdgexCollector() (*edgexCollector, error) {
	collectors := make(map[string]collector)
	for key, url := range collectorUrls {
		collector, err := factories[key](*url)
		if err != nil {
			return nil, err
		}
		collectors[key] = collector
	}

	return &edgexCollector{
		collectors: collectors,
		scrapeDuration: prometheus.NewDesc(
			prometheus.BuildFQName(namespace, "scrape", "collector_duration_seconds"),
			"Duration of edgex_exporter scrapes.",
			nil,
			nil,
		),
		totalScrapes: prometheus.NewCounter(prometheus.CounterOpts{
			Name: "edgex_requests_total",
			Help: "Total of edgex_exporter scrapes.",
		}),
	}, nil
}

func execute(name string, c collector, ch chan<- prometheus.Metric) {
	err := c.collect(ch)
	if err != nil {
		log.Infof("ERROR: %s collector failed: %s", name, err)
	} else {
		log.Infof("OK: %s collector succeeded", name)
	}
}

func (e *edgexCollector) Collect(ch chan<- prometheus.Metric) {
	begin := time.Now()
	e.totalScrapes.Inc()

	wg := sync.WaitGroup{}
	wg.Add(len(e.collectors))
	for name, c := range e.collectors {
		go func(name string, c collector) {
			execute(name, c, ch)
			wg.Done()
		}(name, c)
	}
	wg.Wait()

	duration := time.Since(begin)
	ch <- prometheus.MustNewConstMetric(e.scrapeDuration, prometheus.GaugeValue, duration.Seconds())
	ch <- e.totalScrapes
}

func (e *edgexCollector) Describe(ch chan<- *prometheus.Desc) {
	ch <- e.scrapeDuration
	ch <- e.totalScrapes.Desc()
}
