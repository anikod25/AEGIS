# AEGIS CI/CD Deployment Guide

## Project and repository

AEGIS is the existing React, FastAPI, and MySQL academic project. Source repository: <https://github.com/anikod25/AEGIS>.

The pipeline uses Jenkins, Docker Hub, and a Minikube cluster on the AWS Jenkins host. It checks out each commit, runs the backend tests with a temporary MySQL container, builds the frontend, builds and pushes tagged backend and web images, deploys MySQL/backend/web to Kubernetes, and checks `/health` through the deployed web service.

## Files added for the assignment

- `Jenkinsfile` — declarative pipeline from checkout to verification.
- `Dockerfile` — multi-stage image that builds React and serves it through the existing Nginx gateway configuration.
- `backend/Dockerfile` — existing FastAPI image.
- `k8s/` — namespace, MySQL with persistent storage, backend, web Deployment and Services.

The pipeline publishes two images: `<Docker-Hub-user>/aegis-backend` and `<Docker-Hub-user>/aegis-web`. Each run pushes a build-number/commit tag and `latest`.

## AWS and Jenkins setup

Use an AWS Linux VM with enough disk and memory for Jenkins, Docker, and Minikube. Install/configure Jenkins, Docker Engine, Minikube, kubectl, Python 3.12 with `venv`, Node.js 22/npm, and curl on the Jenkins agent. The Jenkins service account must be able to use Docker and the Minikube/kubectl configuration. Start Minikube as that same account and verify `minikube status` and `kubectl get nodes` before running the job.

Install Jenkins plugins for Pipeline, Git, Credentials Binding, and GitHub integration. Create a Pipeline job from SCM using this repository and `Jenkinsfile`. Configure GitHub to send push events to `https://<your-jenkins-host>/github-webhook/` and enable the GitHub hook trigger on the job. Keep Jenkins behind access controls; do not expose its admin port publicly.

Create these Jenkins credentials with the exact IDs below:

| ID | Jenkins credential type | Use |
|---|---|---|
| `dockerhub-credentials` | Username with password | Docker Hub login and Kubernetes image pull secret |
| `aegis-mysql-password` | Secret text | MySQL application user password |
| `aegis-mysql-root-password` | Secret text | MySQL root password |
| `aegis-jwt-secret` | Secret text | AEGIS JWT signing key, at least 32 characters |

Use long alphanumeric passwords for the two MySQL credentials because the backend builds its database URL from the password. Do not commit credentials or `.env` files. Create the two Docker Hub repositories (`aegis-backend` and `aegis-web`) under the account used by Jenkins. Public repositories are simplest for Minikube; the pipeline also creates a pull secret for private repositories.

## Pipeline stages

1. **Checkout** — Jenkins checks out the GitHub revision and derives an image tag from the build number and commit hash.
2. **Backend tests** — starts disposable MySQL, installs backend requirements and pytest, and runs `pytest --tb=short`.
3. **Build frontend** — runs `npm ci` and `npm run build`.
4. **Build and push images** — builds the backend and combined React/Nginx web images and pushes both tags to Docker Hub.
5. **Deploy to Minikube** — applies the namespace, secrets, MySQL storage/deployment/service, and the backend/web Deployments and Services. It waits for all rollouts.
6. **Verify** — prints pods, Deployments, and Services, then port-forwards the web Service and requests `/health`.

## Run it and access AEGIS

Run the Jenkins job once. A green run means tests passed, both images were pushed, Kubernetes rollouts completed, and the web health check returned successfully. Jenkins output includes the pod and Service status. The web Service is a NodePort on `30080`.

For an AWS Minikube host, the reliable browser access method is an SSH tunnel. On the AWS host, run:

```bash
kubectl port-forward --address 127.0.0.1 -n aegis service/aegis-web 8080:80
```

On your computer, create a tunnel (replace the login and host with your AWS details):

```bash
ssh -L 8080:127.0.0.1:8080 <ssh-user>@<aws-public-ip>
```

Open `http://localhost:8080`. This avoids exposing the application or Kubernetes ports publicly. If using the NodePort directly for a classroom demo, allow TCP `30080` only from your own public IP in the AWS security group, then try `http://<aws-public-ip>:30080`; Minikube's Docker driver may require the SSH tunnel instead.

## Demonstrate the second deployment

After the first successful run, make a small visible change in the frontend (for example, edit a heading or footer), commit and push it to the configured branch, and let the GitHub webhook start Jenkins again. Show the second build's commit-specific image tag, successful rollout, health check, and the updated page in the browser. Capture screenshots of the successful Jenkins stages, Docker Hub tags, `kubectl get pods/deployments/services -n aegis`, and the updated application for submission.

## Current limitations

This deployment is intended for the assignment demo. It uses a single-replica MySQL Deployment and does not configure TLS, external database backups, or production ingress. The Jenkins agent must be able to reach Docker Hub and have a working Minikube cluster before deployment stages can pass.
