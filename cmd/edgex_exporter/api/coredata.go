// This package should be replaced by "github.com/edgexfoundry/core-clients-go"
package api

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"

	"github.com/edgexfoundry/core-domain-go/models"
)

type CoreData struct {
	BaseUrl    string
	HTTPClient *http.Client
	// logger *log.Logger
}

func NewCoreDataClient(urlstr string) *CoreData {
	return &CoreData{
		BaseUrl:    urlstr,
		HTTPClient: &http.Client{},
	}
}

func (c *CoreData) CreateValueDescriptor(v models.ValueDescriptor) error {
	spath := "/valuedescriptor"
	jsonBytes, _ := json.Marshal(v)

	req, err := newJsonRequest(c.BaseUrl, "POST", spath, bytes.NewBuffer(jsonBytes))

	if err != nil {
		return err
	}

	res, err := c.HTTPClient.Do(req)
	if err != nil {
		return err
	}
	defer res.Body.Close()

	return nil
}

func (c *CoreData) ListValueDescriptor() (*[]models.ValueDescriptor, error) {
	spath := fmt.Sprintf("/valuedescriptor")
	req, err := newRequest(c.BaseUrl, "GET", spath, nil)
	if err != nil {
		return nil, err
	}

	res, err := c.HTTPClient.Do(req)
	if err != nil {
		return nil, err
	}

	var v []models.ValueDescriptor
	if err := decodeBody(res, &v); err != nil {
		return nil, err
	}
	return &v, nil
}

func (c *CoreData) DeleteValueDescriptor(name string) error {
	spath := fmt.Sprintf("/valuedescriptor/name/%s", name)
	req, err := newRequest(c.BaseUrl, "DELETE", spath, nil)
	if err != nil {
		return err
	}

	res, err := c.HTTPClient.Do(req)
	if err != nil {
		return err
	}
	defer res.Body.Close()

	return nil
}

func (c *CoreData) GetReadingCount() (int, error) {
	spath := "/reading/count"
	req, err := newRequest(c.BaseUrl, "GET", spath, nil)
	if err != nil {
		return 0, err
	}

	res, err := c.HTTPClient.Do(req)
	if err != nil {
		return 0, err
	}

	var count int
	if err := decodeBody(res, &count); err != nil {
		return 0, err
	}

	return count, nil
}

func (c *CoreData) GetEventCount() (int, error) {
	spath := "/event/count"
	req, err := newRequest(c.BaseUrl, "GET", spath, nil)
	if err != nil {
		return 0, err
	}

	res, err := c.HTTPClient.Do(req)
	if err != nil {
		return 0, err
	}

	var count int
	if err := decodeBody(res, &count); err != nil {
		return 0, err
	}

	return count, nil
}
