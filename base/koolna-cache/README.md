# koolna-cache

Squid caching proxy for koolna pod package downloads. Caches HTTPS content via SSL bump so repeated `mise install`, `pip install`, and `npm install` across pods hit the cache instead of upstream registries.

## How it works

1. On first start, generates a self-signed CA certificate (persisted on PVC)
2. Exports the CA cert to a Kubernetes ConfigMap (`koolna-cache-ca`)
3. The koolna-operator mounts this ConfigMap into pods and sets proxy env vars
4. The koolna-tmux sidecar runs `update-ca-certificates` so pods trust the proxy CA
5. All HTTP/HTTPS traffic routes through squid, which caches immutable content (tarballs, wheels) aggressively

## Configuration

- `KOOLNA_NAMESPACE` - Kubernetes namespace (default: `default`)
- Cache size: 10GB (edit `cache_dir` in `squid.conf`)
- Max object size: 512MB

## Volumes

- `/var/spool/squid` - cache storage (mount a PVC here for persistence)
- `/etc/squid/ssl_cert` - CA cert and key (mount a PVC here to persist across restarts)
