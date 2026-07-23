# ⚡ Dados Abertos do Setor Elétrico 
![Avatar Twitter 1](https://github.com/user-attachments/assets/f7e05698-789b-41cc-8965-bb9a2f28b14b)

![ons-logo@2x ac52821bc48c70c7d00b5fd88ad4a3c8f4013a25](https://github.com/user-attachments/assets/0a1f3849-d6f9-4ea6-801b-d03fca56f5f8)

![images](https://github.com/user-attachments/assets/93c6ca2f-0df1-4fc3-86b8-057bfc385cd8)

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
from dadosAbertosSetorEletrico import dadosAbertosSetorEletrico

# Inicializa o cliente
cliente = dadosAbertosSetorEletrico("ccee")

# Lista os produtos disponíveis na API da CCEE
produtos = cliente.listar_produtos_disponiveis()
print(produtos)

# Baixa todos os dados do produto desejado como DataFrame
df = cliente.baixar_dados_produto_completo("parcela_carga_consumo")
print(df.head())
```

## ✅ Testes Automatizados

Este projeto já vem com uma suíte completa de testes automatizados que garante o funcionamento correto de cada parte do código. Mesmo que você nunca tenha usado testes em Python, aqui está como fazer funcionar.

### 🧪 O que está sendo testado?

- Inicialização correta da classe `dadosAbertosSetorEletrico`
- Comunicação com a API para listar produtos
- Extração de IDs de recursos (datasets)
- Download de dados completos de forma assíncrona
- Casos de erro simulados e retorno vazio

Os testes estão localizados na pasta:

tests/test_dadosAbertosSetorEletrico.py

Todos os testes estão **comentados passo a passo** para facilitar a leitura até mesmo para iniciantes.

### ⚙️ Como rodar os testes

1. Instale os pacotes de teste (se ainda não tiver feito):

```bash
pip install pytest pytest-asyncio
```

2. Execute os testes na raiz do projeto:

```bash
pytest -v 
```
- O -v significa “modo verboso” e exibe o nome de cada teste sendo executado.

Se tudo estiver funcionando corretamente, você verá algo assim:

```bash
tests/test_dadosAbertosSetorEletrico.py::test_init_ccee PASSED
tests/test_dadosAbertosSetorEletrico.py::test_listar_produtos_disponiveis PASSED
tests/test_dadosAbertosSetorEletrico.py::test_baixar_dados_mockado PASSED
...
```

- ✅ Dica: Se você estiver usando Jupyter Notebook ou Google Colab, prefira usar o método await cliente.baixar_dados_produto_completo_async(...) para rodar de forma assíncrona.

## Observações Importantes

- Nem todos os datasets possuem dados acessíveis via API (`datastore_search`). Quando não disponíveis, o script mostra a URL para download manual.

- Alguns datasets podem conter muitos registros — a paginação automática com `limit` e `offset` evita estouro de memória.

- A classe trata de forma unificada três instituições distintas, facilitando reuso do código.


## Contribuições

Contribuições são muito bem-vindas!
Se você quiser sugerir melhorias, corrigir bugs ou adicionar novas funcionalidades, sinta-se à vontade para abrir uma issue ou pull request.

## 🚀 CI/CD e publicação no PyPI

O projeto usa GitHub Actions para automatizar validações e publicação de novas versões.

### Validação contínua

A esteira `CI` é executada em pushes para `main`/`master` e em pull requests. Ela:

- executa a suíte de testes em Python 3.8, 3.9, 3.10, 3.11 e 3.12;
- gera as distribuições do pacote com `python -m build`;
- valida os metadados gerados com `twine check`.

### Publicação de uma nova versão

A esteira `Publicar no PyPI` é disparada somente quando uma GitHub Release é publicada. Antes de publicar, ela roda os testes novamente, gera os artefatos `sdist` e `wheel` e usa a action `pypa/gh-action-pypi-publish` para enviar esses arquivos ao PyPI.

### Como a publicação no PyPI funciona

A publicação não usa senha nem token salvo no repositório. Ela usa **PyPI Trusted Publishing**, em que o PyPI confia no GitHub Actions deste repositório por OIDC.

O workflow não precisa saber o login/senha da sua conta PyPI. A ligação acontece em duas partes:

1. **Nome do projeto no PyPI:** vem do metadata do pacote em `setup.cfg`, no campo `name = dados-abertos-setor-eletrico`. É esse nome que define para qual projeto do PyPI os artefatos serão enviados.
2. **Permissão para publicar:** vem da configuração feita dentro do PyPI, na conta que administra o projeto. No PyPI, você cadastra este repositório GitHub como **Trusted Publisher** do projeto `dados-abertos-setor-eletrico`. Quando a action roda, o PyPI valida via OIDC se a execução veio exatamente do repositório, workflow e environment configurados.

Para isso funcionar, é necessário configurar uma vez no projeto do PyPI `dados-abertos-setor-eletrico` um publicador confiável com estes dados:

- **Owner/organization:** `diegonerii`
- **Repository name:** `Dados-Abertos-Setor-Eletrico-Brasileiro`
- **Workflow name:** `publish-pypi.yml`
- **Environment name:** `pypi`

Depois dessa configuração, o fluxo é:

1. Atualize o campo `version` em `setup.cfg`.
2. Faça commit e merge das alterações na branch principal.
3. Crie uma Release no GitHub com uma tag no padrão `vX.Y.Z`, por exemplo `v0.1.5`.
4. Publique a Release.
5. O GitHub Actions executa a action `Publicar no PyPI`; se os testes passarem, o pacote é enviado automaticamente para o PyPI.

> Para reduzir risco de publicação acidental, o workflow não possui disparo manual. Se quiser uma aprovação humana antes do envio, configure uma regra de proteção no ambiente `pypi` em **Settings > Environments** no GitHub.

> Se preferir usar token de API em vez de Trusted Publishing, configure um secret `PYPI_API_TOKEN` e adapte o passo `Publicar no PyPI` do workflow para enviar `password: ${{ secrets.PYPI_API_TOKEN }}`.


## Fontes oficiais

- **Portal de Dados Abertos da CCEE** → [Acessar Portal](https://dadosabertos.ccee.org.br/)

- **Portal de Dados Abertos da ONS** → [Acessar Portal](https://dados.ons.org.br/)

- **Portal de Dados Abertos da ANEEL** → [Acessar Portal](https://dadosabertos.aneel.gov.br/)

- **CKAN API Reference (oficial)** → [Acessar Documentação (Inglês)](https://docs.ckan.org/en/2.11/)



