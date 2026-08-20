function getPort(config: AppConfig | null): number | undefined {
    if (config && config.server) {
        return config.server.port;
    }
    return undefined;
}
