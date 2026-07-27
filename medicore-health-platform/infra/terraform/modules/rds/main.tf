variable "name" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "allowed_security_group_ids" {
  type    = list(string)
  default = []
}

variable "engine_version" {
  type    = string
  default = "16.3"
}

variable "instance_class" {
  type    = string
  default = "db.t3.medium"
}

variable "allocated_storage" {
  type    = number
  default = 100
}

variable "multi_az" {
  type    = bool
  default = true
}

variable "database_names" {
  description = "One RDS instance is provisioned per entry, implementing database-per-service isolation."
  type        = list(string)
}

variable "master_username" {
  type    = string
  default = "medicore_admin"
}

resource "aws_db_subnet_group" "this" {
  name       = "${var.name}-db-subnets"
  subnet_ids = var.private_subnet_ids
  tags       = { Name = "${var.name}-db-subnets" }
}

resource "aws_security_group" "rds" {
  name        = "${var.name}-rds-sg"
  description = "Allow Postgres access from EKS worker nodes only"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = var.allowed_security_group_ids
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.name}-rds-sg" }
}

resource "aws_kms_key" "rds" {
  description             = "KMS key for RDS encryption at rest (${var.name})"
  deletion_window_in_days = 30
  enable_key_rotation     = true
}

resource "random_password" "master" {
  for_each = toset(var.database_names)
  length   = 32
  special  = false
}

# One Multi-AZ Postgres instance per microservice database, per the
# "database-per-service" isolation requirement in the architecture doc.
resource "aws_db_instance" "this" {
  for_each = toset(var.database_names)

  identifier     = "${var.name}-${each.value}"
  engine         = "postgres"
  engine_version = var.engine_version
  instance_class = var.instance_class

  allocated_storage     = var.allocated_storage
  storage_encrypted     = true
  kms_key_id            = aws_kms_key.rds.arn
  db_subnet_group_name  = aws_db_subnet_group.this.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  db_name  = replace(each.value, "-", "_")
  username = var.master_username
  password = random_password.master[each.value].result

  multi_az                  = var.multi_az
  backup_retention_period   = 14
  backup_window              = "03:00-04:00"
  maintenance_window          = "mon:04:30-mon:05:30"
  deletion_protection        = true
  copy_tags_to_snapshot       = true
  auto_minor_version_upgrade = true
  skip_final_snapshot        = false
  final_snapshot_identifier  = "${var.name}-${each.value}-final"

  tags = { Name = "${var.name}-${each.value}", Service = each.value }
}

output "endpoints" {
  value = { for k, v in aws_db_instance.this : k => v.endpoint }
}

output "rds_security_group_id" {
  value = aws_security_group.rds.id
}
