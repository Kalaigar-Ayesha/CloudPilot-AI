provider "google" {
  project = var.project_id
  region  = "us-central1"
}

variable "project_id" {
  default = "cloudpilot-project"
}

resource "google_compute_network" "vpc" {
  name                    = "cloudpilot-gke-vpc"
  auto_create_subnetworks = "false"
}

resource "google_compute_subnetwork" "subnet" {
  name          = "cloudpilot-gke-subnet"
  region        = "us-central1"
  network       = google_compute_network.vpc.name
  ip_cidr_range = "10.10.0.0/24"
}

resource "google_container_cluster" "gke" {
  name     = "cloudpilot-gke-cluster"
  location = "us-central1"

  remove_default_node_pool = true
  initial_node_count       = 1

  network    = google_compute_network.vpc.name
  subnetwork = google_compute_subnetwork.subnet.name
}

resource "google_container_node_pool" "primary_nodes" {
  name       = "cloudpilot-nodes"
  location   = "us-central1"
  cluster    = google_container_cluster.gke.name
  node_count = 2

  node_config {
    preemptible  = true
    machine_type = "e2-medium"
  }
}

output "gke_cluster_name" {
  value = google_container_cluster.gke.name
}
