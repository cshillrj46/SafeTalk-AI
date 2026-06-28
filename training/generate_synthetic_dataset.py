"""
Gera um dataset sintético de mensagens em português para treinar o
classificador inicial.

Importante (honestidade técnica): isto NÃO substitui dados reais.
É um ponto de partida razoável para o MVP rodar de ponta a ponta — o
roadmap real do produto depende de dataset real (parceria com
Procon/Reclame Aqui, ou contribuição opt-in e anonimizada de usuários).
Documentamos isso aqui em vez de fingir que o dataset sintético é
suficiente para produção.

Uso:
    python training/generate_synthetic_dataset.py
"""
import csv
import random
from pathlib import Path

random.seed(42)

NOMES = ["João", "Maria", "Carlos", "Ana", "Pedro", "Juliana", "Rafael", "Beatriz", "Lucas", "Fernanda"]
VALORES = ["50", "100", "150", "200", "300", "500", "1.000", "1.500", "2.000"]
BANCOS = ["Banco do Brasil", "Caixa", "Itaú", "Bradesco", "Nubank", "Santander", "Inter"]

GOLPE_TEMPLATES = [
    "Oi, troquei de número, esse é meu novo WhatsApp. Pode me fazer um PIX urgente de R$ {valor}? Te explico depois.",
    "URGENTE: sua conta no {banco} será bloqueada hoje. Confirme seus dados clicando no link para evitar o bloqueio.",
    "Olá, sou da central de atendimento do {banco}. Identificamos uma compra suspeita. Me informe o código de verificação que você recebeu por SMS.",
    "Ganhe R$ {valor} por dia trabalhando de casa, poucas horas por dia! Mandamos o cadastro agora, é só clicar.",
    "Seu WhatsApp está desatualizado e vai parar de funcionar. Atualize agora clicando no link antes que seja tarde.",
    "Seu pedido está com uma pendência no boleto. Pague a taxa de entrega urgente de R$ {valor} para liberar a encomenda.",
    "{nome}, preciso que você me ajude agora, é urgente! Faz um PIX de R$ {valor} pra essa chave que depois eu te devolvo.",
    "Parabéns! Você foi sorteado em uma promoção exclusiva do {banco}. Para receber o prêmio de R$ {valor}, confirme seus dados.",
    "Oi {nome}, aqui é da empresa de cobrança. Sua dívida vai virar protesto hoje à noite se você não fizer o PIX agora.",
    "Atenção: detectamos login suspeito na sua conta {banco}. Clique no link e confirme sua senha para proteger sua conta.",
]

LEGITIMA_TEMPLATES = [
    "Oi {nome}, vamos almoçar amanhã? Marquei aquele restaurante novo.",
    "Bom dia! Só confirmando nossa reunião de hoje às 14h sobre o projeto.",
    "{nome}, você viu o jogo de ontem? Que virada incrível no segundo tempo.",
    "Cheguei bem em casa, obrigado pela carona hoje!",
    "Lembra de trazer o documento para a reunião de amanhã, por favor.",
    "Adorei as fotos da viagem, {nome}! Onde foi essa praia?",
    "O relatório que você pediu já está pronto, vou te enviar por e-mail.",
    "Vamos remarcar o aniversário do {nome} pra sábado que vem?",
    "Oi, tudo bem? Faz tempo que a gente não se fala, como você está?",
    "A reunião foi adiada para sexta-feira às 10h, conforme conversamos.",
    "Comprei aquele livro que você recomendou, comecei a ler ontem.",
    "Parabéns pelo aniversário, {nome}! Te desejo tudo de bom.",
    "Pode me confirmar o endereço da festa de sábado?",
    "Vi a apresentação que você enviou, ficou muito boa.",
    "Vamos remarcar a consulta para a próxima semana, tudo bem pra você?",
]


def _fill(template: str) -> str:
    return template.format(
        nome=random.choice(NOMES),
        valor=random.choice(VALORES),
        banco=random.choice(BANCOS),
    )


def generate(n_per_class: int = 300) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for _ in range(n_per_class):
        rows.append((_fill(random.choice(GOLPE_TEMPLATES)), "golpe"))
        rows.append((_fill(random.choice(LEGITIMA_TEMPLATES)), "legitima"))
    random.shuffle(rows)
    return rows


def main() -> None:
    out_path = Path(__file__).parent / "data" / "messages.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows = generate(n_per_class=300)

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["message", "label"])
        writer.writerows(rows)

    print(f"✅ Dataset sintético gerado: {out_path} ({len(rows)} linhas)")
    print("⚠️  Lembrete: isso é dado sintético para o pipeline funcionar de ponta a ponta.")
    print("   Para produção, substitua por dados reais (anonimizados e com opt-in).")


if __name__ == "__main__":
    main()
