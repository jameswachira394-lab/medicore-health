# MediCore Health Platform

A cloud-native healthcare management SaaS platform — 8 FastAPI microservices,
database-per-service PostgreSQL, DevSecOps CI/CD, and production-grade
Kubernetes/Terraform infrastructure for AWS EKS.

## Repository layout

```
medicore-health-platform/
├── frontend/                     # React (Vite) SPA — Patient Portal, Doctor Dashboard, Admin Dashboard
├── services/
│   ├── api-gateway/              # Single entry point; reverse-proxies to the 8 microservices below
│   ├── auth-service/             # Registration, login, MFA, JWT, password reset
│   ├── patient-service/          # Patient profiles (encrypted PII)
│   ├── doctor-service/           # Doctor profiles + availability
│   ├── appointment-service/      # Booking engine, waitlist, reschedule/cancel
│   ├── medical-records-service/  # Diagnoses, prescriptions, lab tests (strict RBAC)
│   ├── billing-service/          # Invoices, payments, insurance claims
│   ├── notification-service/     # Email/SMS/push fan-out
│   └── reporting-service/        # Analytics rollups for hospital dashboards
├── shared/common/                # Shared library: config, DB, JWT/RBAC, encryption, audit logging
├── infra/
│   ├── terraform/                # VPC, EKS, RDS (per-service), S3 modules + dev/staging/prod envs
│   ├── k8s/                      # Base manifests + Kustomize overlays (dev/staging/prod)
│   ├── helm/medicore/            # Equivalent Helm chart (alternative to Kustomize)
│   ├── argocd/                   # ArgoCD Application definitions (GitOps)
│   ├── monitoring/                # Prometheus, Grafana dashboard, Loki/Promtail values
│   └── db/                       # Local multi-database init script
├── .github/workflows/            # CI/CD (test → scan → build → push → deploy) + Terraform pipeline
├── docker-compose.yml            # Full local stack (frontend + gateway + all 9 services + Postgres + Redis)
└── Makefile
```

## Architecture

Each microservices owns its own database (auth_db, patient_db, doctor_db,
appointment_db, records_db, billing_db, notification_db, reporting_db),
communicates over HTTP + JWT bearer tokens issued by `auth-service`, and is
independently containerized, tested, scanned, and deployed.

```
Browser (React SPA) → CloudFront → WAF → ALB → Ingress (nginx)
                                                    ├── app.medicore.health  → frontend (nginx, static SPA)
                                                    └── api.medicore.health  → api-gateway → microservices → RDS/S3/Redis
```

The frontend never talks to individual microservices — it calls the `api-gateway` exclusively, which reverse-proxies each path prefix (`/auth`, `/patients`, `/doctors`, `/appointments`, `/medical-records`, `/billing`, `/notifications`, `/reports`) to the owning service and forwards the JWT bearer token unchanged. Each downstream service still independently validates that token and enforces its own RBAC — the gateway is a routing layer, not a substitute trust boundary.

Role-based access is enforced in every service via `shared_common.security`:
`patient`, `doctor`, `nurse`, `receptionist`, `hospital_admin`, `system_admin`.
Notably: doctors cannot access billing, and billing/reception cannot access
medical records — enforced in code and covered by tests.

### Frontend

A single React (Vite + Tailwind) SPA serves all three portals behind role-based routing:

| Portal | Routes | Who |
|---|---|---|
| Patient | `/patient`, `/patient/find-a-doctor`, `/patient/appointments`, `/patient/records`, `/patient/billing` | `patient` |
| Doctor | `/doctor`, `/doctor/schedule`, `/doctor/availability`, `/doctor/patients/:id` | `doctor`, `nurse` |
| Admin | `/admin`, `/admin/doctors`, `/admin/reports` | `receptionist`, `hospital_admin`, `system_admin` |

JWT access/refresh tokens are stored in `localStorage`; the API client transparently retries once on a 401 after refreshing the access token, and clears tokens + redirects to `/login` if the refresh itself fails.

## Running locally

```bash
make up            # docker compose up --build -d — starts everything, including the UI
make logs           # tail all services
make down           # tear down
```

Once `make up` finishes:

| | URL |
|---|---|
| **Frontend (start here)** | http://localhost:5173 |
| API Gateway (single entry point) | http://localhost:8000 |
| auth-service | http://localhost:8001 |
| patient-service | http://localhost:8002 |
| doctor-service | http://localhost:8003 |
| appointment-service | http://localhost:8004 |
| medical-records-service | http://localhost:8005 |
| billing-service | http://localhost:8006 |
| notification-service | http://localhost:8007 |
| reporting-service | http://localhost:8008 |

The frontend talks only to the gateway (`VITE_API_BASE_URL=http://localhost:8000`); the individual service ports are exposed for direct API exploration via `/docs` on each. Register a patient account at `/register`, or add doctors/staff by registering through `POST /auth/register` with `role` set to `doctor`, `nurse`, `receptionist`, `hospital_admin`, or `system_admin` (there's no self-serve staff signup UI by design — a `hospital_admin` links a registered doctor account to a doctor profile via Admin → Doctors).

## Running test

```bash
make test-all
```

All 9 services (8 microservices + the API Gateway) currently pass their
full test suites, covering registration/login/MFA/lockout, encrypted-PII
CRUD, double-booking prevention, cross-role access-control boundaries,
invoicing/payments, notification fan-out, and gateway proxying/routing.

For the frontend:

```bash
cd frontend
npm install
npm run dev      # hot-reload dev server at http://localhost:5173
npm run build    # production build (static assets, served by nginx in prod)
npm run lint     # oxlint
```

## Deploying to AWS infrastructure

1. **Infrastructure**: `cd infra/terraform/envs/<env> && terraform init && terraform apply`
   provisions VPC, EKS cluster + managed node group, one RDS Postgres
   instance per service, and 3 encrypted S3 buckets (medical documents,
   reports, backups).
2. **Secrets**: populate AWS Secrets Manager at `medicore/<env>/<service>/*`;
   the External Secrets Operator (`infra/k8s/base/security/external-secrets.yaml`)
   syncs them into Kubernetes Secrets — nothing sensitive is ever committed.
3. **Deploy**: either `kubectl apply -k infra/k8s/overlays/<env>` or
   `helm install medicore infra/helm/medicore -f <env-values>`. In
   production, ArgoCD (`infra/argocd/medicore-prod.yaml`) manages sync from
   Git, with manual-approval-only for the production Application.
4. **CI/CD**: pushes to `develop`/`main` run `.github/workflows/ci-cd.yaml` —
   per-service test → SonarQube → Trivy (deps) → GitLeaks → Docker build →
   Trivy (image) → ECR push → environment deploy. Production deploys sit
   behind a GitHub Environment protection rule requiring manual approval.

## Security & compliance features implemented

- **Encryption at rest**: application-layer AES field encryption (patient
  PII, clinical notes, lab results) on top of KMS-backed RDS/S3 encryption.
- **Encryption in transit**: TLS termination at the ALB/Ingress; mTLS via
  service mesh is the natural next step for internal traffic.
- **Audit logging**: every read/write of Patient, MedicalRecordEntry, and
  Invoice resources emits a structured JSON audit event (`shared_common.audit`)
  shipped via Promtail → Loki, queryable in Grafana, and retained 90 days.
- **RBAC**: enforced per-endpoint via `shared_common.security.make_require_roles`,
  independently unit-tested per service.
- **Account protection**: bcrypt/argon2 password hashing, TOTP-based MFA,
  automatic lockout after repeated failed logins.
- **Kubernetes hardening**: default-deny NetworkPolicies with explicit
  allow rules, Pod Security Standards (`restricted`), Kyverno policies
  (non-root, no privileged containers, ECR-only images), IRSA per service.
- **Secrets management**: AWS Secrets Manager + External Secrets Operator;
  no plaintext secrets in Git or container images.

## What's intentionally stubbed for this portfolio scope

- Payment gateway and insurance-system integrations (`billing-service`)
  are modeled with the right interfaces but not wired to a real processor.
- Notification delivery (`notification-service`) logs instead of calling
  live AWS SES/SNS/FCM — swap in real credentials + boto3/firebase-admin
  calls in `app/services/senders.py` when ready.
- Event-driven architecture (Kafka/SQS) is described in the design but the
  current implementation uses direct service-to-service HTTP calls; the
  `_notify()` pattern in `appointment-service` is the natural seam to swap
  for an event bus.
- AI Medical Assistant, video consultations (WebRTC), and OpenSearch-backed
  full-text reporting are follow-on milestones per the original roadmap.

## License

Internal portfolio/reference project — no license granted for reuse.
