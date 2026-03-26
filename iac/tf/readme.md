### VPC 아키텍처 ###
![](https://github.com/gnosia93/training-on-eks/blob/main/appendix/images/terraform-vpc.png)
* VPC
* Subnets (Public / Private)
* Graviton EC2 for Code-Server
* Security Groups
* S3 bucket 

### [테라폼 설치](https://developer.hashicorp.com/terraform/install) ###
mac 의 경우 아래의 명령어로 설치할 수 있다. 
```
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
```

### VPC 생성 ###
테라폼으로 VPC 및 접속용 vs-code EC2 인스턴스를 생성한다.   
```
git pull https://github.com/gnosia93/training-on-eks.git
cd training-on-eks/tf
terraform init
```
[결과]
```
Initializing the backend...
Initializing provider plugins...
- Finding latest version of hashicorp/aws...
- Finding latest version of hashicorp/http...
- Installing hashicorp/aws v6.27.0...
- Installed hashicorp/aws v6.27.0 (signed by HashiCorp)
- Installing hashicorp/http v3.5.0...
- Installed hashicorp/http v3.5.0 (signed by HashiCorp)
Terraform has created a lock file .terraform.lock.hcl to record the provider
selections it made above. Include this file in your version control repository
so that Terraform can guarantee to make the same selections by default when
you run "terraform init" in the future.

Terraform has been successfully initialized!

You may now begin working with Terraform. Try running "terraform plan" to see
any changes that are required for your infrastructure. All Terraform commands
should now work.

If you ever set or change modules or backend configuration for Terraform,
rerun this command to reinitialize your working directory. If you forget, other
commands will detect it and remind you to do so if necessary.
```
VPC 를 생성한다. 
```
terraform apply -auto-approve
```

### Karpenter 설치 ###
```
Karpenter 자체는 Helm으로 설치합니다 (Terraform apply 후):

# kubeconfig 설정
aws eks update-kubeconfig --name ${var.cluster_name}

# Karpenter 설치
helm install karpenter oci://public.ecr.aws/karpenter/karpenter \
  --namespace karpenter --create-namespace \
  --set settings.clusterName=${var.cluster_name} \
  --set settings.clusterEndpoint=$(aws eks describe-cluster --name ${var.cluster_name} --query "cluster.endpoint" --output text) \
  --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=${karpenter_role_arn}
variables.tf에 cluster_name 변수가 이미 있으니 그대로 쓰면 됩니다.
```

### VPC 삭제 ###
워크샵과 관련된 리소스를 모두 삭제한다.
```
terraform destroy --auto-approve
```

### TOE_EKS_EC2_Role 삭제 ###
```
aws iam remove-role-from-instance-profile \
    --instance-profile-name EKS_Creator_Profile \
    --role-name TOE_EKS_EC2_Role

aws iam delete-instance-profile --instance-profile-name EKS_Creator_Profile

aws iam detach-role-policy \
    --role-name TOE_EKS_EC2_Role \
    --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

aws iam delete-role --role-name TOE_EKS_EC2_Role
```
