function getPort(config: AppConfig | null): number | undefined {
    return config?.server?.port;
}
