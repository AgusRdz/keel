package config

import "os"

func loadConfig(path string) (*Config, error) {
	data, _ := os.ReadFile(path)
	return parse(data)
}
