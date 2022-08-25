# Minimal deployment

This step presents a minimal set of components to deploy a working Valhalla instance.

This configuration is set up for an Sydney-focused deployment.

## Requirements

* Docker CLI and Docker Compose must be installed
* Port 8002 must be accessible
* Approx. 20GB of disk storage available
## Deployment and configuration of Valhalla

### Deployment process

Deploy the Docker Compose file via the CLI, i.e.:

```bash
$ cd valhalla/mini-deployment
$ docker-compose up
```

This will begin the deployment process. On an initial deployment, Valhalla must download and process map data. Depending on the computational resources available, this may take a few hours (perhaps 2hrs on an `m5.xlarge` instance) and ultimately consume around 10GB of disk space.

Upon completion, call the `/status` address to test if Valhalla deployed successfully:

```bash
$ curl localhost:8002/status
{"version":"3.1.4","tileset_last_modified":1635754322}