# Configure the MongoDB Atlas provider
provider "mongodbatlas" {
  public_key  = "<your public key>"
  private_key = "<your private key>"
}
print
# Define the MongoDB Atlas project and cluster
resource "mongodbatlas_project" "project" {
  org_id = "<your org ID>"
  name   = "my-project"
}

resource "mongodbatlas_cluster" "cluster" {
  project_id        = mongodbatlas_project.project.id
  name              = "my-cluster"
  num_shards        = 3
  replication_factor = 3

  # Specify the MongoDB version and instance size for each shard
  # This example uses MongoDB version 4.2 and AWS instance type M10
  provider_backup_enabled = true
  provider_instance_size_name = "M10"
  provider_disk_size_gb = 40
  provider_region_name = "US_EAST_1"
  provider_mdb_version = "4.2"

  # Enable VPC peering
  provider_vpc_peering_enabled = true
  provider_vpc_id = "<your VPC ID>"
  provider_vpc_region_name = "<your VPC region>"
  provider_vpc_peer_region_name = "us-east-1"
  provider_vpc_peer_account_id = "<your AWS account ID>"
  provider_vpc_peer_vpc_id = "<peer VPC ID>"
}

# Output the connection string for the MongoDB Atlas cluster
output "connection_string" {
  value = mongodbatlas_cluster.cluster.connection_string
}
