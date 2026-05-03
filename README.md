# SwiftDeploy

A declarative CLI tool that generates Nginx and Docker Compose configs from a single manifest.yaml and manages the full container lifecycle.

## Prerequisites

- Docker installed
- Python 3.10+
- jinja2 and pyyaml installed

Install dependencies:

    pip3 install jinja2 pyyaml

## Quick Start

    git clone https://github.com/Ada-Mazi/swiftdeploy
    cd swiftdeploy
    pip3 install jinja2 pyyaml
    docker build -t swift-deploy-1-node:latest app/
    ./swiftdeploy deploy

## Subcommands

### init
Parses manifest.yaml and generates nginx.conf and docker-compose.yml

    ./swiftdeploy init

### validate
Runs 5 pre-flight checks

    ./swiftdeploy validate

Checks:
1. manifest.yaml exists and is valid YAML
2. All required fields present and non-empty
3. Docker image exists locally
4. Nginx port is not already bound
5. Generated nginx.conf is syntactically valid

### deploy
Builds image, starts stack, waits for health checks

    ./swiftdeploy deploy

### promote
Switches mode with rolling restart

    ./swiftdeploy promote canary
    ./swiftdeploy promote stable

### teardown
Removes all containers, networks, volumes

    ./swiftdeploy teardown
    ./swiftdeploy teardown --clean

## API Endpoints

- GET /        welcome message with mode, version, timestamp
- GET /healthz liveness check with status and uptime
- POST /chaos  simulate degraded behaviour (canary mode only)

## Chaos Modes (canary only)

    curl -X POST http://localhost:8090/chaos -H "Content-Type: application/json" -d '{"mode": "slow", "duration": 2}'
    curl -X POST http://localhost:8090/chaos -H "Content-Type: application/json" -d '{"mode": "error", "rate": 0.5}'
    curl -X POST http://localhost:8090/chaos -H "Content-Type: application/json" -d '{"mode": "recover"}'

## GitHub Repo

https://github.com/Ada-Mazi/swiftdeploy
