#!/bin/bash
# userdata.sh
set -e                                     # 에러 나면, 즉시 중단
exec > /var/log/userdata.log 2>&1          # 프로세스 교체 없이, 현재 셸의 출력만 변경

# ============================================
# apt/dpkg 락 대기 (필수)
# ============================================
echo "=== Waiting for apt/dpkg locks ==="
for i in {1..60}; do
  if ! fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 && \
     ! fuser /var/lib/dpkg/lock >/dev/null 2>&1 && \
     ! fuser /var/lib/apt/lists/lock >/dev/null 2>&1; then
    echo "locks released after ${i}x5s"
    break
  fi
  echo "  [$i/60] still locked, sleeping 5s..."
  sleep 5
done


# ============================================================
# 1. VS Code Server (code-server)
# ============================================================
sudo -u ubuntu -i <<'EC2_USER_SCRIPT'
echo "=== UserData Start 1 ==="
curl -fsSL https://code-server.dev/install.sh | sh && sudo systemctl enable --now code-server@ubuntu
sleep 5
sed -i 's/127.0.0.1:8080/0.0.0.0:9090/g; s/^password: .*/password: code!@#c/g' /home/ubuntu/.config/code-server/config.yaml
EC2_USER_SCRIPT

# ============================================================
# 2. Python 환경
# ============================================================
echo "=== UserData Start 2 ==="
sudo -u ubuntu -i <<'PYTHON_SETUP'
wget https://repo.anaconda.com/archive/Anaconda3-2025.12-2-Linux-x86_64.sh
bash Anaconda3-2025.12-2-Linux-x86_64.sh -b -p /home/ubuntu/anaconda3
/home/ubuntu/anaconda3/bin/conda init bash
source ~/.bashrc
conda --version

#pip install torch --index-url https://download.pytorch.org/whl/cu121
pip install jupyterlab ipykernel
python -m ipykernel install --user --name gpu-dev --display-name "gpu-dev"
pip install huggingface_hub
PYTHON_SETUP

# ============================================================
# 3. VS Code 확장
# ============================================================
echo "=== UserData Start 3 ==="
sudo -u ubuntu -i code-server \
  --install-extension ms-python.python \
  --install-extension ms-toolsai.jupyter \
  --install-extension ms-toolsai.jupyter-keymap \
  --install-extension ms-toolsai.jupyter-renderers

# ============================================================
# 4. VS Code 설정 (conda 환경 연결)
# ============================================================
echo "=== UserData Start 4 ==="
sudo -u ubuntu -i <<'VSCODE_SETTINGS'
mkdir -p /home/ubuntu/.local/share/code-server/User
cat > /home/ubuntu/.local/share/code-server/User/settings.json <<EOF
{
  "python.defaultInterpreterPath": "/home/ubuntu/anaconda3/envs/gpu-dev/bin/python",
  "jupyter.kernels.filter": [],
  "python.condaPath": "/home/ubuntu/anaconda3/bin/conda"
}
EOF
VSCODE_SETTINGS

systemctl restart code-server@ubuntu
echo "=== UserData Complete ==="
