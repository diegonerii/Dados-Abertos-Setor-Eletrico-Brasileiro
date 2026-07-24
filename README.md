# ⚡ Dados Abertos do Setor Elétrico

Biblioteca Python para consultar APIs CKAN de dados abertos do setor elétrico brasileiro nas instituições **CCEE**, **ONS** e **ANEEL**.

## Instalação

```bash
pip install dados-abertos-setor-eletrico
```

Para desenvolvimento local:

```bash
git clone https://github.com/diegonerii/Dados-Abertos-Setor-Eletrico-Brasileiro.git
cd Dados-Abertos-Setor-Eletrico-Brasileiro
python -m pip install -e .
```

## Inicialização

```python
from dadosAbertosSetorEletrico import dadosAbertosSetorEletrico

cliente = dadosAbertosSetorEletrico("ccee")
```

Instituições aceitas: `"ccee"`, `"ons"` e `"aneel"`. Os nomes podem ser informados em letras maiúsculas ou misturadas.

Por padrão, cada requisição usa `timeout=30.0` e envia um `User-Agent` identificável. Você pode customizar:

```python
cliente = dadosAbertosSetorEletrico(
    "aneel",
    timeout=10,
    headers={"X-Origem": "minha-aplicacao"},
)
```

## Listagem de produtos

`listar_produtos_disponiveis()` preserva a resposta completa do CKAN:

```python
resposta = cliente.listar_produtos_disponiveis()
produtos = resposta["result"]
print(produtos[:5])
```

A URL gerada para `package_list` segue sempre o formato sem barras duplicadas:

- `https://dadosabertos.ccee.org.br/api/3/action/package_list`
- `https://dados.ons.org.br/api/3/action/package_list`
- `https://dadosabertos.aneel.gov.br/api/3/action/package_list`

## Download síncrono

Use em scripts Python comuns, quando não há um event loop ativo:

```python
df = cliente.baixar_dados_produto_completo("nome-do-produto")
print(df.head())
```

O método retorna sempre um `pandas.DataFrame` quando executado com sucesso. Produtos ou recursos sem registros retornam `pd.DataFrame()` vazio.

## Download assíncrono

Use em Jupyter Notebook, Google Colab ou aplicações assíncronas:

```python
df = await cliente.baixar_dados_produto_completo_async("nome-do-produto")
```

O método síncrono `baixar_dados_produto_completo()` não retorna mais `asyncio.Task` quando existe um event loop ativo. Nesses ambientes ele levanta `RuntimeError` com orientação para usar `await cliente.baixar_dados_produto_completo_async(...)`, evitando tipos de retorno inconsistentes.

## Tratamento de erros

A biblioteca valida erros HTTP, JSON inválido e respostas CKAN com `success: false`.

```python
from dadosAbertosSetorEletrico import (
    DadosAbertosSetorEletricoError,
    dadosAbertosSetorEletrico,
)

cliente = dadosAbertosSetorEletrico("ons", timeout=10)

try:
    resposta = cliente.listar_produtos_disponiveis()
except DadosAbertosSetorEletricoError as exc:
    print(f"Falha ao consultar dados abertos: {exc}")
```

No download assíncrono, quando apenas alguns recursos falham, os recursos válidos são retornados e um `warnings.warn()` informa quais recursos falharam. Se todos os recursos falharem, uma exceção é lançada.

## Testes

Testes unitários usam mocks e não dependem da internet:

```bash
python -m pip install pytest
pytest -v
```

### Testes de integração opcionais

Os testes reais das APIs são desabilitados por padrão e não baixam bases grandes. Para executar apenas `package_list` real da CCEE, ONS e ANEEL:

```bash
RUN_INTEGRATION_TESTS=1 pytest -m integration -v
```

## Publicação para mantenedores

Não inclua credenciais em arquivos do repositório. Antes de publicar uma nova versão:

```bash
rm -rf build dist *.egg-info
python -m build
python -m twine check dist/*
python -m twine upload dist/*
```

A versão atual preparada para publicação é `0.1.5`.

## Fontes oficiais

- [Portal de Dados Abertos da CCEE](https://dadosabertos.ccee.org.br/)
- [Portal de Dados Abertos do ONS](https://dados.ons.org.br/)
- [Portal de Dados Abertos da ANEEL](https://dadosabertos.aneel.gov.br/)
- [CKAN API Reference](https://docs.ckan.org/en/2.11/)
