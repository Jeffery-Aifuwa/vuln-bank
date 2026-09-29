# Phase 5: Cloud Infrastructure as Code (IaC) Foundation

## Phase Objective
Define, parameterize, validate, plan, and deploy a secure, cost-controlled AWS infrastructure baseline using Terraform (>= 1.10.0). The scope includes a multi-AZ VPC, public/private subnets, tiered security groups, an Amazon ECR repository with AWS-native basic scanning, and an encrypted remote state storage configuration with native S3 state locking (`use_lockfile = true`).

## Plain English Summary
We used Terraform to write and deploy the code that creates our AWS cloud foundation instead of configuring resources manually in the AWS Console. We established an isolated network with public subnets for our load balancer and private subnets for our application and database tiers. We created firewall rules ensuring our database only accepts traffic from the application tier, a private container registry to store our hardened Docker images with automated scanning on push, and a secure S3 bucket with native state locking to track our Terraform state without needing DynamoDB. To keep ongoing costs strictly controlled, paid resources like NAT Gateways were deliberately excluded. All configuration was formatted, validated, planned, and applied in three controlled stages (targeted S3 bootstrap, backend migration, and core infrastructure apply).

## Technical Explanation
Infrastructure as Code establishes deterministic, auditable, and repeatable cloud environments. In Phase 5, Terraform manifests were organized under `terraform/` using the HashiCorp AWS provider (~> 5.0) to model our network, security perimeter, container registry, and state storage tiers.

1. **Network Topology & Segmentation:**
   * **VPC:** `10.0.0.0/16` (`vpc-026cb2c60aff29eb6`) with DNS support and DNS hostnames enabled.
   * **Multi-AZ Dual-Tier Subnets:** Two public subnets (`subnet-0335fae401a6beb87` [10.0.1.0/24], `subnet-061e13aaed7697e1a` [10.0.2.0/24]) spanning `us-east-1a` and `us-east-1b` mapped with public IPs on launch, and two private subnets (`subnet-0cdfee20e437881d0` [10.0.10.0/24], `subnet-0ba2b37bc074d2f2b` [10.0.20.0/24]) with public IPs disabled.
   * **Route Isolation:** Public route table points `0.0.0.0/0` to the Internet Gateway. The private route table contains only local VPC routes. NAT Gateways are explicitly omitted for cost control.
2. **Defense-in-Depth Tiered Security Groups:**
   * `alb-sg` (`sg-020ee6533f5d8bc2d`): Allows inbound TCP 80/443 from `0.0.0.0/0` and `::/0`; unrestricted egress.
   * `app-sg` (`sg-05f803c061ea785b2`): Restricts inbound TCP 5000 strictly to traffic originating from `alb-sg`. Direct public ingress is denied.
   * `db-sg` (`sg-05731dd81ab620a43`): Restricts inbound TCP 5432 strictly to traffic originating from `app-sg`. Egress is constrained to the internal VPC CIDR (`10.0.0.0/16`).
3. **Artifact Registry (Amazon ECR):**
   * Private repository `vuln-bank-web` (`910149519734.dkr.ecr.us-east-1.amazonaws.com/vuln-bank-web`) configured with `image_tag_mutability = "MUTABLE"` to support active development builds.
   * AWS-native ECR Basic Scanning on push (`scan_on_push = true`) for vulnerability discovery.
   * Server-side encryption enabled (AES256).
   * ECR Lifecycle Policy expiring untagged images older than 14 days and capping tagged images at 30 to control storage footprint.
4. **Remote State Architecture:**
   * S3 Bucket: `vuln-bank-tfstate-910149519734-us-east-1` with Versioning enabled and AES256 server-side encryption.
   * Access Controls: S3 Public Access Block fully enabled (all 4 flags) and a bucket policy explicitly denying non-HTTPS transport (`aws:SecureTransport = "false"`).
   * State Locking: Configured for S3 native object-locking (`use_lockfile = true`), eliminating the requirement and cost of an Amazon DynamoDB locking table.

## Architecture & Design Decisions
* **S3 Native State Locking:** Terraform v1.10+ supports native conditional writes on S3, deprecating the need for separate DynamoDB tables for state locking.
* **Tag Mutability:** Configured as `MUTABLE` to prevent CI build failures during continuous integration when pushing feature tags, while managing retention via automated lifecycle policies.
* **AWS-Native Basic Scanning:** Leveraged built-in basic scanning to avoid the per-scan fee structure of AWS Inspector v2 (Enhanced Scanning).
* **Strict Cost Controls:** Omitted NAT Gateways (saving ~$32.40/month per AZ) and leveraged AWS Free Tier-eligible resource configurations.
* **Three-Stage Rollout:** Bootstrapped the S3 bucket with targeted local execution, migrated the state backend to S3, and applied the remaining 17 infrastructure resources cleanly into the remote state.

## Files Created
* `terraform/versions.tf`
* `terraform/variables.tf`
* `terraform/terraform.tfvars`
* `terraform/main.tf`
* `terraform/vpc.tf`
* `terraform/security_groups.tf`
* `terraform/ecr.tf`
* `terraform/state_storage.tf`
* `terraform/backend.tf`
* `terraform/outputs.tf`
* `docs/05-terraform-iac-foundation.md`

## Provisioned Resource Identifiers
| Resource Identifier | Value |
|---|---|
| **VPC ID** | `vpc-026cb2c60aff29eb6` |
| **VPC CIDR** | `10.0.0.0/16` |
| **Public Subnet 1 (us-east-1a)** | `subnet-0335fae401a6beb87` |
| **Public Subnet 2 (us-east-1b)** | `subnet-061e13aaed7697e1a` |
| **Private Subnet 1 (us-east-1a)** | `subnet-0cdfee20e437881d0` |
| **Private Subnet 2 (us-east-1b)** | `subnet-0ba2b37bc074d2f2b` |
| **ALB Security Group** | `sg-020ee6533f5d8bc2d` |
| **App Workload Security Group** | `sg-05f803c061ea785b2` |
| **Database Security Group** | `sg-05731dd81ab620a43` |
| **ECR Repository URL** | `910149519734.dkr.ecr.us-east-1.amazonaws.com/vuln-bank-web` |
| **S3 State Bucket** | `vuln-bank-tfstate-910149519734-us-east-1` |

## Verification Performed & Results
* **Format Check:** `terraform fmt -check -diff` executed with zero formatting diffs.
* **Initialization:** `terraform init` installed hashicorp/aws v5.x provider cleanly.
* **Validation:** `terraform validate` returned `Success! The configuration is valid.`
* **Bootstrap Apply:** 5 resources added (`aws_s3_bucket.state`, `aws_s3_bucket_versioning.state`, `aws_s3_bucket_server_side_encryption_configuration.state`, `aws_s3_bucket_public_access_block.state`, `aws_s3_bucket_policy.enforce_tls`).
* **State Migration:** `terraform init -migrate-state` successfully copied local state to `s3://vuln-bank-tfstate-910149519734-us-east-1/phase-5/terraform.tfstate`.
* **Core Apply:** 17 resources added, 0 changed, 0 destroyed. Total provisioned: 22 resources.

## Warnings & Unexpected Findings
* Neither `tfsec` nor `checkov` was installed on the local workstation. IaC static scanning should be integrated into the GitHub Actions CI pipeline for automated enforcement.
* Credential resolution required handling newer AWS CLI profile sessions; passing the profile explicitly or exporting temporary session environment variables resolved the provider authentication cleanly.

## How This Phase Connects to the Next Phase
The provisioned VPC, subnets, security groups, and ECR repository will serve as the host infrastructure for **Phase 6: Cloud Native Deployment**. In Phase 6, we will push our hardened container image to the ECR repository URL (`910149519734.dkr.ecr.us-east-1.amazonaws.com/vuln-bank-web`), evaluate compute hosting (ECS Fargate vs. EC2) based on IAM permissions, and provision the application workloads and PostgreSQL RDS instance.