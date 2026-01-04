/**
 * ElastiCache Redis Module
 * Creates an Amazon ElastiCache Redis cluster for FortifAI caching and pub/sub
 */

variable "cluster_id" {
  description = "The ID of the ElastiCache cluster"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where the cluster will be created"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for the ElastiCache subnet group"
  type        = list(string)
}

variable "allowed_security_groups" {
  description = "List of security group IDs allowed to access Redis"
  type        = list(string)
  default     = []
}

variable "node_type" {
  description = "The compute and memory capacity of the nodes"
  type        = string
  default     = "cache.t3.medium"
}

variable "num_cache_nodes" {
  description = "The number of cache nodes in the cluster"
  type        = number
  default     = 1
}

variable "engine_version" {
  description = "The Redis engine version"
  type        = string
  default     = "7.0"
}

variable "port" {
  description = "The port number on which Redis accepts connections"
  type        = number
  default     = 6379
}

variable "parameter_group_family" {
  description = "The family of the parameter group"
  type        = string
  default     = "redis7"
}

variable "automatic_failover_enabled" {
  description = "Enable automatic failover (requires num_cache_nodes > 1)"
  type        = bool
  default     = false
}

variable "multi_az_enabled" {
  description = "Enable Multi-AZ (requires automatic_failover_enabled = true)"
  type        = bool
  default     = false
}

variable "at_rest_encryption_enabled" {
  description = "Enable encryption at rest"
  type        = bool
  default     = true
}

variable "transit_encryption_enabled" {
  description = "Enable encryption in transit"
  type        = bool
  default     = true
}

variable "auth_token" {
  description = "Password used to access Redis (required when transit_encryption_enabled = true)"
  type        = string
  sensitive   = true
  default     = null
}

variable "snapshot_retention_limit" {
  description = "Number of days for which ElastiCache will retain automatic snapshots"
  type        = number
  default     = 7
}

variable "snapshot_window" {
  description = "The daily time range during which automated backups are created"
  type        = string
  default     = "03:00-04:00"
}

variable "maintenance_window" {
  description = "Specifies the weekly time range for maintenance"
  type        = string
  default     = "sun:04:00-sun:05:00"
}

variable "notification_topic_arn" {
  description = "ARN of an SNS topic to send ElastiCache notifications"
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

# Subnet Group
resource "aws_elasticache_subnet_group" "main" {
  name        = "${var.cluster_id}-subnet-group"
  description = "Subnet group for ${var.cluster_id} ElastiCache cluster"
  subnet_ids  = var.subnet_ids

  tags = merge(var.tags, {
    Name = "${var.cluster_id}-subnet-group"
  })
}

# Security Group
resource "aws_security_group" "redis" {
  name        = "${var.cluster_id}-redis-sg"
  description = "Security group for ${var.cluster_id} ElastiCache Redis"
  vpc_id      = var.vpc_id

  tags = merge(var.tags, {
    Name = "${var.cluster_id}-redis-sg"
  })
}

# Ingress rules for allowed security groups
resource "aws_security_group_rule" "redis_ingress" {
  count                    = length(var.allowed_security_groups)
  type                     = "ingress"
  from_port                = var.port
  to_port                  = var.port
  protocol                 = "tcp"
  source_security_group_id = var.allowed_security_groups[count.index]
  security_group_id        = aws_security_group.redis.id
  description              = "Allow Redis access from security group"
}

# Egress rule
resource "aws_security_group_rule" "redis_egress" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.redis.id
}

# Parameter Group
resource "aws_elasticache_parameter_group" "main" {
  name   = "${var.cluster_id}-params"
  family = var.parameter_group_family

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  parameter {
    name  = "notify-keyspace-events"
    value = "Ex"
  }

  parameter {
    name  = "timeout"
    value = "300"
  }

  tags = var.tags
}

# Redis Replication Group (recommended over cache cluster for production)
resource "aws_elasticache_replication_group" "main" {
  replication_group_id = var.cluster_id
  description          = "Redis cluster for FortifAI"

  node_type            = var.node_type
  num_cache_clusters   = var.num_cache_nodes
  port                 = var.port
  parameter_group_name = aws_elasticache_parameter_group.main.name

  engine               = "redis"
  engine_version       = var.engine_version
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [aws_security_group.redis.id]

  automatic_failover_enabled = var.num_cache_nodes > 1 ? var.automatic_failover_enabled : false
  multi_az_enabled           = var.multi_az_enabled

  at_rest_encryption_enabled = var.at_rest_encryption_enabled
  transit_encryption_enabled = var.transit_encryption_enabled
  auth_token                 = var.transit_encryption_enabled ? var.auth_token : null

  snapshot_retention_limit = var.snapshot_retention_limit
  snapshot_window          = var.snapshot_window
  maintenance_window       = var.maintenance_window

  notification_topic_arn = var.notification_topic_arn

  auto_minor_version_upgrade = true

  # Apply changes immediately
  apply_immediately = true

  tags = var.tags
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "redis_cpu" {
  alarm_name          = "${var.cluster_id}-cpu-utilization"
  alarm_description   = "Redis cluster CPU utilization"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Average"
  threshold           = 75

  dimensions = {
    CacheClusterId = aws_elasticache_replication_group.main.id
  }

  alarm_actions = var.notification_topic_arn != null ? [var.notification_topic_arn] : []

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "redis_memory" {
  alarm_name          = "${var.cluster_id}-memory-utilization"
  alarm_description   = "Redis cluster memory utilization"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DatabaseMemoryUsagePercentage"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Average"
  threshold           = 80

  dimensions = {
    CacheClusterId = aws_elasticache_replication_group.main.id
  }

  alarm_actions = var.notification_topic_arn != null ? [var.notification_topic_arn] : []

  tags = var.tags
}

# Outputs
output "replication_group_id" {
  description = "The ID of the ElastiCache replication group"
  value       = aws_elasticache_replication_group.main.id
}

output "replication_group_arn" {
  description = "The ARN of the ElastiCache replication group"
  value       = aws_elasticache_replication_group.main.arn
}

output "primary_endpoint_address" {
  description = "The address of the primary endpoint"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
}

output "reader_endpoint_address" {
  description = "The address of the reader endpoint"
  value       = aws_elasticache_replication_group.main.reader_endpoint_address
}

output "port" {
  description = "The port number on which the cache cluster accepts connections"
  value       = var.port
}

output "security_group_id" {
  description = "The security group ID for the Redis cluster"
  value       = aws_security_group.redis.id
}

output "subnet_group_name" {
  description = "The name of the subnet group"
  value       = aws_elasticache_subnet_group.main.name
}

output "connection_string" {
  description = "Redis connection string"
  value       = "redis://${aws_elasticache_replication_group.main.primary_endpoint_address}:${var.port}"
  sensitive   = true
}
