# Flask Task Tracker | DevOps Learning Project

A small task-tracking web application that I used to practice **Python testing, Docker, Docker Compose, GitHub Actions, container registries, Linux, and server deployment**.

The aim of this project was not just to create a to-do app. I wanted to understand how an application goes from source code to a tested Docker image that can run on a separate Ubuntu Server virtual machine.

## What I built

The Flask app lets a user:

- Create, edit, complete, reopen, and delete tasks.
- Add a description and due date.
- Filter tasks by active or completed status.
- Keep tasks in a SQLite database.

The application also includes input validation, CSRF protection, and HTML escaping. It is a **single-user learning project**, not a publicly secured multi-user service.

## Technologies

| Technology | How I used it |
| --- | --- |
| Python + Flask | Built the web application using an application factory. |
| SQLite | Stored task data locally. |
| `unittest` | Tested task operations, validation, persistence, and security-related behavior. |
| Gunicorn | Served the Flask application inside the container. |
| Docker | Packaged the application and its dependencies into an image. |
| Docker Compose | Configured and ran the app with a persistent volume. |
| GitHub Actions | Ran tests and built/published Docker images after successful pushes. |
| GitHub Container Registry (GHCR) | Stored the published Docker images. |
| Ubuntu Server + KVM/QEMU | Provided a separate local server environment for hands-on deployment practice. |

## CI pipeline and image publishing

The workflow is defined in [`.github/workflows/tests.yml`](.github/workflows/tests.yml).

```text
Pull request to main
        |
        v
   Run Python tests

Push to main
        |
        v
   Run Python tests
        |
        v
 Build Docker image
        |
        v
  Publish to GHCR
   - latest tag
   - commit SHA tag
```

- **Pull requests targeting `main`** run the test job without publishing an image.
- **Pushes to `main`** run the tests first. The Docker job only starts if the tests succeed.
- The image is published as `ghcr.io/aigarasvait/task-tracker` with both `latest` and a commit-specific tag.

**Deployment is not automated through GitHub Actions.** The GitHub Actions workflow ends after publishing the image. I deploy/update the application on my Ubuntu Server VM separately rather than using a GitHub Actions SSH deployment job.

This project does **not** use Kubernetes; I plan to explore that in a separate project.

## Run the application locally

### Requirements

- Docker Engine
- Docker Compose plugin (`docker compose`)

Clone this repository and start the app:

```bash
git clone https://github.com/AigarasVait/task-tracker.git
cd task-tracker
docker compose up -d --build
```

Open **http://127.0.0.1:5000** on the computer running Docker.

The committed [`compose.yaml`](compose.yaml) builds the image locally and binds port 5000 to **127.0.0.1**, so it does not expose the app on every network interface.

Useful commands:

```bash
docker compose ps              # Show container status
docker compose logs -f web     # Follow application logs
docker compose up -d --build   # Rebuild and apply code changes
docker compose down            # Stop and remove containers; keep the data volume
```

> **Data:** Compose uses the named volume `task-data`, mounted at `/app/instance`. This preserves the SQLite database and the application's secret key when the container is recreated. Avoid `docker compose down -v` unless you intentionally want to remove the volume and its data.

If Docker requires administrative access on your machine, use `sudo` with the commands above.

## Run the tests

Install dependencies in a Python environment and execute:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -v
```

The three tests in [`test_app.py`](test_app.py) cover:

1. Task creation, editing, completion, deletion, and database persistence.
2. Invalid inputs, missing tasks, and unsupported requests.
3. CSRF checks and HTML escaping.

Tests use temporary SQLite databases so they do not change the normal app database.

## Docker image

The [`Dockerfile`](Dockerfile) uses `python:3.14-slim`, installs dependencies from `requirements.txt`, copies the application, and starts it with Gunicorn on port 5000.

A published image can be pulled using:

```bash
docker pull ghcr.io/aigarasvait/task-tracker:latest
```

For repeatable deployments, a **commit SHA tag** is preferable to the moving `latest` tag. Depending on the package's visibility, pulling from GHCR may require authentication.

## Local Ubuntu Server lab

To practise deployment beyond my development laptop, I set up a separate **Ubuntu Server virtual machine** using **KVM/QEMU and Virtual Machine Manager**. This helped me learn about Linux services, virtual networking, ports, SSH, and running containers on a server.

The server setup and application deployment work, but **updating the VM is a separate/manual step**; GitHub Actions currently automates testing and image publishing, not remote deployment.

The repository's `compose.yaml` is the **local-build configuration**. Deploying a prebuilt image from GHCR on a server requires a corresponding server-side Compose configuration that references the GHCR image rather than `build: .`.

## What I learned while building it

Some of the most useful lessons came from troubleshooting:

- **Missing Gunicorn:** A container could not start because the executable was not installed in the image. I added the dependency and rebuilt the image.
- **Container name conflicts:** I learned how stopped or failed containers can still reserve their names.
- **Persistent data:** I used a named Docker volume so recreating the application container would not remove its SQLite database.
- **Image naming:** GHCR/Docker image names must be lowercase. I updated the workflow to lowercase `GITHUB_REPOSITORY` and use that result in the image tags.
- **Networking:** I worked through port mappings, container listening addresses, firewall rules, and access between my Ubuntu desktop and server VM.
- **Virtualisation:** I troubleshot an initial libvirt connection problem while setting up my server lab.

## Project status

- [x] Build a working Flask task tracker.
- [x] Add automated Python tests.
- [x] Containerise the app with Docker and Gunicorn.
- [x] Manage the container and persistent data with Docker Compose.
- [x] Configure GitHub Actions to test pull requests and pushes to `main`.
- [x] Build and publish Docker images to GHCR after tests pass.
- [x] Set up a local Ubuntu Server VM and run the application there.
- [ ] Automate remote deployment from GitHub Actions (not implemented).

## Possible improvements

- Add code coverage and linting to CI.
- Add container health checks and more deployment documentation.
- Add authentication and HTTPS before considering public access.
- Document a reliable backup and restore process for the SQLite volume.
