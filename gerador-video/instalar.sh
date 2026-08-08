#!/usr/bin/env bash
# Instalador da rota local (gratuita): voz XTTS-v2 + avatar SadTalker.
# Uso:  bash instalar.sh
# Idempotente — pode rodar de novo se algo falhar no meio.
# Windows: rode dentro do WSL (Ubuntu).

set -u
cd "$(dirname "$0")"
RAIZ="$(pwd)"

ok()   { printf '\033[32m✓ %s\033[0m\n' "$*"; }
info() { printf '\033[34m→ %s\033[0m\n' "$*"; }
erro() { printf '\033[31m✗ %s\033[0m\n' "$*"; exit 1; }

# ---------- pré-requisitos ----------
command -v git >/dev/null || erro "git não encontrado. Instale: sudo apt install git (ou brew install git)"
command -v ffmpeg >/dev/null || erro "ffmpeg não encontrado. Instale: sudo apt install ffmpeg (ou brew install ffmpeg)"

acha_python() { # devolve o primeiro python existente da lista
  for p in "$@"; do command -v "$p" >/dev/null && { echo "$p"; return; }; done
  echo ""
}
PY_VOZ=$(acha_python python3.11 python3.12 python3.10 python3)
PY_VID=$(acha_python python3.10 python3.11 python3.9 python3)
[ -n "$PY_VOZ" ] || erro "python3 não encontrado."
info "Python p/ voz: $PY_VOZ · p/ vídeo: $PY_VID"

# ---------- venv da voz (XTTS + servidor) ----------
if [ ! -x .venv-voz/bin/python ]; then
  info "Criando ambiente da voz (.venv-voz)…"
  "$PY_VOZ" -m venv .venv-voz || erro "falha ao criar venv (instale o pacote python3-venv)"
fi
info "Instalando Coqui TTS (XTTS-v2) — pode demorar, baixa o PyTorch…"
.venv-voz/bin/pip install -q --upgrade pip
.venv-voz/bin/pip install -q coqui-tts pyyaml requests anthropic \
  || .venv-voz/bin/pip install -q TTS pyyaml requests anthropic \
  || erro "não consegui instalar o Coqui TTS. Cole a mensagem acima na conversa que eu ajusto."
ok "Motor de voz instalado"

# ---------- SadTalker (avatar) ----------
mkdir -p motores
if [ ! -d motores/SadTalker ]; then
  info "Clonando SadTalker…"
  git clone -q --depth 1 https://github.com/OpenTalker/SadTalker motores/SadTalker
fi
if [ ! -x .venv-video/bin/python ]; then
  info "Criando ambiente do vídeo (.venv-video)…"
  "$PY_VID" -m venv .venv-video
fi
info "Instalando dependências do SadTalker (pesado: PyTorch + visão computacional)…"
.venv-video/bin/pip install -q --upgrade pip
if ! .venv-video/bin/pip install -q -r motores/SadTalker/requirements.txt 2>/tmp/sad_req.log; then
  info "Pins originais falharam neste Python; tentando versões atuais…"
  sed 's/[=<>].*//' motores/SadTalker/requirements.txt | grep -v '^\s*$' > /tmp/sad_req_livre.txt
  .venv-video/bin/pip install -q torch torchvision torchaudio
  .venv-video/bin/pip install -q -r /tmp/sad_req_livre.txt \
    || erro "dependências do SadTalker falharam. Envie /tmp/sad_req.log na conversa que eu ajusto."
fi
if [ ! -f motores/SadTalker/checkpoints/SadTalker_V0.0.2_256.safetensors ]; then
  info "Baixando modelos do SadTalker (~2,5 GB)…"
  ( cd motores/SadTalker && bash scripts/download_models.sh ) \
    || erro "download dos modelos falhou (rede?). Rode o instalador de novo."
fi
ok "Motor de avatar instalado"

# ---------- dataset ----------
if [ ! -f dataset/metadata.csv ]; then
  ZIP=$(ls -t "$HOME"/Downloads/dataset-avatar-*.zip 2>/dev/null | head -1)
  if [ -n "${ZIP:-}" ]; then
    info "Preparando dataset a partir de: $ZIP"
    .venv-voz/bin/python pipeline/preparar_dataset.py "$ZIP" --saida "$RAIZ/dataset" \
      || erro "preparo do dataset falhou — cole a saída na conversa."
    ok "Dataset preparado"
  else
    info "AVISO: não achei dataset-avatar-*.zip em ~/Downloads."
    info "Quando o download terminar, rode:  .venv-voz/bin/python pipeline/preparar_dataset.py ~/Downloads/dataset-avatar-*.zip --saida dataset"
  fi
else
  ok "Dataset já preparado"
fi

# ---------- config ----------
if [ ! -f pipeline/config.yaml ]; then
  cat > pipeline/config.yaml <<EOF
dataset: ../dataset
saida_dir: ../saida
voz:
  backend: xtts
video:
  backend: sadtalker
  sadtalker_dir: ../motores/SadTalker
  wav2lip_dir: ../motores/Wav2Lip
  python: ../.venv-video/bin/python
EOF
  ok "config.yaml criado"
fi

# ---------- pronto ----------
echo
ok "Instalação concluída!"
if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  info "Opcional: exporte ANTHROPIC_API_KEY para o botão 'Gerar roteiro com Claude'."
  info "Sem a chave, você escreve/cola o roteiro manualmente — o resto funciona igual."
fi
info "Abrindo o Estúdio de Geração…"
exec .venv-voz/bin/python pipeline/servidor.py
