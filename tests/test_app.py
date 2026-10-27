import re
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from app import create_app
from database import conectar


class TaskAppTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.db"
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "DATABASE": str(self.database_path),
        })
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def csrf_token(self):
        response = self.client.get("/")
        match = re.search(
            r'name="csrf_token" value="([^"]+)"',
            response.get_data(as_text=True),
        )
        self.assertIsNotNone(match)
        return match.group(1)

    def adicionar_tarefa(self, titulo, **overrides):
        dados = {
            "titulo": titulo,
            "descricao": "Descrição de teste",
            "prioridade": "Media",
            "data_vencimento": "",
            "csrf_token": self.csrf_token(),
        }
        dados.update(overrides)
        return self.client.post("/adicionar", data=dados)

    def test_fluxo_completo_de_tarefa(self):
        resposta = self.adicionar_tarefa(
            "Tarefa teste",
            prioridade="Alta",
            data_vencimento="2026-12-31",
        )
        self.assertEqual(resposta.status_code, 302)

        with conectar(self.database_path) as conexao:
            tarefa = conexao.execute(
                "SELECT * FROM tarefas WHERE titulo = ?", ("Tarefa teste",)
            ).fetchone()
        tarefa_id = tarefa["id"]
        self.assertEqual(tarefa["prioridade"], "Alta")

        resposta = self.client.post(
            f"/editar/{tarefa_id}",
            data={
                "csrf_token": self.csrf_token(),
                "titulo": "Tarefa atualizada",
                "descricao": "Descrição atualizada",
                "prioridade": "Baixa",
                "data_vencimento": "",
            },
        )
        self.assertEqual(resposta.status_code, 302)

        resposta = self.client.post(
            f"/concluir/{tarefa_id}",
            data={"csrf_token": self.csrf_token()},
        )
        self.assertEqual(resposta.status_code, 302)

        with conectar(self.database_path) as conexao:
            tarefa = conexao.execute(
                "SELECT * FROM tarefas WHERE id = ?", (tarefa_id,)
            ).fetchone()
        self.assertEqual(tarefa["titulo"], "Tarefa atualizada")
        self.assertEqual(tarefa["prioridade"], "Baixa")
        self.assertEqual(tarefa["concluida"], 1)

        resposta = self.client.post(
            f"/excluir/{tarefa_id}",
            data={"csrf_token": self.csrf_token()},
        )
        self.assertEqual(resposta.status_code, 302)
        with conectar(self.database_path) as conexao:
            self.assertIsNone(
                conexao.execute(
                    "SELECT id FROM tarefas WHERE id = ?", (tarefa_id,)
                ).fetchone()
            )

    def test_rejeita_post_sem_token_csrf(self):
        resposta = self.client.post(
            "/adicionar",
            data={"titulo": "Sem token", "prioridade": "Media"},
        )
        self.assertEqual(resposta.status_code, 400)

        resposta_unicode = self.client.post(
            "/adicionar",
            data={"titulo": "Token inválido", "csrf_token": "não é um token"},
        )
        self.assertEqual(resposta_unicode.status_code, 400)

    def test_exige_chave_secreta(self):
        with self.assertRaisesRegex(RuntimeError, "FLASK_SECRET_KEY"):
            create_app({
                "SECRET_KEY": None,
                "DATABASE": str(self.database_path),
            })

    def test_valida_campos_no_servidor(self):
        token = self.csrf_token()
        dados_invalidos = (
            {"titulo": "   "},
            {"titulo": "x" * 151},
            {"titulo": "Válida", "descricao": "x" * 5001},
            {"titulo": "Válida", "prioridade": "Urgente"},
            {"titulo": "Válida", "data_vencimento": "31-12-2026"},
            {"titulo": "Válida", "data_vencimento": "20261231"},
        )
        for dados in dados_invalidos:
            with self.subTest(dados=dados):
                resposta = self.client.post(
                    "/adicionar",
                    data={"prioridade": "Media", **dados, "csrf_token": token},
                )
                self.assertEqual(resposta.status_code, 302)

        with conectar(self.database_path) as conexao:
            total = conexao.execute(
                "SELECT COUNT(*) FROM tarefas"
            ).fetchone()[0]
        self.assertEqual(total, 0)

    def test_paginação_preserva_filtros_e_limita_resultados(self):
        with conectar(self.database_path) as conexao:
            conexao.executemany(
                """
                INSERT INTO tarefas (titulo, prioridade)
                VALUES (?, 'Alta')
                """,
                [(f"Tarefa pendente {indice}",) for indice in range(12)],
            )
            conexao.execute(
                "INSERT INTO tarefas (titulo, prioridade, concluida) "
                "VALUES ('Tarefa concluída', 'Alta', 1)"
            )
            conexao.commit()

        resposta = self.client.get(
            "/?status=pendentes&prioridade=Alta&pagina=1"
        )
        conteudo = resposta.get_data(as_text=True)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(conteudo.count('class="tarefa '), 10)
        self.assertIn(
            "status=pendentes&amp;prioridade=Alta&amp;pagina=2",
            conteudo,
        )

        segunda_pagina = self.client.get(
            "/?status=pendentes&prioridade=Alta&pagina=2"
        ).get_data(as_text=True)
        self.assertEqual(segunda_pagina.count('class="tarefa '), 2)
        self.assertIn("Página 2 de 2", segunda_pagina)

        pagina_fora_do_limite = self.client.get(
            "/?status=pendentes&prioridade=Alta&pagina=99"
        ).get_data(as_text=True)
        self.assertIn("Página 2 de 2", pagina_fora_do_limite)

        sem_resultados = self.client.get(
            "/?busca=nao-existe"
        ).get_data(as_text=True)
        self.assertIn(
            "Nenhuma tarefa corresponde aos filtros selecionados.",
            sem_resultados,
        )

    def test_inicializacao_migra_banco_existente_sem_perder_dados(self):
        caminho = Path(self.temp_dir.name) / "legado.db"
        with closing(sqlite3.connect(caminho)) as conexao:
            with conexao:
                conexao.execute("""
                    CREATE TABLE tarefas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        titulo TEXT NOT NULL,
                        descricao TEXT,
                        concluida INTEGER NOT NULL DEFAULT 0,
                        criada_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conexao.execute(
                    "INSERT INTO tarefas (titulo) VALUES ('Tarefa legada')"
                )

        create_app({
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "DATABASE": str(caminho),
        })

        with conectar(caminho) as conexao:
            tarefa = conexao.execute(
                "SELECT titulo, prioridade, data_vencimento FROM tarefas"
            ).fetchone()
        self.assertEqual(tarefa["titulo"], "Tarefa legada")
        self.assertEqual(tarefa["prioridade"], "Media")
        self.assertIsNone(tarefa["data_vencimento"])


if __name__ == "__main__":
    unittest.main()
