// This package should be replaced by "github.com/edgexfoundry/core-clients-go"
package api

import (
	"bytes"
	"encoding/json"
	"io"
	"io/ioutil"
	"mime/multipart"
	"net/http"
	"os"
)

type Client struct {
	Metadata *Metadata
	CoreData *CoreData
	// Logger *log.Logger
}

func NewClient(metadataUrl, coreDataUrl string) *Client {
	return &Client{
		Metadata: NewMetadataClient(metadataUrl),
		CoreData: NewCoreDataClient(coreDataUrl),
	}
}

func decodeBody(res *http.Response, out interface{}) error {
	defer res.Body.Close()
	decoder := json.NewDecoder(res.Body)

	return decoder.Decode(out)
}

func newRequest(baseUrl, method, spath string, body io.Reader) (*http.Request, error) {
	path := baseUrl + spath

	req, err := http.NewRequest(method, path, body)
	if err != nil {
		return nil, err
	}

	// req.SetBasicAuth(c.Username, c.Password)
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")

	return req, nil
}

func newJsonRequest(baseUrl string, method string, spath string, body io.Reader) (*http.Request, error) {
	path := baseUrl + spath

	req, err := http.NewRequest(method, path, body)
	if err != nil {
		return nil, err
	}

	req.Header.Set("Content-Type", "application/json")

	return req, nil
}

func newFileUploadRequest(baseUrl string, method string, spath string, filePath string) (*http.Request, error) {
	path := baseUrl + spath

	file, err := os.Open(filePath)
	if err != nil {
		return nil, err
	}

	fileContents, err := ioutil.ReadAll(file)
	if err != nil {
		return nil, err
	}

	fi, err := file.Stat()
	if err != nil {
		return nil, err
	}
	file.Close()

	body := new(bytes.Buffer)
	writer := multipart.NewWriter(body)
	part, err := writer.CreateFormFile("file", fi.Name())
	if err != nil {
		return nil, err
	}
	part.Write(fileContents)

	err = writer.Close()
	if err != nil {
		return nil, err
	}
	req, err := http.NewRequest(method, path, body)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", writer.FormDataContentType())

	return req, nil
}
