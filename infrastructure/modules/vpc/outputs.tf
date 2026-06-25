output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "パブリックサブネット ID リスト（ALB に割り当て）"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "プライベートサブネット ID リスト（ECS / RDS に割り当て）"
  value       = aws_subnet.private[*].id
}

output "vpc_cidr_block" {
  description = "VPC CIDR ブロック（セキュリティグループの ingress で参照）"
  value       = aws_vpc.main.cidr_block
}
