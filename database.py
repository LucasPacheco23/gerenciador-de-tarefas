import sqlite3


def conectar():
    conexao = sqlite3.connect("tarefas.db")
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def criar_tabela():
    conexao = conectar()

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS tarefas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descricao TEXT,
            concluida INTEGER NOT NULL DEFAULT 0,
            prioridade TEXT NOT NULL DEFAULT 'Media',
            criada_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    colunas = conexao.execute(
        "PRAGMA table_info(tarefas)"
    ).fetchall()

    nomes_colunas = [coluna["name"] for coluna in colunas]

    if "prioridade" not in nomes_colunas:
        conexao.execute("""
            ALTER TABLE tarefas
            ADD COLUMN prioridade TEXT NOT NULL DEFAULT 'Media'
        """)

    if "data_vencimento" not in nomes_colunas:
        conexao.execute("""
            ALTER TABLE tarefas
            ADD COLUMN data_vencimento TEXT
        """)

    conexao.commit()
    conexao.close()