#!/usr/bin/env python3
"""Gera um vídeo seu a partir de um prompt.

Fluxo:  prompt → roteiro (Claude) → áudio na sua voz clonada (TTS) → vídeo
        com seu rosto (lip-sync/avatar) → arquivo final .mp4

Uso:
  export ANTHROPIC_API_KEY=...
  python gerar_video.py --prompt "Vídeo de 40s explicando por que registrar a lancha na Capitania"
  python gerar_video.py --roteiro roteiro.txt          # pula a etapa do Claude
  python gerar_video.py --prompt "..." --so-roteiro    # só gera e mostra o roteiro

Configuração: copie config.exemplo.yaml para config.yaml e ajuste os backends.
"""

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml

AQUI = Path(__file__).parent
MODELO_CLAUDE = "claude-opus-5"

SYSTEM_ROTEIRISTA = """\
Você é roteirista de vídeos curtos falados em português brasileiro. Você escreve \
falas para UMA pessoa dizer olhando para a câmera, em primeira pessoa, com tom \
natural de conversa — nada de linguagem de texto escrito.

Regras:
- Devolva APENAS o texto a ser falado. Sem títulos, sem marcações de cena, sem \
"[pausa]", sem emojis, sem asteriscos.
- Frases curtas, ritmo de fala real. Escreva números por extenso (ex.: "um milhão \
e cem mil", nunca "1.100.000"), pois o texto vai direto para síntese de voz.
- Evite siglas soletradas; se necessário, escreva como se pronuncia.
- Respeite a duração pedida: fala natural rende cerca de 140 palavras por minuto.
- Comece já no assunto (sem "olá pessoal" a menos que pedido) e termine com um \
fechamento natural, sem "não esqueça de curtir" a menos que pedido.
"""


def carregar_config() -> dict:
    for nome in ("config.yaml", "config.exemplo.yaml"):
        p = AQUI / nome
        if p.exists():
            return yaml.safe_load(p.read_text(encoding="utf-8"))
    sys.exit("Nenhum config.yaml encontrado em pipeline/.")


# ---------------------------------------------------------------- roteiro
def gerar_roteiro(prompt: str) -> str:
    import anthropic

    client = anthropic.Anthropic()
    resp = client.beta.messages.create(
        model=MODELO_CLAUDE,
        max_tokens=4096,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=SYSTEM_ROTEIRISTA,
        messages=[{"role": "user", "content": prompt}],
    )
    if resp.stop_reason == "refusal":
        sys.exit("O modelo recusou o pedido de roteiro. Reformule o prompt.")
    texto = "".join(b.text for b in resp.content if b.type == "text").strip()
    if not texto:
        sys.exit("Roteiro vazio — verifique o prompt.")
    return texto


# ---------------------------------------------------------------- voz (TTS)
def sintetizar_voz(texto: str, cfg: dict, saida: Path) -> None:
    backend = cfg["voz"]["backend"]
    if backend == "xtts":
        _tts_xtts(texto, cfg, saida)
    elif backend == "elevenlabs":
        _tts_elevenlabs(texto, cfg, saida)
    else:
        sys.exit(f"Backend de voz desconhecido: {backend}")


def _tts_xtts(texto: str, cfg: dict, saida: Path) -> None:
    """XTTS-v2 (Coqui TTS) — local, gratuito. pip install TTS. Clona a voz
    a partir dos wavs de referência gerados por preparar_dataset.py."""
    try:
        from TTS.api import TTS  # type: ignore
    except ImportError:
        sys.exit("Instale o Coqui TTS: pip install TTS  (requer Python <=3.11)")

    refs = sorted(Path(cfg["dataset"]).joinpath("referencia/voz").glob("*.wav"))
    if not refs:
        sys.exit("Sem wavs de referência — rode preparar_dataset.py primeiro.")

    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
    tts.tts_to_file(
        text=texto,
        speaker_wav=[str(r) for r in refs],
        language="pt",
        file_path=str(saida),
    )


def _tts_elevenlabs(texto: str, cfg: dict, saida: Path) -> None:
    """ElevenLabs — API paga, melhor qualidade. Crie a voz clonada uma vez no
    painel deles (upload dos wavs de referencia/voz) e informe voice_id no config."""
    import requests

    chave = os.environ.get("ELEVENLABS_API_KEY")
    if not chave:
        sys.exit("Defina ELEVENLABS_API_KEY no ambiente.")
    voice_id = cfg["voz"].get("elevenlabs_voice_id")
    if not voice_id:
        sys.exit("Defina voz.elevenlabs_voice_id no config.yaml.")

    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={"xi-api-key": chave},
        json={"text": texto, "model_id": "eleven_multilingual_v2",
              "voice_settings": {"stability": 0.5, "similarity_boost": 0.8}},
        timeout=300,
    )
    r.raise_for_status()
    saida.write_bytes(r.content)


# ---------------------------------------------------------------- vídeo (avatar)
def gerar_avatar(audio: Path, cfg: dict, saida: Path) -> None:
    backend = cfg["video"]["backend"]
    if backend == "sadtalker":
        _video_sadtalker(audio, cfg, saida)
    elif backend == "wav2lip":
        _video_wav2lip(audio, cfg, saida)
    else:
        sys.exit(f"Backend de vídeo desconhecido: {backend}")


def _video_sadtalker(audio: Path, cfg: dict, saida: Path) -> None:
    """SadTalker — gera cabeça falante a partir de UMA foto + áudio.
    Clone https://github.com/OpenTalker/SadTalker e aponte video.sadtalker_dir."""
    sad_dir = Path(cfg["video"]["sadtalker_dir"]).expanduser()
    rosto = Path(cfg["dataset"]) / "referencia" / "rosto.png"
    if not sad_dir.exists():
        sys.exit(f"SadTalker não encontrado em {sad_dir} — clone o repositório e ajuste o config.")
    if not rosto.exists():
        sys.exit("referencia/rosto.png ausente — grave o item f01 e rode preparar_dataset.py.")

    tmp_out = saida.parent / "sadtalker_out"
    proc = subprocess.run(
        [sys.executable, "inference.py",
         "--driven_audio", str(audio.resolve()),
         "--source_image", str(rosto.resolve()),
         "--result_dir", str(tmp_out.resolve()),
         "--preprocess", "full", "--still", "--enhancer", "gfpgan"],
        cwd=sad_dir, capture_output=True, text=True,
    )
    if proc.returncode != 0:
        sys.exit(f"SadTalker falhou:\n{proc.stderr[-3000:]}")
    gerados = sorted(tmp_out.rglob("*.mp4"), key=lambda p: p.stat().st_mtime)
    if not gerados:
        sys.exit("SadTalker não produziu vídeo.")
    shutil.move(str(gerados[-1]), str(saida))


def _video_wav2lip(audio: Path, cfg: dict, saida: Path) -> None:
    """Wav2Lip — sincroniza lábios sobre um VÍDEO seu real (referencia/rosto.mp4).
    Resultado mais 'você' que foto animada. Clone https://github.com/Rudrabha/Wav2Lip."""
    w2l_dir = Path(cfg["video"]["wav2lip_dir"]).expanduser()
    base = Path(cfg["dataset"]) / "referencia" / "rosto.mp4"
    if not w2l_dir.exists():
        sys.exit(f"Wav2Lip não encontrado em {w2l_dir}.")
    if not base.exists():
        sys.exit("referencia/rosto.mp4 ausente — grave o item f03 e rode preparar_dataset.py.")

    proc = subprocess.run(
        [sys.executable, "inference.py",
         "--checkpoint_path", "checkpoints/wav2lip_gan.pth",
         "--face", str(base.resolve()),
         "--audio", str(audio.resolve()),
         "--outfile", str(saida.resolve())],
        cwd=w2l_dir, capture_output=True, text=True,
    )
    if proc.returncode != 0:
        sys.exit(f"Wav2Lip falhou:\n{proc.stderr[-3000:]}")


# ---------------------------------------------------------------- finalização
def finalizar(video: Path, audio: Path, saida: Path) -> None:
    """Remuxa com o áudio em AAC e garante compatibilidade ampla."""
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(video), "-i", str(audio),
         "-map", "0:v", "-map", "1:a",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
         "-c:a", "aac", "-b:a", "192k", "-shortest", str(saida)],
        check=True, capture_output=True,
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    grupo = ap.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--prompt", help="o que o vídeo deve dizer, em linguagem natural")
    grupo.add_argument("--roteiro", type=Path, help="arquivo .txt com o roteiro pronto")
    ap.add_argument("--so-roteiro", action="store_true", help="gera só o roteiro e para")
    ap.add_argument("--saida", type=Path, help="arquivo .mp4 final")
    args = ap.parse_args()

    cfg = carregar_config()
    carimbo = datetime.now().strftime("%Y%m%d-%H%M%S")
    trabalho = Path(cfg.get("saida_dir", "saida")) / carimbo
    trabalho.mkdir(parents=True, exist_ok=True)

    # 1. roteiro
    if args.roteiro:
        texto = args.roteiro.read_text(encoding="utf-8").strip()
    else:
        print("① Gerando roteiro com Claude…")
        texto = gerar_roteiro(args.prompt)
    (trabalho / "roteiro.txt").write_text(texto + "\n", encoding="utf-8")
    print(f"\n--- ROTEIRO ---\n{texto}\n---------------\n")
    if args.so_roteiro:
        print(f"Roteiro salvo em {trabalho/'roteiro.txt'}")
        return

    # 2. voz
    print(f"② Sintetizando sua voz ({cfg['voz']['backend']})…")
    audio = trabalho / "voz.wav"
    sintetizar_voz(texto, cfg, audio)

    # 3. avatar
    print(f"③ Gerando vídeo do avatar ({cfg['video']['backend']})…")
    bruto = trabalho / "avatar_bruto.mp4"
    gerar_avatar(audio, cfg, bruto)

    # 4. mux final
    final = args.saida or (trabalho / "video_final.mp4")
    print("④ Finalizando…")
    finalizar(bruto, audio, final)
    print(f"\n✓ Vídeo pronto: {final.resolve()}")
    print("Lembrete: identifique o vídeo como gerado por IA ao publicar.")


if __name__ == "__main__":
    main()
