# ---------------------------------------------------
# Security Group for FSx Lustre
# ---------------------------------------------------
resource "aws_security_group" "fsx_lustre" {
  name        = "fsx-sg"
  description = "FSx Lustre access"
  vpc_id      = aws_vpc.main.id
}

# EFA는 all-traffic self-reference 필요 (ingress + egress 모두)
resource "aws_security_group_rule" "fsx_self_ingress_all" {
  type              = "ingress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  security_group_id = aws_security_group.fsx_lustre.id
  self              = true
  description       = "EFA all traffic self"
}

resource "aws_security_group_rule" "fsx_self_egress_all" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  security_group_id = aws_security_group.fsx_lustre.id
  self              = true
  description       = "EFA all traffic self"
}

# EKS 노드 → FSx (all)
resource "aws_security_group_rule" "eks_to_fsx_all" {
  type                     = "ingress"
  from_port                = 0
  to_port                  = 0
  protocol                 = "-1"
  security_group_id        = aws_security_group.fsx_lustre.id
  source_security_group_id = aws_eks_cluster.main.vpc_config[0].cluster_security_group_id
  description              = "EKS nodes to FSx (EFA enabled)"
}

# FSx → EKS 노드 (all, 반대 방향)
resource "aws_security_group_rule" "fsx_to_eks_all" {
  type                     = "ingress"
  from_port                = 0
  to_port                  = 0
  protocol                 = "-1"
  security_group_id        = aws_eks_cluster.main.vpc_config[0].cluster_security_group_id
  source_security_group_id = aws_security_group.fsx_lustre.id
  description              = "FSx to EKS nodes (EFA enabled)"
}

# ---------------------------------------------------
# FSx for Lustre File System
# ---------------------------------------------------
resource "aws_fsx_lustre_file_system" "llama_cache" {
  storage_capacity                = 4800           # EFA + 1000 MB/s tier: min/multiples 4800 GiB
  subnet_ids                      = [aws_subnet.private[0].id]   # private subnet 첫 번째
  security_group_ids              = [aws_security_group.fsx_lustre.id]
  deployment_type                 = "PERSISTENT_2"
  per_unit_storage_throughput     = 1000
  file_system_type_version        = "2.15"
  data_compression_type           = "LZ4"
  storage_type                    = "SSD"
  efa_enabled                     = true
  automatic_backup_retention_days = 0

  tags = {
    Name    = "eai-fsx"
    Cluster = "eks-agentic-ai"
  }
}

# ---------- Outputs ----------
output "fsx_id" {
  value = aws_fsx_lustre_file_system.llama_cache.id
}

output "fsx_dns_name" {
  value = aws_fsx_lustre_file_system.llama_cache.dns_name
}

output "fsx_mount_name" {
  value = aws_fsx_lustre_file_system.llama_cache.mount_name
}

output "fsx_security_group_id" {
  value = aws_security_group.fsx_lustre.id
}

# kubectl apply 해서 바로 쓸 수 있는 PV/PVC 매니페스트
output "fsx_pv_manifest" {
  value = <<-EOT
    ---
    apiVersion: v1
    kind: PersistentVolume
    metadata:
      name: llama-405b-cache-pv
    spec:
      capacity:
        storage: ${aws_fsx_lustre_file_system.llama_cache.storage_capacity}Gi
      accessModes:
        - ReadWriteMany
      mountOptions:
        - flock
      persistentVolumeReclaimPolicy: Retain
      csi:
        driver: fsx.csi.aws.com
        volumeHandle: ${aws_fsx_lustre_file_system.llama_cache.id}
        volumeAttributes:
          dnsname: ${aws_fsx_lustre_file_system.llama_cache.dns_name}
          mountname: ${aws_fsx_lustre_file_system.llama_cache.mount_name}
    ---
    apiVersion: v1
    kind: PersistentVolumeClaim
    metadata:
      name: llama-405b-cache
      namespace: llm-serving
    spec:
      accessModes:
        - ReadWriteMany
      storageClassName: ""
      volumeName: llama-405b-cache-pv
      resources:
        requests:
          storage: ${aws_fsx_lustre_file_system.llama_cache.storage_capacity}Gi
  EOT
}
