pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        timestamps()
        disableConcurrentBuilds()
    }

    triggers {
        githubPush()
    }

    environment {
        K8S_NAMESPACE = 'aegis'
        MYSQL_TEST_CONTAINER = 'aegis-ci-mysql'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.IMAGE_TAG = "${env.BUILD_NUMBER}-${sh(script: 'git rev-parse --short=7 HEAD', returnStdout: true).trim()}"
                    echo "Building commit ${env.GIT_COMMIT} as image tag ${env.IMAGE_TAG}"
                }
            }
        }

        stage('Backend tests') {
            steps {
                sh '''#!/bin/sh
                    set -eu
                    docker rm -f "$MYSQL_TEST_CONTAINER" >/dev/null 2>&1 || true
                    docker run -d --name "$MYSQL_TEST_CONTAINER" \
                      -e MYSQL_DATABASE=aegis_test \
                      -e MYSQL_USER=aegis \
                      -e MYSQL_PASSWORD=aegis_ci_password \
                      -e MYSQL_ROOT_PASSWORD=aegis_ci_root_password \
                      -p 127.0.0.1:3307:3306 mysql:8.0
                    cleanup() { docker rm -f "$MYSQL_TEST_CONTAINER" >/dev/null 2>&1 || true; }
                    trap cleanup EXIT
                    ready=0
                    for attempt in $(seq 1 60); do
                      if docker exec "$MYSQL_TEST_CONTAINER" mysqladmin ping -h 127.0.0.1 -uaegis -paegis_ci_password --silent >/dev/null 2>&1; then
                        ready=1
                        break
                      fi
                      sleep 2
                    done
                    if [ "$ready" -ne 1 ]; then
                      docker logs "$MYSQL_TEST_CONTAINER"
                      echo 'MySQL did not become ready in time.' >&2
                      exit 1
                    fi

                    python3 -m venv .ci-venv
                    .ci-venv/bin/python -m pip install --upgrade pip
                    .ci-venv/bin/pip install -r backend/requirements.txt pytest
                    DATABASE_URL='mysql+pymysql://aegis:aegis_ci_password@127.0.0.1:3307/aegis_test' \
                    JWT_SECRET_KEY='ci-only-test-secret-key-that-is-at-least-32-characters' \
                    .ci-venv/bin/pytest --tb=short
                '''
            }
        }

        stage('Build frontend') {
            steps {
                dir('frontend') {
                    sh 'npm ci && npm run build'
                }
            }
        }

        stage('Build and push Docker images') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-credentials', usernameVariable: 'DH_USER', passwordVariable: 'DH_TOKEN')]) {
                    sh '''#!/bin/sh
                        set -eu
                        printf '%s' "$DH_TOKEN" | docker login --username "$DH_USER" --password-stdin
                        docker build -f backend/Dockerfile \
                          -t "$DH_USER/aegis-backend:$IMAGE_TAG" \
                          -t "$DH_USER/aegis-backend:latest" .
                        docker build -f Dockerfile --build-arg VITE_API_URL=/api \
                          -t "$DH_USER/aegis-web:$IMAGE_TAG" \
                          -t "$DH_USER/aegis-web:latest" .
                        docker push "$DH_USER/aegis-backend:$IMAGE_TAG"
                        docker push "$DH_USER/aegis-backend:latest"
                        docker push "$DH_USER/aegis-web:$IMAGE_TAG"
                        docker push "$DH_USER/aegis-web:latest"
                        docker logout
                    '''
                }
            }
        }

        stage('Deploy to Minikube') {
            steps {
                withCredentials([
                    usernamePassword(credentialsId: 'dockerhub-credentials', usernameVariable: 'DH_USER', passwordVariable: 'DH_TOKEN'),
                    string(credentialsId: 'aegis-mysql-password', variable: 'MYSQL_PASSWORD'),
                    string(credentialsId: 'aegis-mysql-root-password', variable: 'MYSQL_ROOT_PASSWORD'),
                    string(credentialsId: 'aegis-jwt-secret', variable: 'JWT_SECRET_KEY')
                ]) {
                    sh '''#!/bin/sh
                        set -eu
                        minikube status
                        kubectl config use-context minikube
                        kubectl apply -f k8s/namespace.yaml

                        kubectl create secret generic aegis-secrets -n "$K8S_NAMESPACE" \
                          --from-literal=mysql-root-password="$MYSQL_ROOT_PASSWORD" \
                          --from-literal=mysql-password="$MYSQL_PASSWORD" \
                          --from-literal=jwt-secret-key="$JWT_SECRET_KEY" \
                          --dry-run=client -o yaml | kubectl apply -f -
                        kubectl create secret docker-registry aegis-dockerhub -n "$K8S_NAMESPACE" \
                          --docker-server=https://index.docker.io/v1/ \
                          --docker-username="$DH_USER" --docker-password="$DH_TOKEN" \
                          --dry-run=client -o yaml | kubectl apply -f -

                        kubectl apply -f k8s/mysql.yaml
                        kubectl rollout status deployment/aegis-mysql -n "$K8S_NAMESPACE" --timeout=240s

                        kubectl apply -f k8s/backend.yaml
                        kubectl set image deployment/aegis-backend \
                          backend="$DH_USER/aegis-backend:$IMAGE_TAG" -n "$K8S_NAMESPACE"
                        kubectl rollout status deployment/aegis-backend -n "$K8S_NAMESPACE" --timeout=240s

                        kubectl apply -f k8s/web.yaml
                        kubectl set image deployment/aegis-web \
                          web="$DH_USER/aegis-web:$IMAGE_TAG" -n "$K8S_NAMESPACE"
                        kubectl rollout status deployment/aegis-web -n "$K8S_NAMESPACE" --timeout=240s
                    '''
                }
            }
        }

        stage('Verify deployment') {
            steps {
                sh '''#!/bin/sh
                    set -eu
                    kubectl get pods,deployments,services -n "$K8S_NAMESPACE" -o wide
                    kubectl port-forward --address 127.0.0.1 \
                      service/aegis-web 18080:80 -n "$K8S_NAMESPACE" \
                      >/tmp/aegis-port-forward.log 2>&1 &
                    port_forward_pid=$!
                    trap 'kill "$port_forward_pid" >/dev/null 2>&1 || true' EXIT
                    ready=0
                    for attempt in $(seq 1 30); do
                      if curl --fail --silent http://127.0.0.1:18080/health; then
                        echo '\nAEGIS web service health check passed.'
                        ready=1
                        break
                      fi
                      sleep 2
                    done
                    if [ "$ready" -ne 1 ]; then
                      cat /tmp/aegis-port-forward.log
                      echo 'AEGIS web health check failed.' >&2
                      exit 1
                    fi
                '''
            }
        }
    }

    post {
        always {
            sh 'docker rm -f "$MYSQL_TEST_CONTAINER" >/dev/null 2>&1 || true'
            archiveArtifacts artifacts: 'frontend/dist/**', allowEmptyArchive: true
        }
    }
}
