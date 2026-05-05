# AGENTS.md

This repository contains the configuration for a Raspberry Pi home server dashboard.

The goal of this repo is to keep the dashboard infrastructure reproducible, simple,
and safe to modify with AI coding agents.

## Project Purpose

This stack provides a local home dashboard for services running on a Raspberry Pi.

Main services:

- Caddy as the local reverse proxy
- Homepage as the start dashboard
- Portainer as Docker management UI
- Glances as system metrics UI
- whoami as a reverse proxy test service

External applications linked from the dashboard:

- Quiz app: `http://myhouse.local:8081`
- Notes app: `http://myhouse.local:8082`

## Repository Structure

```text
.
|-- docker-compose.yml
|-- caddy/
|   `-- Caddyfile
|-- homepage/
|   `-- config/
|       |-- services.yaml
|       |-- settings.yaml
|       |-- widgets.yaml
|       |-- bookmarks.yaml
|       `-- kubernetes.yaml
|-- .env.example
|-- .gitignore
|-- README.md
`-- AGENTS.md
```

## Important Design Rules

Keep the setup simple.

Prefer explicit configuration over clever automation.

Do not introduce Kubernetes, Terraform, Ansible, or complex orchestration unless
explicitly requested.

This is a small Raspberry Pi home server, not a production cloud platform.

## Networking Model

Caddy is the main entry point.

Current model:

```text
LAN -> Caddy / exposed ports -> local Docker services
```

Current URLs:

```text
http://myhouse.local        -> Homepage
http://myhouse.local:8081   -> Quiz
http://myhouse.local:8082   -> Notes
http://myhouse.local:9000   -> Portainer
http://myhouse.local:61208  -> Glances
```

Current limitation:

Quiz and Notes are still exposed directly through ports because they are
root-mounted web apps and do not work cleanly under path prefixes like `/quiz`
or `/notes`.

Do not change this to path-based routing unless you also update the applications
to support non-root base paths.

Future preferred model:

```text
http://quiz.myhouse.local   -> Quiz
http://notes.myhouse.local  -> Notes
```

This requires local DNS or host file configuration.

## Caddy Rules

Use Caddy as the only service exposed on port 80.

Avoid enabling automatic HTTPS for `.local` addresses unless explicitly requested.

For LAN-only use, prefer:

```caddyfile
:80 {
    reverse_proxy homepage:3000
}
```

or explicit HTTP site labels:

```caddyfile
http://myhouse.local {
    reverse_proxy homepage:3000
}
```

Avoid plain:

```caddyfile
myhouse.local {
    reverse_proxy homepage:3000
}
```

because Caddy may try to enable automatic HTTPS and redirect HTTP to HTTPS.

## Homepage Rules

Homepage configuration lives in:

```text
homepage/config/
```

The most important file is:

```text
homepage/config/services.yaml
```

Use YAML list format. Correct structure:

```yaml
- Apps:
    - Quiz:
        href: http://myhouse.local:8081
        description: Aplikacja edukacyjna
        icon: mdi-school
```

Incorrect structure:

```yaml
Apps:
  Quiz:
    href: http://myhouse.local:8081
```

The incorrect structure can cause frontend errors such as:

```text
TypeError: g.map is not a function
```

Homepage uses its own `/api/*` endpoints. Do not route `/api/*` in Caddy to
another backend, because that breaks Homepage.

If exposing another backend through Caddy, use a different prefix such as:

```text
/home-api
/quiz-api
/notes-api
```

## Glances Rules

Glances runs on:

```text
http://myhouse.local:61208
```

The Glances service should be accessible from the Homepage container through
Docker DNS:

```text
http://glances:61208
```

The Glances container needs to bind to `0.0.0.0`:

```yaml
environment:
  - GLANCES_OPT=-w --bind 0.0.0.0
```

The service should be attached to the same Docker network as Homepage:

```yaml
networks:
  - home_net
```

For Homepage Glances widgets, use:

```yaml
widget:
  type: glances
  url: http://glances:61208
  version: 4
  metric: cpu
```

Known working metrics:

- `cpu`
- `memory`

Disk and temperature widgets are currently not fully configured. Do not assume
they work without testing the Glances API first.

Useful checks:

```bash
curl -s http://localhost:61208/api/4/cpu
curl -s http://localhost:61208/api/4/mem
curl -s http://localhost:61208/api/4/fs
curl -s http://localhost:61208/api/4/sensors
```

## Docker Rules

Use Docker Compose.

Do not remove volumes automatically.

Never run this without explicit user approval:

```bash
docker system prune --volumes
```

This may delete important persistent data.

Safe cleanup commands:

```bash
docker builder prune -f
docker system prune
sudo apt autoremove -y
sudo apt clean
```

Do not expose databases to LAN unless needed.

Current known issue:

`home-webserver-db` may still expose port `5432` to the LAN. This should be
cleaned up later, but not while making unrelated changes.

## Portainer Rules

Portainer runs on:

```text
http://myhouse.local:9000
```

Portainer has access to Docker through:

```text
/var/run/docker.sock:/var/run/docker.sock
```

Treat Portainer as an admin service.

Do not expose it to the public internet.

## Security Rules

This stack is intended for LAN-only use.

Do not add public exposure, Cloudflare Tunnel, port forwarding, public DNS, or
HTTPS automation unless explicitly requested.

Do not commit secrets.

Do not commit `.env`.

Do not commit API keys, tokens, passwords, private SSH keys, or database dumps.

Commit only `.env.example`.

## Git Rules

Before making changes, inspect the current state:

```bash
git status
docker compose ps
```

After changing Compose or config files, validate with:

```bash
docker compose config
```

Then apply changes with:

```bash
docker compose up -d
```

For service-specific recreation:

```bash
docker compose up -d --force-recreate <service>
```

Useful checks:

```bash
docker compose ps
docker compose logs --tail=100 caddy
docker compose logs --tail=100 homepage
curl -I http://localhost
curl -I http://localhost/whoami
```

## Testing Checklist

After modifying Caddy:

```bash
docker compose restart caddy
curl -I http://localhost
curl -I http://localhost/whoami
```

After modifying Homepage config:

```bash
docker compose up -d --force-recreate homepage
curl -s http://localhost/api/services
```

After modifying Glances:

```bash
docker compose up -d --force-recreate glances
docker exec -it homepage sh -c "wget -qO- http://glances:61208/api/4/cpu"
```

After modifying Docker Compose:

```bash
docker compose config
docker compose up -d
docker compose ps
```

## Current Known Working State

Working:

- Homepage loads at `http://myhouse.local`
- Quiz opens at `http://myhouse.local:8081`
- Notes opens at `http://myhouse.local:8082`
- Portainer opens at `http://myhouse.local:9000`
- Glances opens at `http://myhouse.local:61208`
- CPU and memory widgets from Glances work in Homepage

Known limitations:

- Quiz and Notes are not yet routed through clean local subdomains
- Disk and temperature widgets in Homepage are not fully configured
- Some backend/database ports may still be exposed directly
- Local DNS is not yet configured

## Style Preferences

Keep explanations and changes simple.

Prefer small, incremental changes.

Avoid large rewrites.

When adding a new service:

1. Add it to `docker-compose.yml`.
2. Start it with `docker compose up -d <service>`.
3. Verify it works directly.
4. Add a Homepage tile.
5. Only then consider Caddy routing.

## Do Not Do

Do not migrate everything to Kubernetes.

Do not introduce Traefik.

Do not replace Caddy with Nginx unless explicitly requested.

Do not remove working direct ports until replacement routing has been tested.

Do not delete Docker volumes.

Do not expose services publicly.

Do not assume `.local` subdomains work without local DNS.
