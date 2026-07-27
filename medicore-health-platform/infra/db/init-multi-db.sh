#!/bin/bash
# Creates one database per microservice on container init, so
# docker-compose can approximate the "database-per-service" pattern using
# a single Postgres instance (production uses separate RDS instances).
set -e

for db in auth_db patient_db doctor_db appointment_db records_db billing_db notification_db reporting_db; do
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE $db;
EOSQL
done
