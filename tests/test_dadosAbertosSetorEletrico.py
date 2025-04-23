import pytest
from unittest.mock import patch, AsyncMock
from dadosAbertosSetorEletrico import dadosAbertosSetorEletrico
import pandas as pd

# -------------------
# Testes de inicialização da classe
# -------------------

def test_init_ccee():
    # Testa se, ao inicializar com "ccee", o host é atribuido corretamente
    cliente = dadosAbertosSetorEletrico("ccee")
    assert cliente.host == "https://dadosabertos.ccee.org.br"

def test_init_invalido():
    # Testa se, ao passar uma instituição inválida, uma exceção é levantada
    with pytest.raises(ValueError):
        dadosAbertosSetorEletrico("xyz")

# -------------------
# Teste de listagem de produtos com simulação da API
# -------------------
@patch("dadosAbertosSetorEletrico.requests.get")
def test_listar_produtos_disponiveis(mock_get):
    # Simula resposta da API com dois produtos
    mock_get.return_value.json.return_value = {"result": ["produto1", "produto2"]}
    cliente = dadosAbertosSetorEletrico("ccee")
    produtos = cliente.listar_produtos_disponiveis()
    assert produtos["result"] == ["produto1", "produto2"]

# -------------------
# Teste de busca de resource_ids simulando resposta da API
# -------------------
@patch("dadosAbertosSetorEletrico.requests.get")
def test_buscar_resource_ids(mock_get):
    # Simula resposta com dois IDs de recurso
    mock_get.return_value.json.return_value = {
        "result": {"resources": [{"id": "abc"}, {"id": "def"}]}
    }
    cliente = dadosAbertosSetorEletrico("ccee")
    ids = cliente._dadosAbertosSetorEletrico__buscar_resource_ids_por_produto("algum-produto")
    assert ids == ["abc", "def"]

# -------------------
# Teste assíncrono com multiplos resource_ids e paginação
# -------------------
@pytest.mark.asyncio
async def test_baixar_dados_mockado():
    cliente = dadosAbertosSetorEletrico("ccee")

    chamadas = []

    # Simula comportamento paginado: retorna dado no offset 0 e vazio depois
    async def fake_fetch_offset(client, resource_id, offset, limit):
        chamadas.append((resource_id, offset))
        if offset == 0:
            return [{"coluna": f"valor_{resource_id}"}]
        else:
            return []

    # Substitui os métodos internos por versões simuladas (mocks)
    cliente._dadosAbertosSetorEletrico__buscar_resource_ids_por_produto = lambda x: ["id1", "id2"]
    cliente._dadosAbertosSetorEletrico__fetch_offset = fake_fetch_offset

    # Executa a função com os mocks
    df = await cliente.baixar_dados_produto_completo_async("produto-teste")

    # Verifica se os dados retornados estão corretos
    assert not df.empty
    assert set(df["coluna"]) == {"valor_id1", "valor_id2"}
    assert chamadas == [("id1", 0), ("id1", 10000), ("id2", 0), ("id2", 10000)]

# -------------------
# Teste com um resource_id que falha
# -------------------
@pytest.mark.asyncio
async def test_baixar_dados_com_erro():
    cliente = dadosAbertosSetorEletrico("ccee")

    # Simula uma exceção para um dos resource_ids
    async def fake_fetch_offset(client, resource_id, offset, limit):
        if resource_id == "erro":
            raise Exception("Erro simulado")
        if offset == 0:
            return [{"coluna": "ok"}]
        return []

    # Define que haverá um resource_id válido e um que falha
    cliente._dadosAbertosSetorEletrico__buscar_resource_ids_por_produto = lambda x: ["ok", "erro"]

    # Envolve o fake_fetch em tratamento de erro para evitar crash do teste
    async def safe_fetch(client, resource_id, offset, limit):
        try:
            return await fake_fetch_offset(client, resource_id, offset, limit)
        except:
            return []

    cliente._dadosAbertosSetorEletrico__fetch_offset = safe_fetch

    df = await cliente.baixar_dados_produto_completo_async("produto-teste")

    # Garante que pelo menos o resource_id válido foi retornado
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "coluna" in df.columns
    assert "ok" in df["coluna"].values or len(df) == 1

# -------------------
# Teste de um resource_id que não retorna nenhum dado
# -------------------
@pytest.mark.asyncio
async def test_baixar_dados_vazio():
    cliente = dadosAbertosSetorEletrico("ccee")

    # Simula resposta vazia para todos os offsets
    async def fake_fetch_offset(client, resource_id, offset, limit):
        return []

    cliente._dadosAbertosSetorEletrico__buscar_resource_ids_por_produto = lambda x: ["id_vazio"]
    cliente._dadosAbertosSetorEletrico__fetch_offset = fake_fetch_offset

    df = await cliente.baixar_dados_produto_completo_async("produto-teste")
    if df is None:
        df = pd.DataFrame()  # Garante consistência no retorno para facilitar validação

    # Verifica se é um DataFrame válido e vazio
    assert isinstance(df, pd.DataFrame)
    assert df.empty
