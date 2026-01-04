# FortifAI Infrastructure - Terraform

terraform {
  required_version = ">= 1.0.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket = "fortifai-terraform-state"
    key    = "infrastructure/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "FortifAI"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Variables
variable "aws_region" {
  description = "AWS region"
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  default     = "production"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  default     = "10.0.0.0/16"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "redis_auth_token" {
  description = "Redis authentication token"
  type        = string
  sensitive   = true
  default     = null
}

# VPC
module "vpc" {
  source = "./modules/vpc"
  
  cidr_block  = var.vpc_cidr
  environment = var.environment
}

# EKS Cluster
module "eks" {
  source = "./modules/eks"
  
  cluster_name              = "fortifai-${var.environment}"
  cluster_version           = "1.28"
  vpc_id                    = module.vpc.vpc_id
  subnet_ids                = module.vpc.private_subnet_ids
  node_group_desired_size   = 2
  node_group_min_size       = 1
  node_group_max_size       = 4
  node_group_instance_types = ["t3.medium"]
  
  tags = {
    Environment = var.environment
  }
}

# RDS PostgreSQL
module "rds" {
  source = "./modules/rds"
  
  identifier              = "fortifai-${var.environment}"
  db_name                 = "fortifai"
  db_username             = "fortifai_admin"
  db_password             = var.db_password
  vpc_id                  = module.vpc.vpc_id
  subnet_ids              = module.vpc.private_subnet_ids
  allowed_security_groups = [module.eks.cluster_security_group_id]
  instance_class          = "db.t3.medium"
  multi_az                = var.environment == "production"
  deletion_protection     = var.environment == "production"
  
  tags = {
    Environment = var.environment
  }
}

# ElastiCache Redis
module "elasticache" {
  source = "./modules/elasticache"
  
  cluster_id              = "fortifai-${var.environment}"
  vpc_id                  = module.vpc.vpc_id
  subnet_ids              = module.vpc.private_subnet_ids
  allowed_security_groups = [module.eks.cluster_security_group_id]
  node_type               = "cache.t3.medium"
  num_cache_nodes         = var.environment == "production" ? 2 : 1
  auth_token              = var.redis_auth_token
  
  tags = {
    Environment = var.environment
  }
}

# Outputs
output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "eks_cluster_arn" {
  description = "EKS cluster ARN"
  value       = module.eks.cluster_arn
}

output "rds_endpoint" {
  description = "RDS database endpoint"
  value       = module.rds.db_instance_endpoint
}

output "rds_connection_string" {
  description = "RDS connection string (without password)"
  value       = module.rds.connection_string
  sensitive   = true
}

output "redis_endpoint" {
  description = "Redis primary endpoint"
  value       = module.elasticache.primary_endpoint_address
}

output "redis_connection_string" {
  description = "Redis connection string"
  value       = module.elasticache.connection_string
  sensitive   = true
}
