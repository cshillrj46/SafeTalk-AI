"""
Treina o classificador de golpe/legítima.

Diferenças deliberadas em relação ao protótipo original:
- Validação cruzada (não só um único split treino/teste), para ter uma
  noção mais confiável de variância do modelo.
- LogisticRegression em vez de RandomForest: mais rápido, mais leve para
  servir, e com probabilidades melhor calibradas para o threshold de
  confiança usado no pipeline (app/detection/pipeline.py).
- Salva métricas em um arquivo de relatório, não só imprime no terminal.

Uso:
    python training/generate_synthetic_dataset.py   # se ainda não gerou os dados
    python training/train_model.py
"""
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split

ROOT = Path(__file__).parent.parent
DATA_PATH = ROOT / "training" / "data" / "messages.csv"
MODEL_DIR = ROOT / "models"


def main() -> None:
    if not DATA_PATH.exists():
        raise SystemExit(
            f"Dataset não encontrado em {DATA_PATH}. "
            "Rode primeiro: python training/generate_synthetic_dataset.py"
        )

    df = pd.read_csv(DATA_PATH)
    X, y = df["message"], df["label"]

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
    X_vec = vectorizer.fit_transform(X)

    model = LogisticRegression(max_iter=1000, class_weight="balanced")

    # Validação cruzada para checar estabilidade antes do split final.
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X_vec, y, cv=cv, scoring="f1_macro")
    print(f"📊 F1-macro (5-fold cross-validation): {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

    X_train, X_test, y_train, y_test = train_test_split(
        X_vec, y, test_size=0.2, random_state=42, stratify=y
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    report = classification_report(y_test, y_pred, output_dict=True)
    print("📋 Relatório de classificação (holdout):")
    print(classification_report(y_test, y_pred))

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_DIR / "scam_detector.joblib")
    joblib.dump(vectorizer, MODEL_DIR / "vectorizer.joblib")
    with (MODEL_DIR / "training_report.json").open("w", encoding="utf-8") as f:
        json.dump(
            {
                "cv_f1_macro_mean": cv_scores.mean(),
                "cv_f1_macro_std": cv_scores.std(),
                "holdout_report": report,
                "n_samples": len(df),
                "aviso": (
                    "Score próximo de 1.0 é esperado e NÃO indica um modelo pronto para produção: "
                    "o dataset sintético é gerado a partir de poucos templates fixos (veja "
                    "generate_synthetic_dataset.py), então treino e teste compartilham o mesmo "
                    "vocabulário e estrutura de frase. Isso valida que o pipeline de treino "
                    "funciona de ponta a ponta — não substitui avaliação com dados reais e variados."
                ),
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"✅ Modelo, vetorizador e relatório salvos em {MODEL_DIR}/")
    print(
        "⚠️  Score próximo de 1.0 é esperado com dataset sintético baseado em templates — "
        "não é uma métrica real de produção. Veja o aviso em training_report.json."
    )


if __name__ == "__main__":
    main()
