terraform {
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 1.6.0" # Update to the latest version if needed
    }
  }
}

provider "mongodbatlas" {
  public_key = var.mongodb_atlas_public_key
  private_key = var.mongodb_atlas_private_key
}

variable "project_id" {
  description = "MongoDB Atlas Project ID"
  type        = string
}

variable "cluster_name" {
  default     = "terraform-example-cluster"
  description = "Name of the MongoDB Atlas cluster"
}

variable "gcp_region" {
  default     = "CENTRAL_US" # Update to your preferred GCP region
  description = "GCP region where the cluster will be deployed"
}

variable "private_link_vpc_name" {
  default     = "example-private-link-vpc"
  description = "VPC name for Private Link in GCP"
}

resource "mongodbatlas_cluster" "example_cluster" {
  project_id            = var.project_id
  name                  = var.cluster_name
  provider_name         = "GCP"
  backing_provider_name = "GCP"
  provider_region_name  = var.gcp_region

  cluster_type          = "REPLICASET"
  disk_size_gb          = 10
  num_shards            = 1
  replication_specs {
    num_shards = 1
    regions_config {
      region_name     = var.gcp_region
      electable_nodes = 3
      priority        = 7
    }
  }

  provider_instance_size_name = "M10" # Adjust size as needed
  auto_scaling_disk_gb_enabled = true
}

resource "mongodbatlas_private_endpoint" "gcp_private_link" {
  project_id     = var.project_id
  provider_name  = "GCP"
  region         = var.gcp_region
  endpoint_group_name = var.private_link_vpc_name
}

resource "mongodbatlas_network_container" "network_container" {
  project_id    = var.project_id
  atlas_cidr_block = "10.8.0.0/21" # Adjust CIDR as needed
  provider_name = "GCP"
  region_name   = var.gcp_region
}

resource "mongodbatlas_network_peering" "network_peering" {
  project_id          = var.project_id
  container_id        = mongodbatlas_network_container.network_container.container_id
  provider_name       = "GCP"
  gcp_project_id      = "<YOUR-GCP-PROJECT-ID>" # Replace with your GCP project ID
  network_name        = "<YOUR-GCP-NETWORK-NAME>" # Replace with your GCP VPC network name
  atlas_vpc_cidr_block = mongodbatlas_network_container.network_container.atlas_cidr_block
}

output "cluster_connection_string" {
  value = mongodbatlas_cluster.example_cluster.connection_strings.standard_srv
}
