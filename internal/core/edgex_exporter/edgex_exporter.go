package main

import (
	"net/http"
	"os"

	"github.com/ohmk/edgex_exporter/collector"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"github.com/prometheus/common/log"
	"github.com/prometheus/common/version"
	"gopkg.in/alecthomas/kingpin.v2"
)

var (
	listenAddress = kingpin.Flag(
		"web.listen-address",
		"Address on which to expose metrics and web interface.",
	).Default(":9410").String()
	metricsPath = kingpin.Flag(
		"web.telemetry-path",
		"Path under which to expose metrics.",
	).Default("/metrics").String()
)

func init() {
	prometheus.MustRegister(version.NewCollector("edgex_exporter"))
}

func main() {
	log.AddFlags(kingpin.CommandLine)
	kingpin.Version(version.Print("edgex_exporter"))
	kingpin.HelpFlag.Short('h')
	kingpin.Parse()

	log.Infoln("Starting edgex_exporter", version.Info())
	log.Infoln("Build context", version.BuildContext())

	ec, err := collector.NewEdgexCollector()
	if err != nil {
		log.Fatal("Couldn't create collector", err)
		os.Exit(-1)
	}

	prometheus.MustRegister(ec)
	http.Handle(*metricsPath, promhttp.Handler())

	log.Infoln("Listening on", *listenAddress)
	log.Fatal(http.ListenAndServe(*listenAddress, nil))
}
