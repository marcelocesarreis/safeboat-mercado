#!/usr/bin/env python3
"""Prepara o dataset exportado pelo estúdio para clonagem de voz e avatar.

Entrada:  o .zip exportado pelo estudio.html (ou a pasta já extraída).
Saída:    dataset/
            audio/<id>.wav          — 24 kHz mono, ideal para XTTS/F5-TTS
            metadata.csv            — formato LJSpeech: id|texto
            referencia/voz/*.wav    — melhores clipes para conditioning de voz
            referencia/rosto.png    — frame frontal neutro para o avatar
            referencia/rosto.mp4    — vídeo curto de referência (lip-sync/driving)

Requisitos: ffmpeg no PATH.

Uso:
  python preparar_dataset.py dataset-avatar-2026-08-06.zip --saida ../dataset
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

TAXA_AMOSTRAGEM = 24000  # esperada pelo XTTS-v2 e F5-TTS

# Clipes usados como referência de timbre (fala limpa e variada)
IDS_REFERENCIA_VOZ = ["p01", "p02", "p03", "s01", "v06", "c03"]
ID_ROSTO_NEUTRO = "f01"   # bloco visual: rosto neutro
ID_VIDEO_REFERENCIA = "f03"  # movimento de cabeça — bom driving video


def executar(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit(f"Comando falhou: {' '.join(cmd)}\n{proc.stderr[-2000:]}")


def verificar_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        sys.exit("ffmpeg não encontrado no PATH. Instale com: sudo apt install ffmpeg (ou brew install ffmpeg)")


def extrair_zip(origem: Path, destino: Path) -> Path:
    with zipfile.ZipFile(origem) as z:
        z.extractall(destino)
    return destino


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("entrada", type=Path, help=".zip exportado pelo estúdio, ou pasta extraída")
    ap.add_argument("--saida", type=Path, default=Path("../dataset"), help="pasta de saída")
    args = ap.parse_args()

    verificar_ffmpeg()

    tmp = None
    if args.entrada.suffix == ".zip":
        tmp = tempfile.mkdtemp(prefix="dataset-avatar-")
        raiz = extrair_zip(args.entrada, Path(tmp))
    else:
        raiz = args.entrada

    manifesto_path = raiz / "metadados.json"
    if not manifesto_path.exists():
        sys.exit(f"metadados.json não encontrado em {raiz} — exporte o dataset pelo estúdio.")
    manifesto = json.loads(manifesto_path.read_text(encoding="utf-8"))

    saida = args.saida
    dir_audio = saida / "audio"
    dir_ref_voz = saida / "referencia" / "voz"
    dir_ref = saida / "referencia"
    for d in (dir_audio, dir_ref_voz):
        d.mkdir(parents=True, exist_ok=True)

    linhas_metadata = []
    n_audio = 0

    for grav in manifesto["gravacoes"]:
        origem = raiz / grav["arquivo"]
        if not origem.exists():
            print(f"  aviso: {grav['arquivo']} listado mas ausente, pulando")
            continue

        if grav["tipo"] == "audio_video":
            # Texto limpo: remove marcadores de estilo como "[ENTUSIASMADO] "
            texto = grav["texto"]
            if texto.startswith("["):
                texto = texto.split("]", 1)[1].strip()

            wav = dir_audio / f"{grav['id']}.wav"
            executar([
                "ffmpeg", "-y", "-i", str(origem),
                "-vn", "-ac", "1", "-ar", str(TAXA_AMOSTRAGEM),
                # corta silêncio nas pontas, preservando a fala
                "-af", "silenceremove=start_periods=1:start_threshold=-45dB:stop_periods=1:stop_threshold=-45dB",
                str(wav),
            ])
            linhas_metadata.append(f"{grav['id']}|{texto}")
            n_audio += 1

            if grav["id"] in IDS_REFERENCIA_VOZ:
                shutil.copy(wav, dir_ref_voz / wav.name)

        if grav["id"] == ID_ROSTO_NEUTRO:
            # frame do meio do clipe como imagem de referência do rosto
            executar([
                "ffmpeg", "-y", "-i", str(origem),
                "-vf", "select=eq(n\\,30)", "-vframes", "1",
                str(dir_ref / "rosto.png"),
            ])

        if grav["id"] == ID_VIDEO_REFERENCIA:
            executar([
                "ffmpeg", "-y", "-i", str(origem),
                "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                str(dir_ref / "rosto.mp4"),
            ])

    (saida / "metadata.csv").write_text("\n".join(linhas_metadata) + "\n", encoding="utf-8")
    shutil.copy(manifesto_path, saida / "metadados.json")
    if tmp:
        shutil.rmtree(tmp)

    print(f"\n✓ Dataset preparado em {saida.resolve()}")
    print(f"  {n_audio} clipes de áudio a {TAXA_AMOSTRAGEM} Hz + metadata.csv")
    print(f"  Referências de voz: {len(list(dir_ref_voz.glob('*.wav')))} clipes")
    print(f"  Rosto: {'ok' if (dir_ref / 'rosto.png').exists() else 'FALTANDO (grave o item f01)'}")
    print(f"  Vídeo de referência: {'ok' if (dir_ref / 'rosto.mp4').exists() else 'FALTANDO (grave o item f03)'}")
    print("\nPróximo passo: python gerar_video.py --prompt \"...\"")


if __name__ == "__main__":
    main()
