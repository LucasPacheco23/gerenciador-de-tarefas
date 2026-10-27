# Gerenciador de Tarefas

Aplicação web em Flask para criar, editar, concluir e excluir tarefas. As tarefas podem ter descrição, prioridade e data de vencimento; a lista oferece pesquisa, filtros, estatísticas e paginação. Os dados são armazenados localmente em SQLite.

## Tecnologias

- Python e Flask
- HTML5 e CSS3
- SQLite
- `unittest` para testes automatizados

## Requisitos

- Python 3.9 ou superior
- Git
- PowerShell (para os comandos abaixo no Windows)

## Executar localmente

Clone o repositório e entre na pasta:

```powershell
git clone https://github.com/LucasPacheco23/gerenciador-de-tarefas.git
cd gerenciador-de-tarefas
```

Crie e ative um ambiente virtual e instale as dependências:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Configure uma chave secreta para a sessão do Flask. Gere outra chave para cada ambiente e não a compartilhe nem a salve no repositório:

```powershell
$env:FLASK_SECRET_KEY = (python -c "import secrets; print(secrets.token_hex(32))")
```

Inicie o servidor local:

```powershell
python app.py
```

Abra o endereço local exibido no terminal. O modo de depuração fica desativado por padrão. Para habilitá-lo somente durante o desenvolvimento no PowerShell, execute `$env:FLASK_DEBUG = "1"` antes de iniciar. O servidor integrado do Flask é destinado ao desenvolvimento; use um servidor WSGI apropriado em produção.

O banco `tarefas.db` é criado na pasta do projeto na primeira inicialização e atualizado automaticamente quando novas colunas são necessárias.

## Testes

Com o ambiente virtual ativado, execute:

```powershell
python -m unittest discover -s tests -v
```

Os testes usam bancos temporários e não alteram o banco de dados local do projeto.

## Estrutura

```text
gerenciador-de-tarefas/
├── static/
│   └── css/
│       └── style.css
├── templates/
│   ├── editar.html
│   └── index.html
├── tests/
│   └── test_app.py
├── app.py
├── database.py
├── requirements.txt
└── README.md
```

O ambiente virtual, o banco de dados e arquivos locais de configuração não são versionados.

## Autor

[Lucas Pacheco no GitHub](https://github.com/LucasPacheco23)
