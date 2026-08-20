function buildUrl(host: string, port: number, path: string): string {
    return "https://" + host + ":" + port + "/" + path;
}
