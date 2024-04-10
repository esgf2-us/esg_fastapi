# ESGF Search API
This Project is developed as a speculative replacement for the existing Java based ESG Search API layer. The current implementation is based on FastAPI for an asynchronous framework.

## Installation
The primary installation target is Kubernetes via Helm, but since that requires a Docker container, you can also run that container locally via Docker or Podman. For example:
```bash
podman run -it code.ornl.gov:4567/esgf/mirrors/esg_fastapi/esgf-esg-fastapi
```

## Contributing
To install and develop locally, use Poetry to create a virtual environment with the dependencies and configuration setup:
```bash
poetry install
```

And start the server in `watch` mode with uvicorn:
```bash
uvicorn esg_fastapi.api --reload
```
While running in this mode, uvicorn will serve the API on http://localhost:8080 and watch for any changes to the source files. When detected, the server will reload the application automatically to include the new changes.