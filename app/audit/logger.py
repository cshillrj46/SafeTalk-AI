"""
Log de auditoria persistente.

Usa SQLite (biblioteca padrão, sem dependência extra) — suficiente para o
MVP e para um único cliente/instância. Em produção com múltiplos clientes
e alto volume, isso migraria para Postgres ou um data warehouse, mas a
interface (record / stats_summary) não mudaria.

Importante: o que entra aqui é SEMPRE a mensagem já anonimizada
(app.core.anonymizer.anonymize). Esta classe não decide o que anonimizar —
só persiste o que recebe. A responsabilidade de nunca passar texto bruto
é do chamador (app.detection.pipeline).
"""
import json
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path


class AuditLogger:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path, check_same_thread=False)

    def _init_db(self) -> None:
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT NOT NULL,
                    client_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    anonymized_message TEXT NOT NULL,
                    risk TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    source TEXT NOT NULL,
                    triggered_rules TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_client_created ON audit_log(client_id, created_at)")

    def record(
        self,
        request_id: str,
        client_id: str,
        anonymized_message: str,
        risk: str,
        confidence: float,
        source: str,
        triggered_rules: list[str],
    ) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO audit_log
                    (request_id, client_id, created_at, anonymized_message, risk, confidence, source, triggered_rules)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request_id,
                    client_id,
                    datetime.now(timezone.utc).isoformat(),
                    anonymized_message,
                    risk,
                    confidence,
                    source,
                    json.dumps(triggered_rules),
                ),
            )

    def stats_summary(self, client_id: str, window_hours: int = 24) -> dict:
        since = (datetime.now(timezone.utc) - timedelta(hours=window_hours)).isoformat()
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT risk, source FROM audit_log WHERE client_id = ? AND created_at >= ?",
                (client_id, since),
            ).fetchall()

        por_fonte: dict[str, int] = {}
        total_alto = total_medio = total_baixo = 0
        for risk, source in rows:
            por_fonte[source] = por_fonte.get(source, 0) + 1
            if risk == "alto":
                total_alto += 1
            elif risk == "medio":
                total_medio += 1
            else:
                total_baixo += 1

        return {
            "client": client_id,
            "window_hours": window_hours,
            "total_analisadas": len(rows),
            "total_alto_risco": total_alto,
            "total_medio_risco": total_medio,
            "total_baixo_risco": total_baixo,
            "por_fonte": por_fonte,
        }
