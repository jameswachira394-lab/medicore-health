terraform {
  backend "s3" {
    # Configure via -backend-config or a backend.hcl per environment, e.g.:
    #   terraform init -backend-config=backend.hcl
    # bucket = "medicore-terraform-state-staging"
    # key    = "medicore/staging/terraform.tfstate"
    # region = "us-east-1"
    # dynamodb_table = "medicore-terraform-locks"
    # encrypt = true
  }
}

provider "aws" {
  region = var.aws_region
}

module "vpc" {
  source = "../../modules/vpc"

  name                  = "medicore-staging"
  azs                   = var.azs
  public_subnet_cidrs   = var.public_subnet_cidrs
  private_subnet_cidrs  = var.private_subnet_cidrs
}

module "eks" {
  source = "../../modules/eks"

  name                = "medicore-staging"
  vpc_id              = module.vpc.vpc_id
  private_subnet_ids  = module.vpc.private_subnet_ids
  public_subnet_ids   = module.vpc.public_subnet_ids
  node_instance_types = var.node_instance_types
  node_desired_size   = var.node_desired_size
  node_min_size       = var.node_min_size
  node_max_size       = var.node_max_size
}

module "rds" {
  source = "../../modules/rds"

  name                        = "medicore-staging"
  vpc_id                      = module.vpc.vpc_id
  private_subnet_ids          = module.vpc.private_subnet_ids
  allowed_security_group_ids  = [module.eks.cluster_security_group_id]
  multi_az                    = var.rds_multi_az
  instance_class              = var.rds_instance_class
  database_names = [
    "auth-db", "patient-db", "doctor-db", "appointment-db",
    "records-db", "billing-db", "notification-db", "reporting-db",
  ]
}

module "s3_medical_documents" {
  source         = "../../modules/s3"
  name           = "medicore-staging"
  bucket_purpose = "medical-documents"
}

module "s3_reports" {
  source         = "../../modules/s3"
  name           = "medicore-staging"
  bucket_purpose = "reports"
}

module "s3_backups" {
  source         = "../../modules/s3"
  name           = "medicore-staging"
  bucket_purpose = "backups"
}
