# SafeTalk B2B API

API de triagem de mensagens para detecção de golpes e engenharia social em
canais de atendimento (WhatsApp Business API, chat web, SMS), pensada para
integração em sistemas de bancos e fintechs — não um bot fechado de
WhatsApp.

Este repositório substitui o protótipo original [SafeTalk-AI](.), que usava
automação não-oficial de WhatsApp Web (`whatsapp-web.js`) e um classificador
simples sem tratamento de privacidade. Aqui o desenho é outro: o cliente B2B
mantém seu próprio canal (WhatsApp Business API oficial, CRM, etc.) e chama
esta API para obter um veredito de risco estruturado.

## Por que essa mudança

- **Canal oficial, não automação não-oficial**: bots baseados em
  `whatsapp-web.js`/Puppeteer correm risco real de banimento de número e não
  escalam. Esta API não toca o canal — ela só analisa o texto que o cliente
  já recebeu pelo canal dele.
- **Privacidade desde o design**: nenhuma mensagem em texto puro é
  persistida. O log de auditoria guarda só a versão anonimizada
  (`app/core/anonymizer.py`), com CPF, telefone, e-mail e cartão mascarados
  antes de qualquer escrita em disco.
- **Decisão em camadas, não um único modelo**: regras heurísticas (baratas e
  rápidas) cobrem os golpes mais óbvios e documentados; um modelo de ML
  cobre o grosso dos casos; um LLM entra só como segunda opinião nos casos
  ambíguos — controlando custo em alto volume.

## Arquitetura

```
Mensagem do chat
        │
        ▼
┌─────────────────────────────────────────────┐
│           Plataforma SafeTalk B2B            │
│  ┌───────────┐  ┌────────────┐  ┌──────────┐ │
│  │ Ingestão  │─▶│  Detecção  │─▶│ Resposta │ │
│  │(auth, PII)│  │  híbrida   │  │ & score  │ │
│  └───────────┘  └────────────┘  └──────────┘ │
└─────────────────────────────────────────────┘
        │
        ▼
Alerta / score ao analista (resposta da API)
```

Detalhes em [`docs/architecture.md`](docs/architecture.md).

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# edite .env se quiser configurar ANTHROPIC_API_KEY para o fallback de LLM

# gera dataset sintético e treina o modelo inicial
python training/generate_synthetic_dataset.py
python training/train_model.py

uvicorn app.main:app --reload
```

A API sobe em `http://localhost:8000`. Documentação interativa automática em
`http://localhost:8000/docs`.

### Chamando a API

```bash
curl -X POST http://localhost:8000/v1/analyze \
  -H "X-API-Key: dev-key-local" \
  -H "Content-Type: application/json" \
  -d '{"message": "Pix urgente agora, troquei de número, me ajuda!"}'
```

### Testes

```bash
pytest -v
```

## O que ainda é um MVP (limitações conhecidas, não escondidas)

- **Dataset de treino é sintético** (`training/generate_synthetic_dataset.py`).
  Suficiente para o pipeline funcionar de ponta a ponta, insuficiente para
  produção. Próximo passo real: dataset com mensagens reais anonimizadas,
  via parceria ou opt-in de usuários.
- **Anonimização é baseada em regex** — cobre CPF, CNPJ, telefone, e-mail e
  cartão, mas não nomes próprios ou endereços em texto livre. Uma v2
  precisaria de um modelo de NER em português.
- **Rate limiting é em memória**, válido para uma única instância. Múltiplas
  réplicas precisam de Redis ou um API gateway dedicado.
- **Log de auditoria em SQLite** — adequado para MVP/demo, não para alto
  volume multi-cliente em produção (migrar para Postgres).

## Licença

MIT — ver [LICENSE](LICENSE).
