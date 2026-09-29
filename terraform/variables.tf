variable "aws_region" {
  type        = string
  description = "Target AWS deployment region"
  default     = "us-east-1"
}

variable "project_name" {
  type        = string
  description = "Project name identifier for resource naming and tagging"
  default     = "vuln-bank"
}

variable "environment" {
  type        = string
  description = "Deployment lifecycle stage"
  default     = "dev"
}

variable "vpc_cidr" {
  type        = string
  description = "Primary CIDR block for the Virtual Private Cloud"
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  type        = list(string)
  description = "CIDR blocks for public subnets (must be 2 blocks across 2 AZs)"
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  type        = list(string)
  description = "CIDR blocks for private subnets (must be 2 blocks across 2 AZs)"
  default     = ["10.0.10.0/24", "10.0.20.0/24"]
}
