#!/usr/bin/env python3
"""Estúdio de Geração — servidor local.

Sobe uma interface no navegador onde você digita um prompt e recebe o vídeo
pronto (roteiro → voz clonada → avatar → mp4). Roda tudo localmente.

Uso:
  python servidor.py            # abre em http://localhost:8199
"""

import json
import threading
import webbrowser
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import gerar_video as gv

PORTA = 8199
AQUI = Path(__file__).parent
RAIZ = AQUI.parent  # gerador-video/

ESTADO = {
    "ocupado": False,
    "etapa": "",          # roteiro | voz | avatar | finalizando | pronto | erro
    "detalhe": "",
    "erro": None,
    "video": None,        # URL relativa do mp4 final
    "iniciado_em": None,
}
TRAVA = threading.Lock()


def _reset_estado():
    ESTADO.update(ocupado=True, etapa="", detalhe="", erro=None, video=None,
                  iniciado_em=datetime.now().isoformat(timespec="seconds"))


def trabalho_gerar(roteiro: str) -> None:
    cfg = gv.carregar_config()
    carimbo = datetime.now().strftime("%Y%m%d-%H%M%S")
    pasta = gv.caminho(cfg.get("saida_dir", "../saida")) / carimbo
    pasta.mkdir(parents=True, exist_ok=True)
    try:
        (pasta / "roteiro.txt").write_text(roteiro + "\n", encoding="utf-8")

        ESTADO.update(etapa="voz", detalhe="Sintetizando sua voz (a primeira vez baixa o modelo XTTS, ~2 GB)…")
        audio = pasta / "voz.wav"
        gv.sintetizar_voz(roteiro, cfg, audio)

        ESTADO.update(etapa="avatar", detalhe=f"Gerando o vídeo do avatar ({cfg['video']['backend']}) — é a etapa mais demorada…")
        bruto = pasta / "avatar_bruto.mp4"
        gv.gerar_avatar(audio, cfg, bruto)

        ESTADO.update(etapa="finalizando", detalhe="Codificando o mp4 final…")
        final = pasta / "video_final.mp4"
        gv.finalizar(bruto, audio, final)

        ESTADO.update(etapa="pronto", detalhe="Vídeo pronto!",
                      video="/" + str(final.relative_to(RAIZ)).replace("\\", "/"))
    except SystemExit as e:            # gv usa sys.exit(msg) para erros de config
        ESTADO.update(etapa="erro", erro=str(e.code))
    except Exception as e:             # noqa: BLE001 — erro inesperado vai para a UI
        ESTADO.update(etapa="erro", erro=f"{type(e).__name__}: {e}")
    finally:
        ESTADO["ocupado"] = False


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(RAIZ), **kwargs)

    def log_message(self, *a):  # silencia o log por requisição
        pass

    def _json(self, obj, status=200):
        corpo = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _ler_corpo(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.path = "/pipeline/gerar.html"
        if self.path == "/api/status":
            return self._json(ESTADO)
        return super().do_GET()

    def do_POST(self):
        if self.path == "/api/roteiro":
            try:
                dados = self._ler_corpo()
                texto = gv.gerar_roteiro(dados["prompt"])
                return self._json({"roteiro": texto})
            except SystemExit as e:
                return self._json({"erro": str(e.code)}, 400)
            except Exception as e:  # noqa: BLE001
                msg = str(e)
                if isinstance(e, ModuleNotFoundError):
                    msg = "Pacote 'anthropic' não instalado neste ambiente — rode o instalar.sh, ou escreva o roteiro manualmente no passo 2."
                elif "ANTHROPIC_API_KEY" in msg or "api_key" in msg.lower() or "authentication" in msg.lower():
                    msg = ("Sem chave da API da Anthropic. Exporte ANTHROPIC_API_KEY antes de rodar o servidor, "
                           "ou escreva/cole o roteiro manualmente no campo abaixo.")
                return self._json({"erro": msg}, 400)

        if self.path == "/api/gerar":
            with TRAVA:
                if ESTADO["ocupado"]:
                    return self._json({"erro": "Já existe uma geração em andamento."}, 409)
                dados = self._ler_corpo()
                roteiro = (dados.get("roteiro") or "").strip()
                if not roteiro:
                    return self._json({"erro": "Roteiro vazio."}, 400)
                _reset_estado()
                threading.Thread(target=trabalho_gerar, args=(roteiro,), daemon=True).start()
            return self._json({"ok": True})

        self._json({"erro": "rota desconhecida"}, 404)


def main():
    servidor = HTTPServer(("127.0.0.1", PORTA), Handler)
    url = f"http://localhost:{PORTA}/"
    print(f"\n🎬 Estúdio de Geração no ar: {url}")
    print("   (o estúdio de gravação também está em /estudio.html)")
    print("   Ctrl+C para encerrar.\n")
    try:
        webbrowser.open(url)
    except Exception:  # noqa: BLE001 — sem navegador (ex.: ssh), segue só com o link
        pass
    servidor.serve_forever()


if __name__ == "__main__":
    main()
