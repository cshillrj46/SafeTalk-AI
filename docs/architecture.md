# Arquitetura

## Visão geral

A API expõe um único endpoint principal, `POST /v1/analyze`, que recebe o
texto de uma mensagem (já transcrita, se originalmente era áudio) e devolve
um veredito estruturado de risco. O cliente B2B (banco, fintech, plataforma
de atendimento) decide o que fazer com esse veredito — bloquear a mensagem,
escalar para um analista humano, ou só alimentar o próprio dashboard de
fraude.

## Camadas do pipeline (`app/detection/pipeline.py`)

1. **Motor de regras** (`rules_engine.py`) — heurísticas baratas para os
   padrões de golpe mais documentados no Brasil: PIX urgente, falso parente
   que trocou de número, falsa central bancária, falsa renda extra, falso
   boleto/taxa de entrega, phishing de "atualização do WhatsApp". Roda
   sempre, em microssegundos. Se a pontuação combinada passa do limiar de
   alto risco, o pipeline responde aqui mesmo — sem gastar inferência de ML
   nem chamar LLM.

2. **Modelo de ML** (`ml_model.py`) — TF-IDF + LogisticRegression, treinado
   em `training/train_model.py`. Cobre os casos que as regras não capturam
   explicitamente. Se a confiança do modelo está acima do limiar configurado
   (`ML_CONFIDENCE_THRESHOLD`), esse é o veredito final.

3. **LLM de segunda opinião** (`llm_fallback.py`) — só é chamado quando nem
   as regras nem o ML tiveram confiança suficiente. Usa um modelo mais barato
   (Claude Haiku por padrão) porque é uma tarefa de classificação simples em
   alto volume, não uma tarefa que justifique o modelo mais caro da linha.

Se todas as camadas falharem ou estiverem indisponíveis, a API ainda
responde — com o melhor palpite disponível e confiança mais baixa,
sinalizado como `source: "indeterminado"`. Nunca retorna erro 500 por causa
de uma camada opcional fora do ar.

## Privacidade (`app/core/anonymizer.py`)

A mensagem original só existe em memória durante o processamento da
requisição. O que é persistido no log de auditoria é sempre a versão
anonimizada — CPF, CNPJ, telefone, e-mail e número de cartão são mascarados
antes de qualquer escrita em disco. Essa é uma decisão de design, não uma
feature opcional.

## Autenticação e rate limiting

- `app/core/auth.py`: autenticação por API key (header `X-API-Key`),
  mapeada para um identificador de cliente nas configurações.
- `app/core/rate_limit.py`: limite de requisições por minuto, por cliente,
  em memória (ponto de extensão documentado para Redis em produção
  multi-instância).

## Auditoria e métricas (`app/audit/logger.py`)

Cada análise gera um registro em SQLite com mensagem anonimizada, veredito,
confiança e qual camada decidiu. O endpoint `GET /v1/stats/summary` expõe um
resumo agregado por cliente — a fonte de dados que alimentaria um dashboard
de fraude no produto B2B.

## O que mudou em relação ao protótipo original (SafeTalk-AI)

| Aspecto | Protótipo original | Esta versão |
|---|---|---|
| Canal | `whatsapp-web.js` (não-oficial, risco de ban) | API pura — cliente usa seu próprio canal oficial |
| ML | RandomForest sem validação cruzada | LogisticRegression com cross-validation e relatório salvo |
| Privacidade | Nenhuma anonimização | Anonimização antes de qualquer persistência |
| Decisão | Único modelo, sem segunda opinião | Regras → ML → LLM, com fallback gracioso em cada etapa |
| Testes | `assert 1+1==2` | Testes reais de regras, anonimização, pipeline e API |
| Dependências | `requirements.txt` não correspondia ao código | Corrigido e versionado |
