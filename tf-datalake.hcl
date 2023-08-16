provider "mongodbatlas" {
  public_key   = "YOUR_PUBLIC_KEY"
  private_key  = "YOUR_PRIVATE_KEY"
}

resource "mongodbatlas_project" "example" {
  org_id   = "YOUR_ORG_ID"
  name     = "example-project"
}

resource "mongodbatlas_cluster" "example" {
  project_id     = mongodbatlas_project.example.id
  name           = "example-cluster"
  provider_name  = "AWS"
  tier           = "M10"
  cluster_type   = "REPLICASET"
  num_shards     = 1

  auto_scaling_disk_gb_enabled = true
  auto_scaling_compute_enabled = true

  replication_specs {
    num_shards = 1
  }
}

resource "mongodbatlas_data_lake" "example" {
  project_id   = mongodbatlas_project.example.id
  name         = "example-data-lake"
  data_lake_config {
    bucket_name          = "my-data-lake-bucket"
    bucket_prefix        = "data-lake-prefix/"
    read_only_role_name  = "AtlasAdmin"
  }
}
