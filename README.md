# ⚡ Dados Abertos do Setor Elétrico 

Este projeto oferece uma interface simples em Python para acessar e baixar dados públicos do Setor Elétrico nos 3 principais órgãos: **CCEE (Câmara de Comercialização de Energia Elétrica)**, **ONS (Operador Nacional do Sistema)** e **ANEEL (Agência Nacional de Energia Elétrica)**.

## Introdução

Através da classe `dadosAbertosSetorEletrico`, você pode listar produtos disponíveis e baixar os dados completos de forma paginada e organizada com `pandas`.

### ✅ Funcionalidades

- 🔍 Listagem de produtos disponíveis na API da CCEE  
- ⬇️ Download completo e incremental dos datasets  
- 📦 Conversão automática para `pandas.DataFrame`

### ⚙️ Pré-requisitos

Antes de começar, certifique-se de ter os seguintes softwares instalados:

- **Python** 3.8 ou superior → [Download Python](https://www.python.org/downloads/)
- **pip** (gerenciador de pacotes do Python)
- **Git** → [Download Git](https://git-scm.com/downloads)
- **Editor de código** (sugestão: [Visual Studio Code](https://code.visualstudio.com/))

### 📦 Instalação

Clone este repositório e instale as dependências:

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio

# (Opcional) Crie e ative um ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt
```

## Exemplo de uso

```python
from dados_ccee import dadosAbertosSetorEletrico

# Inicializa o cliente
cliente = dadosAbertosSetorEletrico()

# Lista os produtos disponíveis na API da CCEE
produtos = cliente.listar_produtos_disponiveis()
print(produtos)

# Baixa todos os dados do produto desejado como DataFrame
df = cliente.baixar_dados_produto_completo("parcela_carga_consumo")
print(df.head())
```

## Estrutura do projeto

📦 seu-repositorio/
├── app.py               # Código principal da classe
├── app.ipynb        # Exemplo prático em notebook
├── requirements.txt            # Dependências do projeto
└── README.md                   # Documentação principal


## Contribuições

Contribuições são muito bem-vindas!
Se você quiser sugerir melhorias, corrigir bugs ou adicionar novas funcionalidades, sinta-se à vontade para abrir uma issue ou pull request.

## Fontes oficiais

- **Portal de Dados Abertos da CCEE** → [Acessar Portal](https://dadosabertos.ccee.org.br/)

- **CKAN API Reference (oficial)** → [Acessar Documentação (Inglês)](https://docs.ckan.org/en/2.11/)



