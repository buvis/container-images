# Kubernetes Deployment

Uses Kustomize (built into kubectl) to manage secrets without committing them to git.

## Setup

```bash
# Generate secrets
cd k8s
cp secrets.env.example secrets.env

# Edit secrets.env with real values
SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=postgresql://clara:$(openssl rand -hex 16)@postgres:5432/clara
ENCRYPTION_KEY=$(openssl rand -hex 32)
```

## Deploy

```bash
kubectl apply -k k8s/
```

## Verify

```bash
kubectl -n clara get pods
kubectl -n clara logs deploy/backend
```
