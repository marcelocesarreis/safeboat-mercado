# Gerador de Vídeos Automáticos · Avatar Pessoal

Sistema que cria vídeos seus a partir de um prompt de texto, em qualquer contexto,
usando sua voz e seu rosto. Funciona em duas fases:

1. **Fase de captura (uma vez)** — o estúdio guia você a gravar um corpus de fala
   foneticamente completo do português brasileiro. Isso vira a base de dados.
2. **Fase de geração (sempre que quiser)** — você escreve um prompt, o Claude
   escreve o roteiro, sua voz clonada fala o texto e um modelo de lip-sync
   coloca a fala no seu rosto. Sai um `.mp4` pronto.

## Por que gravar frases, e não sílabas soltas?

Sistemas que "colam" sílabas gravadas (síntese concatenativa) foram abandonados
há mais de uma década — o resultado soa robótico, porque a prosódia (ritmo,
entonação, coarticulação entre sons) não emenda. A abordagem atual é **neural**:
o modelo aprende o seu timbre, sotaque e jeito de falar a partir de gravações
naturais, e então gera *qualquer* fala nova com naturalidade.

O corpus deste sistema garante que suas gravações cubram **todos os fonemas do
pt-BR** (vogais, nasais, lh/nh/rr/ch/j, encontros consonantais), mais prosódia
de frases longas, estilos expressivos e o vocabulário do seu domínio — que é
exatamente o que os modelos de clonagem precisam para reproduzir você bem.
São ~55 gravações (15–20 min de fala), suficientes para clonagem de alta
qualidade com XTTS-v2 ou ElevenLabs.

## Estrutura

```
gerador-video/
├── estudio.html          # app de gravação no navegador
├── roteiros/corpus.json  # frases foneticamente balanceadas (edite o bloco 7!)
├── pipeline/
│   ├── preparar_dataset.py   # zip exportado → dataset de treino
│   ├── gerar_video.py        # prompt → roteiro → voz → vídeo
│   ├── config.exemplo.yaml
│   └── requirements.txt
├── dataset/              # gerado por preparar_dataset.py (não versionar)
└── saida/                # vídeos gerados (não versionar)
```

## Passo a passo

### 1. Gravar a base de dados

**Pelo celular (recomendado):** abra no navegador do celular o endereço
publicado pelo GitHub Pages —

```
https://marcelocesarreis.github.io/safeboat-mercado/gerador-video/estudio.html
```

O HTTPS do Pages é o que libera câmera e microfone no celular. Use o aparelho
na horizontal, apoiado, na altura dos olhos. As gravações ficam só no navegador
e no zip exportado — nunca são enviadas ao repositório.

**Pelo computador:** dê duplo clique em `estudio.html` (o corpus está embutido
na página) ou sirva localmente:

```bash
# na raiz do repositório
npx http-server . -p 8125 -c-1
# abra http://localhost:8125/gerador-video/estudio.html
```

O estúdio pede câmera e microfone, mostra frase por frase, deixa revisar e
regravar cada uma, acompanha a **cobertura fonética** em tempo real e salva
tudo no navegador (IndexedDB — sobrevive a refresh). Ao final, o botão
**Exportar dataset** baixa um `.zip` com todos os vídeos + `metadados.json`
com as transcrições.

Dicas que valem ouro: mesma sessão, mesma luz, mesmo enquadramento, ambiente
silencioso. Edite o **Bloco 7** do `corpus.json` com o vocabulário que você
realmente usa.

### 2. Preparar o dataset

```bash
cd gerador-video/pipeline
pip install -r requirements.txt   # requer ffmpeg instalado
python preparar_dataset.py ~/Downloads/dataset-avatar-2026-08-06.zip --saida ../dataset
```

Gera os `.wav` a 24 kHz com transcrições (formato LJSpeech), separa os clipes
de referência de voz e extrai foto/vídeo de referência do rosto.

### 3. Escolher os motores (config.yaml)

```bash
cp config.exemplo.yaml config.yaml
```

| Etapa | Opção local (grátis) | Opção API (paga, melhor) |
|---|---|---|
| Voz | **XTTS-v2** (Coqui) — clona direto dos wavs de referência | **ElevenLabs** — crie a voz no painel com os mesmos wavs |
| Vídeo | **Wav2Lip** — lip-sync sobre vídeo real seu (mais natural) ou **SadTalker** — anima uma foto | HeyGen / D-ID — avatar sob demanda |

Para os backends locais de vídeo, clone os repositórios e aponte o caminho no
`config.yaml`:

```bash
git clone https://github.com/Rudrabha/Wav2Lip ~/repos/Wav2Lip      # + checkpoint wav2lip_gan.pth
git clone https://github.com/OpenTalker/SadTalker ~/repos/SadTalker
```

### 4. Gerar vídeos por prompt

```bash
export ANTHROPIC_API_KEY=sk-ant-...

# só o roteiro, para revisar antes
python gerar_video.py --prompt "Vídeo de 45 segundos explicando por que toda \
lancha precisa estar registrada na Capitania, tom didático e direto" --so-roteiro

# vídeo completo
python gerar_video.py --prompt "..."

# ou com roteiro seu, sem passar pelo Claude
python gerar_video.py --roteiro meu_roteiro.txt
```

O roteirista (Claude Opus 5, com fallback automático habilitado) escreve fala
natural em primeira pessoa, números por extenso e ritmo calibrado para ~140
palavras/minuto — pronto para síntese de voz.

## Uso responsável

Este sistema gera mídia sintética **da sua própria pessoa, com o seu
consentimento**. Boas práticas:

- Identifique vídeos publicados como gerados por IA (várias plataformas exigem).
- Não use a base de dados para gerar terceiros, nem ceda os modelos treinados
  sem controle — sua voz e rosto são credenciais biométricas.
- Guarde o dataset exportado em local seguro; ele permite clonar você.

## Evoluções naturais

- **Qualidade de voz**: com 30+ min de fala, fine-tuning do XTTS-v2 ou F5-TTS
  no dataset (o `metadata.csv` já está no formato esperado).
- **Avatar corpo inteiro / gestos**: EchoMimic, LivePortrait ou serviços como
  HeyGen com avatar customizado (aceitam ~2 min de vídeo de referência —
  os blocos 5 e 8 servem de material).
- **Legendas e cortes**: acrescentar etapa de `whisper` + `ffmpeg` no pipeline.
- **Lote**: um CSV de prompts → N vídeos, usando a Batch API do Claude para os roteiros.
