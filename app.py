import hmac
import os
import secrets
from datetime import date

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from database import DATABASE_PATH, conectar, criar_tabela

PRIORIDADES_VALIDAS = ("Baixa", "Media", "Alta")
TITULO_MAX_LENGTH = 150
DESCRICAO_MAX_LENGTH = 5000
TAREFAS_POR_PAGINA = 10


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=str(DATABASE_PATH),
        SECRET_KEY=os.environ.get("FLASK_SECRET_KEY"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if config:
        app.config.update(config)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("A variável FLASK_SECRET_KEY não foi configurada.")

    criar_tabela(app.config["DATABASE"])

    def obter_token_csrf():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_urlsafe(32)
        return session["csrf_token"]

    @app.before_request
    def validar_token_csrf():
        if request.method == "POST":
            token_enviado = request.form.get("csrf_token", "")
            token_sessao = session.get("csrf_token", "")
            if not token_sessao or not hmac.compare_digest(
                token_enviado.encode("utf-8"), token_sessao.encode("utf-8")
            ):
                abort(400, description="Token de segurança inválido ou ausente.")

    @app.context_processor
    def disponibilizar_token_csrf():
        return {"csrf_token": obter_token_csrf}

    @app.route("/")
    def inicio():
        busca = request.args.get("busca", "").strip()
        status = request.args.get("status", "todas")
        prioridade = request.args.get("prioridade", "todas")
        if status not in ("todas", "pendentes", "concluidas"):
            status = "todas"
        if prioridade not in ("todas", *PRIORIDADES_VALIDAS):
            prioridade = "todas"

        filtros_sql = ""
        parametros = []

        if busca:
            filtros_sql += " AND titulo LIKE ?"
            parametros.append(f"%{busca}%")
        if status == "pendentes":
            filtros_sql += " AND concluida = 0"
        elif status == "concluidas":
            filtros_sql += " AND concluida = 1"
        if prioridade in PRIORIDADES_VALIDAS:
            filtros_sql += " AND prioridade = ?"
            parametros.append(prioridade)

        pagina = max(1, request.args.get("pagina", 1, type=int) or 1)

        with conectar(app.config["DATABASE"]) as conexao:
            total_filtrado = conexao.execute(
                "SELECT COUNT(*) FROM tarefas WHERE 1=1" + filtros_sql,
                parametros,
            ).fetchone()[0]
            total_paginas = max(
                1, (total_filtrado + TAREFAS_POR_PAGINA - 1) // TAREFAS_POR_PAGINA
            )
            pagina = min(pagina, total_paginas)

            tarefas = conexao.execute(
                "SELECT * FROM tarefas WHERE 1=1"
                + filtros_sql
                + " ORDER BY concluida ASC, id DESC LIMIT ? OFFSET ?",
                parametros
                + [TAREFAS_POR_PAGINA, (pagina - 1) * TAREFAS_POR_PAGINA],
            ).fetchall()

            estatisticas = conexao.execute("""
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN concluida = 0 THEN 1 ELSE 0 END) AS pendentes,
                    SUM(CASE WHEN concluida = 1 THEN 1 ELSE 0 END) AS concluidas
                FROM tarefas
            """).fetchone()

        return render_template(
            "index.html",
            tarefas=tarefas,
            busca=busca,
            status=status,
            prioridade=prioridade,
            estatisticas=estatisticas,
            pagina=pagina,
            total_paginas=total_paginas,
            total_filtrado=total_filtrado,
        )

    def validar_dados_tarefa():
        titulo = request.form.get("titulo", "").strip()
        descricao = request.form.get("descricao", "").strip()
        prioridade = request.form.get("prioridade", "Media")
        data_vencimento = request.form.get("data_vencimento", "").strip()

        if not titulo:
            return None, "O título da tarefa é obrigatório."
        if len(titulo) > TITULO_MAX_LENGTH:
            return None, "O título deve ter no máximo 150 caracteres."
        if len(descricao) > DESCRICAO_MAX_LENGTH:
            return None, "A descrição deve ter no máximo 5000 caracteres."
        if prioridade not in PRIORIDADES_VALIDAS:
            return None, "Prioridade inválida."
        if data_vencimento:
            try:
                data_validada = date.fromisoformat(data_vencimento)
            except ValueError:
                return None, "Data de vencimento inválida."
            if data_validada.isoformat() != data_vencimento:
                return None, "Data de vencimento inválida."

        return {
            "titulo": titulo,
            "descricao": descricao,
            "prioridade": prioridade,
            "data_vencimento": data_vencimento or None,
        }, None

    @app.route("/adicionar", methods=["POST"])
    def adicionar():
        dados, erro = validar_dados_tarefa()
        if erro:
            flash(erro, "erro")
            return redirect(url_for("inicio"))

        with conectar(app.config["DATABASE"]) as conexao:
            conexao.execute("""
                INSERT INTO tarefas (titulo, descricao, prioridade, data_vencimento)
                VALUES (?, ?, ?, ?)
            """, (
                dados["titulo"],
                dados["descricao"],
                dados["prioridade"],
                dados["data_vencimento"],
            ))

        flash("Tarefa adicionada com sucesso!", "sucesso")
        return redirect(url_for("inicio"))

    @app.route("/concluir/<int:id>", methods=["POST"])
    def concluir(id):
        with conectar(app.config["DATABASE"]) as conexao:
            tarefa = conexao.execute(
                "SELECT concluida FROM tarefas WHERE id = ?", (id,)
            ).fetchone()
            if tarefa is None:
                flash("Tarefa não encontrada.", "erro")
                return redirect(url_for("inicio"))

            conexao.execute(
                "UPDATE tarefas SET concluida = ? WHERE id = ?",
                (0 if tarefa["concluida"] else 1, id),
            )

        return redirect(url_for("inicio"))

    @app.route("/editar/<int:id>", methods=["GET", "POST"])
    def editar(id):
        with conectar(app.config["DATABASE"]) as conexao:
            tarefa = conexao.execute(
                "SELECT * FROM tarefas WHERE id = ?", (id,)
            ).fetchone()
            if tarefa is None:
                flash("Tarefa não encontrada.", "erro")
                return redirect(url_for("inicio"))

            if request.method == "POST":
                dados, erro = validar_dados_tarefa()
                if erro:
                    flash(erro, "erro")
                    return redirect(url_for("editar", id=id))

                conexao.execute("""
                    UPDATE tarefas
                    SET titulo = ?, descricao = ?, prioridade = ?, data_vencimento = ?
                    WHERE id = ?
                """, (
                    dados["titulo"],
                    dados["descricao"],
                    dados["prioridade"],
                    dados["data_vencimento"],
                    id,
                ))

        if request.method == "POST":
            flash("Tarefa atualizada com sucesso!", "sucesso")
            return redirect(url_for("inicio"))
        return render_template("editar.html", tarefa=tarefa)

    @app.route("/excluir/<int:id>", methods=["POST"])
    def excluir(id):
        with conectar(app.config["DATABASE"]) as conexao:
            cursor = conexao.execute("DELETE FROM tarefas WHERE id = ?", (id,))
            if cursor.rowcount == 0:
                flash("Tarefa não encontrada.", "erro")
                return redirect(url_for("inicio"))

        flash("Tarefa excluída com sucesso.", "sucesso")
        return redirect(url_for("inicio"))

    return app


if __name__ == "__main__":
    aplicacao = create_app()
    aplicacao.run(debug=os.environ.get("FLASK_DEBUG") == "1")
