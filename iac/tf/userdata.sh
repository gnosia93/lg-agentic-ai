#!/bin/bash
# userdata.sh
set -e
exec > /var/log/userdata.log 2>&1

echo "=== UserData Start ==="

apt-get update -y

# ============================================================
# 1. VS Code Server (code-server)
# ============================================================
sudo -u ubuntu -i bash -c '
curl -fsSL https://code-server.dev/install.sh | sh
mkdir -p /home/ubuntu/.config/code-server
cat > /home/ubuntu/.config/code-server/config.yaml <<EOF
bind-addr: 0.0.0.0:8080
auth: password
password: ${vscode_password}
cert: false
EOF
'

# ============================================================
# 2. Python 환경
# ============================================================
sudo -u ubuntu bash -c '
source /home/ubuntu/anaconda3/bin/activate
conda create -n gpu-dev python=3.11 -y
conda activate gpu-dev

pip install torch --index-url https://download.pytorch.org/whl/cu121
pip install jupyterlab ipykernel
python -m ipykernel install --user --name gpu-dev --display-name "gpu-dev"
pip install huggingface_hub
'

# ============================================================
# 3. VS Code 확장
# ============================================================
sudo -u ubuntu code-server \
  --install-extension ms-python.python \
  --install-extension ms-toolsai.jupyter \
  --install-extension ms-toolsai.jupyter-keymap \
  --install-extension ms-toolsai.jupyter-renderers

# ============================================================
# 4. VS Code 설정 (conda 환경 연결)
# ============================================================
mkdir -p /home/ubuntu/.local/share/code-server/User
cat <<EOF > /home/ubuntu/.local/share/code-server/User/settings.json
{
  "python.defaultInterpreterPath": "/home/ubuntu/anaconda3/envs/gpu-dev/bin/python",
  "jupyter.kernels.filter": [],
  "python.condaPath": "/home/ubuntu/anaconda3/bin/conda"
}
EOF

chown -R ubuntu:ubuntu /home/ubuntu
systemctl enable --now code-server@ubuntu

echo "=== UserData Complete ==="
