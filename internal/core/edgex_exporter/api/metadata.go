// This package should be replaced by "github.com/edgexfoundry/core-clients-go"
package api

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"

	"github.com/edgexfoundry/core-domain-go/models"
)

// TODO: remove it later
type Device struct {
	Name           string `json:"name"`
	Description    string `json:"description"`
	AdminState     string `json:"adminState"`
	OperatingState string `json:"operatingState"`
	//Addressable    map[string]string `json:"addressable"`
	//Labels         []string          `json:"labels"`
	//Location       string            `json:"location"`
	//Service        map[string]string `json:"service"`
	//Profile        map[string]string `json:"profile"`
}

type Metadata struct {
	BaseUrl    string
	HTTPClient *http.Client
	// logger *log.Logger
}

func NewMetadataClient(urlstr string) *Metadata {
	return &Metadata{
		BaseUrl:    urlstr,
		HTTPClient: &http.Client{},
	}
}

func (m *Metadata) CreateAddressable(a models.Addressable) error {
	spath := "/addressable/"
	jsonBytes, _ := json.Marshal(a)

	req, err := newJsonRequest(m.BaseUrl, "POST", spath, bytes.NewBuffer(jsonBytes))
	if err != nil {
		return err
	}

	res, err := m.HTTPClient.Do(req)
	if err != nil {
		return err
	}
	defer res.Body.Close()

	return nil
}

func (m *Metadata) ListAddressable() (*[]models.Addressable, error) {
	spath := "/addressable"
	req, err := newRequest(m.BaseUrl, "GET", spath, nil)
	if err != nil {
		return nil, err
	}

	res, err := m.HTTPClient.Do(req)
	if err != nil {
		return nil, err
	}

	var a []models.Addressable
	if err := decodeBody(res, &a); err != nil {
		return nil, err
	}

	return &a, nil
}

func (m *Metadata) GetAddressable(name string) (*models.Addressable, error) {
	spath := fmt.Sprintf("/addressable/name/%s", name)
	req, err := newRequest(m.BaseUrl, "GET", spath, nil)
	if err != nil {
		return nil, err
	}

	res, err := m.HTTPClient.Do(req)
	if err != nil {
		return nil, err
	}

	var a models.Addressable
	if err := decodeBody(res, &a); err != nil {
		return nil, err
	}

	return &a, nil
}

func (m *Metadata) GetAddressableCount() (int, error) {
	a, err := m.ListAddressable()
	if err != nil {
		return 0, err
	}
	return len(*a), nil
}

func (m *Metadata) DeleteAddressable(name string) error {
	spath := fmt.Sprintf("/addressable/name/%s", name)
	req, err := newRequest(m.BaseUrl, "DELETE", spath, nil)
	if err != nil {
		return err
	}

	res, err := m.HTTPClient.Do(req)
	if err != nil {
		return err
	}
	defer res.Body.Close()

	return nil
}

func (m *Metadata) CreateDeviceProfile(filePath string) error {
	spath := fmt.Sprintf("/deviceprofile/uploadfile")
	req, err := newFileUploadRequest(m.BaseUrl, "POST", spath, filePath)
	if err != nil {
		return err
	}

	res, err := m.HTTPClient.Do(req)
	if err != nil {
		return err
	}
	defer res.Body.Close()

	return nil
}

func (m *Metadata) DeleteDeviceProfile(name string) error {
	spath := fmt.Sprintf("/deviceprofile/name/%s", name)
	req, err := newRequest(m.BaseUrl, "DELETE", spath, nil)
	if err != nil {
		return err
	}

	res, err := m.HTTPClient.Do(req)
	if err != nil {
		return err
	}
	defer res.Body.Close()

	return nil
}

func (m *Metadata) CreateDevice(d models.Device) error {
	return nil
}

func (m *Metadata) GetDevice(name string) (*Device, error) {
	spath := fmt.Sprintf("/device/name/%s", name)
	req, err := newRequest(m.BaseUrl, "GET", spath, nil)
	if err != nil {
		return nil, err
	}

	res, err := m.HTTPClient.Do(req)
	if err != nil {
		return nil, err
	}

	var d Device
	if err := decodeBody(res, &d); err != nil {
		return nil, err
	}

	return &d, nil
}

func (m *Metadata) ListDevice() (*[]Device, error) {
	spath := "/device"
	req, err := newRequest(m.BaseUrl, "GET", spath, nil)
	if err != nil {
		return nil, err
	}

	res, err := m.HTTPClient.Do(req)
	if err != nil {
		return nil, err
	}

	var d []Device
	if err := decodeBody(res, &d); err != nil {
		return nil, err
	}

	return &d, nil
}

func (m *Metadata) GetDeviceCount() (int, error) {
	d, err := m.ListDevice()
	if err != nil {
		return 0, err
	}

	return len(*d), nil
}

func (m *Metadata) DeleteDevice(name string) error {
	// TOOD: not implemented yet
	return nil
}

func (m *Metadata) CreateDeviceService(ds models.DeviceService) error {
	spath := "/deviceservice"
	jsonBytes, _ := json.Marshal(ds)

	req, err := newJsonRequest(m.BaseUrl, "POST", spath, bytes.NewBuffer(jsonBytes))
	if err != nil {
		return err
	}

	res, err := m.HTTPClient.Do(req)
	if err != nil {
		return err
	}
	defer res.Body.Close()

	return nil
}

func (m *Metadata) GetDeviceService(name string) error {
	// TOOD: not implemented yet
	return nil
}

func (m *Metadata) DeleteDeviceService(name string) error {
	spath := fmt.Sprintf("/deviceservice/name/%s", name)
	req, err := newRequest(m.BaseUrl, "DELETE", spath, nil)
	if err != nil {
		return err
	}

	res, err := m.HTTPClient.Do(req)
	if err != nil {
		return err
	}
	defer res.Body.Close()

	return nil
}
