
 terraform {
   backend "s3" {
     bucket       = "vuln-bank-tfstate-910149519734-us-east-1"
     key          = "phase-5/terraform.tfstate"
     region       = "us-east-1"
     encrypt      = true
     use_lockfile = true
   }
 }
