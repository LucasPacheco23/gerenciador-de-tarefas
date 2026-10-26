# Gerenciador de Tarefas

Aplicação web para gerenciamento de tarefas, desenvolvida como projeto de portfólio para praticar desenvolvimento web com Python, HTML, CSS e banco de dados SQLite.

## Sobre o projeto

O **Gerenciador de Tarefas** é uma aplicação que tem como objetivo facilitar a organização de atividades em um só lugar.

O projeto utiliza Python no backend, páginas HTML para a interface, CSS para a estilização e um banco de dados para armazenar informações.

## Funcionalidades

- Visualização das tarefas cadastradas.
- Edição de tarefas.
- Armazenamento de dados em banco de dados.
- Interface web organizada.

*Observação: ajuste esta lista para corresponder exatamente às funcionalidades implementadas no projeto.*

## Tecnologias utilizadas

- **Python** — lógica e processamento no backend.
- **HTML5** — estrutura das páginas.
- **CSS3** — estilização da interface.
- **SQLite** — armazenamento local dos dados.
- **Git e GitHub** — controle de versão e publicação do código.

## Estrutura do projeto

```text
gerenciador-de-tarefas/
├── static/
│   ├── css/
│       └── style.css
├── templates/
│   ├── editar.html
│   └── index.html
├── app.py
├── database.py
├── requirements.txt
├── .gitignore
└── README.md
```

O banco de dados local e o ambiente virtual são mantidos fora do repositório por meio do `.gitignore`.

## ⚙️ Como executar o projeto

### Pré-requisitos

- Python instalado.
- Git instalado.
- Um terminal para executar os comandos.

### 1. Clone o repositório

```bash
git clone URL_DO_SEU_REPOSITORIO
```

Entre na pasta do projeto:

```bash
cd gerenciador-de-tarefas
```

### 2. Crie um ambiente virtual

No Windows:

```bash
python -m venv .venv
```

Ative o ambiente virtual no PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configuração de segurança

A aplicação utiliza a variável de ambiente `FLASK_SECRET_KEY` para configurar a chave secreta do Flask.

Antes de iniciar o servidor, configure essa variável no terminal. Não armazene chaves secretas diretamente no código-fonte nem as publique no repositório.

A chave utilizada localmente deve ser configurada novamente quando necessário. Em ambientes de produção, utilize uma variável de ambiente persistente e protegida.

```bash
$env:FLASK_SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Execute a aplicação

```bash
python app.py
```

Se a aplicação iniciar um servidor web local, acesse no navegador o endereço indicado no terminal.

> Os comandos de execução podem precisar de ajustes conforme a configuração do projeto.

## Objetivo

Este projeto faz parte do meu portfólio de desenvolvimento e tem como objetivo demonstrar meus conhecimentos em programação Python, desenvolvimento de interfaces web, organização de código e persistência de dados.

## Autor

Lucas Pacheco

- GitHub: (https://github.com/in/lucas-pacheco-782962393/)

---

Desenvolvido como projeto de estudo e portfólio.
