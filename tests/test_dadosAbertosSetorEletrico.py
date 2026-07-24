import asyncio
import os
from unittest.mock import Mock, patch

import httpx
import pandas as pd
import pytest
import requests

from dadosAbertosSetorEletrico import (
    DadosAbertosSetorEletricoError,
    DadosAbertosSetorEletricoHTTPError,
    DadosAbertosSetorEletricoResponseError,
    dadosAbertosSetorEletrico,
)


def make_response(payload=None, status_code=200, json_error=None):
    response = Mock()
    response.status_code = status_code
    response.json.side_effect = json_error if json_error else None
    response.json.return_value = payload
    if status_code >= 400:
        http_error = requests.HTTPError(f"{status_code} error")
        http_error.response = response
        response.raise_for_status.side_effect = http_error
    else:
        response.raise_for_status.return_value = None
    return response


def test_init_instituicoes_e_case_insensitive():
    assert dadosAbertosSetorEletrico("ccee").host == "https://dadosabertos.ccee.org.br"
    assert dadosAbertosSetorEletrico("ONS").host == "https://dados.ons.org.br"
    assert dadosAbertosSetorEletrico("AnEeL").host == "https://dadosabertos.aneel.gov.br"


def test_init_invalido():
    with pytest.raises(ValueError, match="Instituição não encontrada"):
        dadosAbertosSetorEletrico("xyz")


def test_construcao_correta_urls():
    assert dadosAbertosSetorEletrico("ccee")._build_url("package_list") == "https://dadosabertos.ccee.org.br/api/3/action/package_list"
    assert dadosAbertosSetorEletrico("ons")._build_url("/package_list") == "https://dados.ons.org.br/api/3/action/package_list"
    assert dadosAbertosSetorEletrico("aneel")._build_url("package_list") == "https://dadosabertos.aneel.gov.br/api/3/action/package_list"


@patch("dadosAbertosSetorEletrico.requests.get")
def test_package_list_com_sucesso(mock_get):
    mock_get.return_value = make_response({"success": True, "result": ["produto1", "produto2"]})
    cliente = dadosAbertosSetorEletrico("ccee")
    resposta = cliente.listar_produtos_disponiveis()
    assert resposta["result"] == ["produto1", "produto2"]
    mock_get.assert_called_once_with(
        "https://dadosabertos.ccee.org.br/api/3/action/package_list",
        params=None,
        timeout=30.0,
        headers=cliente.headers,
    )


@pytest.mark.parametrize("status", [404, 429])
@patch("dadosAbertosSetorEletrico.requests.get")
def test_erro_http(mock_get, status):
    mock_get.return_value = make_response(status_code=status)
    with pytest.raises(DadosAbertosSetorEletricoHTTPError, match=f"Status HTTP: {status}"):
        dadosAbertosSetorEletrico("ccee").listar_produtos_disponiveis()


@patch("dadosAbertosSetorEletrico.requests.get")
def test_timeout(mock_get):
    mock_get.side_effect = requests.Timeout("tempo esgotado")
    with pytest.raises(DadosAbertosSetorEletricoHTTPError, match="tempo esgotado"):
        dadosAbertosSetorEletrico("ons").listar_produtos_disponiveis()


@patch("dadosAbertosSetorEletrico.requests.get")
def test_conexao_recusada(mock_get):
    mock_get.side_effect = requests.ConnectionError("conexão recusada")
    with pytest.raises(DadosAbertosSetorEletricoHTTPError, match="conexão recusada"):
        dadosAbertosSetorEletrico("aneel").listar_produtos_disponiveis()


@patch("dadosAbertosSetorEletrico.requests.get")
def test_json_invalido(mock_get):
    mock_get.return_value = make_response(json_error=ValueError("json inválido"))
    with pytest.raises(DadosAbertosSetorEletricoResponseError, match="json inválido"):
        dadosAbertosSetorEletrico("ccee").listar_produtos_disponiveis()


@patch("dadosAbertosSetorEletrico.requests.get")
def test_ckan_success_false(mock_get):
    mock_get.return_value = make_response({"success": False, "error": {"message": "falha"}})
    with pytest.raises(DadosAbertosSetorEletricoResponseError, match="success=false"):
        dadosAbertosSetorEletrico("ccee").listar_produtos_disponiveis()


@patch("dadosAbertosSetorEletrico.requests.get")
def test_package_show_sem_resources(mock_get):
    mock_get.return_value = make_response({"success": True, "result": {}})
    cliente = dadosAbertosSetorEletrico("ccee")
    with pytest.raises(DadosAbertosSetorEletricoResponseError, match="resources ausente"):
        cliente._dadosAbertosSetorEletrico__buscar_resource_ids_por_produto("produto")


@patch("dadosAbertosSetorEletrico.requests.get")
def test_multiplos_resources(mock_get):
    mock_get.return_value = make_response({"success": True, "result": {"resources": [{"id": "r1"}, {"id": "r2"}]}})
    cliente = dadosAbertosSetorEletrico("ccee")
    assert cliente._dadosAbertosSetorEletrico__buscar_resource_ids_por_produto("produto") == ["r1", "r2"]


def test_paginacao_mais_de_uma_pagina():
    async def run():
        cliente = dadosAbertosSetorEletrico("ccee")
        chamadas = []

        async def fake_fetch(client, resource_id, offset, limit):
            chamadas.append(offset)
            if offset == 0:
                return [{"a": 1}], 2
            if offset == 1:
                return [{"a": 2}], 2
            return [], 2

        cliente._dadosAbertosSetorEletrico__fetch_offset = fake_fetch
        dados = await cliente._dadosAbertosSetorEletrico__baixar_resource_completo(Mock(), "r1", limit=1)
        assert dados == [{"a": 1}, {"a": 2}]
        assert chamadas == [0, 1]

    asyncio.run(run())


def test_recurso_vazio_retorna_dataframe_vazio():
    async def run():
        cliente = dadosAbertosSetorEletrico("ccee")
        cliente._dadosAbertosSetorEletrico__buscar_resource_ids_por_produto = lambda produto: ["vazio"]

        async def fake_resource(client, resource_id):
            return []

        cliente._dadosAbertosSetorEletrico__baixar_resource_completo = fake_resource
        df = await cliente.baixar_dados_produto_completo_async("produto")
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    asyncio.run(run())


def test_falha_em_apenas_um_recurso_emite_warning():
    async def run():
        cliente = dadosAbertosSetorEletrico("ccee")
        cliente._dadosAbertosSetorEletrico__buscar_resource_ids_por_produto = lambda produto: ["ok", "erro"]

        async def fake_resource(client, resource_id):
            if resource_id == "erro":
                raise DadosAbertosSetorEletricoHTTPError("falha")
            return [{"coluna": "ok"}]

        cliente._dadosAbertosSetorEletrico__baixar_resource_completo = fake_resource
        with pytest.warns(RuntimeWarning, match="erro"):
            df = await cliente.baixar_dados_produto_completo_async("produto")
        assert df["coluna"].tolist() == ["ok"]

    asyncio.run(run())


def test_falha_em_todos_os_recursos():
    async def run():
        cliente = dadosAbertosSetorEletrico("ccee")
        cliente._dadosAbertosSetorEletrico__buscar_resource_ids_por_produto = lambda produto: ["r1", "r2"]

        async def fake_resource(client, resource_id):
            raise DadosAbertosSetorEletricoHTTPError("falha")

        cliente._dadosAbertosSetorEletrico__baixar_resource_completo = fake_resource
        with pytest.raises(DadosAbertosSetorEletricoError, match="Nenhum resource"):
            await cliente.baixar_dados_produto_completo_async("produto")

    asyncio.run(run())


def test_metodo_sincrono_fora_de_event_loop():
    cliente = dadosAbertosSetorEletrico("ccee")

    async def fake_async(produto):
        return pd.DataFrame([{"produto": produto}])

    cliente.baixar_dados_produto_completo_async = fake_async
    df = cliente.baixar_dados_produto_completo("abc")
    assert isinstance(df, pd.DataFrame)
    assert df.iloc[0]["produto"] == "abc"


def test_metodo_sincrono_dentro_de_event_loop():
    async def run():
        cliente = dadosAbertosSetorEletrico("ccee")
        with pytest.raises(RuntimeError, match="event loop ativo"):
            cliente.baixar_dados_produto_completo("abc")

    asyncio.run(run())


def test_headers_customizados_e_user_agent_padrao():
    cliente = dadosAbertosSetorEletrico("ccee", headers={"X-Teste": "1"})
    assert cliente.headers["User-Agent"] == "dados-abertos-setor-eletrico/0.1.5"
    assert cliente.headers["X-Teste"] == "1"


def test_user_agent_customizado():
    cliente = dadosAbertosSetorEletrico("ccee", headers={"User-Agent": "custom"})
    assert cliente.headers["User-Agent"] == "custom"


def test_datastore_success_false():
    async def run():
        request = httpx.Request("GET", "https://example.test")
        response = httpx.Response(200, json={"success": False, "error": {"message": "falha"}}, request=request)

        class Transport(httpx.AsyncBaseTransport):
            async def handle_async_request(self, request):
                return response

        cliente = dadosAbertosSetorEletrico("ccee")
        async with httpx.AsyncClient(transport=Transport()) as client:
            with pytest.raises(DadosAbertosSetorEletricoResponseError, match="success=false"):
                await cliente._dadosAbertosSetorEletrico__fetch_offset(client, "r1", 0, 100)

    asyncio.run(run())


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("RUN_INTEGRATION_TESTS") != "1", reason="defina RUN_INTEGRATION_TESTS=1")
@pytest.mark.parametrize("instituicao", ["ccee", "ons", "aneel"])
def test_integration_package_list(instituicao):
    resposta = dadosAbertosSetorEletrico(instituicao, timeout=10).listar_produtos_disponiveis()
    assert resposta["success"] is True
    assert isinstance(resposta["result"], list)
