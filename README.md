# Home Server Infra

Configuration for my Raspberry Pi home server infrastructure and dashboard.

## Services

- Caddy reverse proxy
- Homepage start panel
- Portainer Docker UI
- Glances system metrics
- MySpeed internet speed tests
- whoami reverse proxy test service

## Local URLs

- Homepage: http://myhouse.local
- Quiz: http://myhouse.local:8081
- Notes: http://myhouse.local:8082
- Portainer: http://myhouse.local:9000
- Glances: http://myhouse.local:61208
- MySpeed: http://myhouse.local:5216

## Setup

```bash
cp .env.example .env
docker compose up -d
```

Set `HOMEPAGE_VAR_PORTAINER_API_KEY` in `.env` to enable the Portainer
containers widget. If the widget says it cannot find the environment, set
`HOMEPAGE_VAR_PORTAINER_ENV_ID` to the matching Portainer environment ID.

## Restart

```bash
docker compose restart
```

## Logs

```bash
docker compose logs -f
```

## Check Disk Usage

```bash
df -h
docker system df
```

## Safe Cleanup

```bash
docker builder prune -f
docker system prune
sudo apt autoremove -y
sudo apt clean
```

Do not run `docker system prune --volumes` unless you are sure that unused
volumes do not contain important data.
