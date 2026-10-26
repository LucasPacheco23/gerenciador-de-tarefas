from flask import Flask, render_template, request, redirect, url_for, flash
from database import conectar, criar_tabela
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

if not app.secret_key:
    raise RuntimeError("A variável FLASK_SECRET_KEY não foi configurada.")

@app.route("/")
def inicio():
    # Recebe os filtros enviados pela página
    busca = request.args.get("busca", "").strip()
    status = request.args.get("status", "todas")
    prioridade = request.args.get("prioridade", "todas")

    # Começa com uma consulta que seleciona todas as tarefas
    sql = "SELECT * FROM tarefas WHERE 1=1"
    parametros = []

    # Filtra pelo título digitado
    if busca:
        sql += " AND titulo LIKE ?"
        parametros.append(f"%{busca}%")

    # Filtra pela situação da tarefa
    if status == "pendentes":
        sql += " AND concluida = 0"
    elif status == "concluidas":
        sql += " AND concluida = 1"

    # Filtra pela prioridade
    prioridades_validas = ["Baixa", "Media", "Alta"]

    if prioridade in prioridades_validas:
        sql += " AND prioridade = ?"
        parametros.append(prioridade)

    # Ordena as tarefas pendentes antes das concluídas
    sql += " ORDER BY concluida ASC, id DESC"

    conexao = conectar()

    tarefas = conexao.execute(
        sql,
        parametros
    ).fetchall()

    # Calcula as estatísticas de todas as tarefas,
    # independentemente dos filtros selecionados.
    estatisticas = conexao.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN concluida = 0 THEN 1 ELSE 0 END) AS pendentes,
            SUM(CASE WHEN concluida = 1 THEN 1 ELSE 0 END) AS concluidas
        FROM tarefas
    """).fetchone()

    conexao.close()

    return render_template(
        "index.html",
        tarefas=tarefas,
        busca=busca,
        status=status,
        prioridade=prioridade,
        estatisticas=estatisticas
    )

@app.route("/adicionar", methods=["POST"])
def adicionar():
    titulo = request.form.get("titulo", "").strip()
    descricao = request.form.get("descricao", "").strip()
    prioridade = request.form.get("prioridade", "Media")
    data_vencimento = request.form.get("data_vencimento", "").strip()

    prioridades_validas = ["Baixa", "Media", "Alta"]

    if not titulo:
        flash("O título da tarefa é obrigatório.", "erro")
        return redirect(url_for("inicio"))

    if prioridade not in prioridades_validas:
        flash("Prioridade inválida.", "erro")
        return redirect(url_for("inicio"))

    if data_vencimento:
        try:
            from datetime import date
            date.fromisoformat(data_vencimento)
        except ValueError:
            flash("Data de vencimento inválida.", "erro")
            return redirect(url_for("inicio"))

    conexao = conectar()

    conexao.execute("""
        INSERT INTO tarefas (
            titulo,
            descricao,
            prioridade,
            data_vencimento
        )
        VALUES (?, ?, ?, ?)
    """, (
        titulo,
        descricao,
        prioridade,
        data_vencimento or None
    ))

    conexao.commit()
    conexao.close()

    flash("Tarefa adicionada com sucesso!", "sucesso")

    return redirect(url_for("inicio"))

@app.route("/concluir/<int:id>", methods=["POST"])
def concluir(id):
    conexao = conectar()

    tarefa = conexao.execute(
        "SELECT concluida FROM tarefas WHERE id = ?",
        (id,)
    ).fetchone()

    if tarefa is None:
        conexao.close()
        flash("Tarefa não encontrada.", "erro")
        return redirect(url_for("inicio"))

    novo_estado = 0 if tarefa["concluida"] else 1

    conexao.execute(
        "UPDATE tarefas SET concluida = ? WHERE id = ?",
        (novo_estado, id)
    )

    conexao.commit()
    conexao.close()

    return redirect(url_for("inicio"))


@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    conexao = conectar()

    tarefa = conexao.execute(
        "SELECT * FROM tarefas WHERE id = ?",
        (id,)
    ).fetchone()

    if tarefa is None:
        conexao.close()
        flash("Tarefa não encontrada.", "erro")
        return redirect(url_for("inicio"))

    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        descricao = request.form.get("descricao", "").strip()
        prioridade = request.form.get("prioridade", "Media")

        prioridades_validas = ["Baixa", "Media", "Alta"]

        if not titulo:
            conexao.close()
            flash("O título da tarefa é obrigatório.", "erro")
            return redirect(url_for("editar", id=id))

        if prioridade not in prioridades_validas:
            conexao.close()
            flash("Prioridade inválida.", "erro")
            return redirect(url_for("editar", id=id))

        data_vencimento = request.form.get(
            "data_vencimento", ""
        ).strip()

        if data_vencimento:
            try:
                from datetime import date
                date.fromisoformat(data_vencimento)
            except ValueError:
                conexao.close()
                flash("Data de vencimento inválida.", "erro")
                return redirect(url_for("editar", id=id))

        conexao.execute("""
            UPDATE tarefas
            SET titulo = ?,
                descricao = ?,
                prioridade = ?,
                data_vencimento = ?
            WHERE id = ?
        """, (
            titulo,
            descricao,
            prioridade,
            data_vencimento or None,
            id
        ))

        conexao.commit()
        conexao.close()

        flash("Tarefa atualizada com sucesso!", "sucesso")
        return redirect(url_for("inicio"))

    conexao.close()

    return render_template("editar.html", tarefa=tarefa)

@app.route("/excluir/<int:id>", methods=["POST"])
def excluir(id):
    conexao = conectar()

    conexao.execute(
        "DELETE FROM tarefas WHERE id = ?",
        (id,)
    )

    conexao.commit()
    conexao.close()

    flash("Operação de exclusão concluída.", "sucesso")

    return redirect(url_for("inicio"))


if __name__ == "__main__":
    criar_tabela()
    app.run(debug=True)