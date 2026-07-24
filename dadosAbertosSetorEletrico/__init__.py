"""Cliente para APIs CKAN de dados abertos do setor elétrico brasileiro."""

import asyncio
import warnings
from typing import Any, Dict, List, Optional, Tuple

import httpx
import pandas as pd
import requests

__version__ = "0.1.5"


class DadosAbertosSetorEletricoError(Exception):
    """Erro base da biblioteca dados-abertos-setor-eletrico."""


class DadosAbertosSetorEletricoHTTPError(DadosAbertosSetorEletricoError):
    """Erro em comunicação HTTP com uma API CKAN."""


class DadosAbertosSetorEletricoResponseError(DadosAbertosSetorEletricoError):
    """Erro de estrutura ou conteúdo de resposta CKAN."""


class dadosAbertosSetorEletrico:
    """Cliente para consultar CCEE, ONS ou ANEEL via API CKAN.

    Parameters
    ----------
    instituicao:
        Nome da instituição: ``ccee``, ``ons`` ou ``aneel``. A comparação não
        diferencia maiúsculas de minúsculas.
    timeout:
        Tempo máximo, em segundos, para cada requisição HTTP.
    headers:
        Cabeçalhos HTTP adicionais. Quando ``User-Agent`` não for informado,
        a biblioteca envia um valor padrão identificável.
    """

    _HOSTS = {
        "ccee": "https://dadosabertos.ccee.org.br",
        "ons": "https://dados.ons.org.br",
        "aneel": "https://dadosabertos.aneel.gov.br",
    }

    def __init__(
        self,
        instituicao: str,
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.instituicao = str(instituicao).lower()
        if self.instituicao not in self._HOSTS:
            validas = ", ".join(sorted(self._HOSTS))
            raise ValueError(f"Instituição não encontrada: {instituicao!r}. Use uma de: {validas}.")

        self.host = self._HOSTS[self.instituicao]
        self.api = "/api/3/action/"
        self.timeout = timeout
        self.headers = {"User-Agent": f"dados-abertos-setor-eletrico/{__version__}"}
        if headers:
            self.headers.update(headers)

    def _build_url(self, endpoint: str) -> str:
        """Monta uma URL CKAN sem barras duplicadas entre host, API e endpoint."""
        return f"{self.host.rstrip('/')}/{self.api.strip('/')}/{endpoint.lstrip('/')}"

    def _format_error(self, endpoint: str, original: BaseException, status_code: Optional[int] = None) -> str:
        status = f" Status HTTP: {status_code}." if status_code is not None else ""
        return (
            f"Erro ao consultar {self.instituicao.upper()} no endpoint {endpoint!r}."
            f"{status} Erro original: {original}"
        )

    def _get_json(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Executa GET síncrono e retorna JSON validado no nível HTTP."""
        url = self._build_url(endpoint)
        try:
            response = requests.get(url, params=params, timeout=self.timeout, headers=self.headers)
            response.raise_for_status()
            data = response.json()
        except requests.Timeout as exc:
            raise DadosAbertosSetorEletricoHTTPError(self._format_error(endpoint, exc)) from exc
        except requests.ConnectionError as exc:
            raise DadosAbertosSetorEletricoHTTPError(self._format_error(endpoint, exc)) from exc
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else response.status_code
            raise DadosAbertosSetorEletricoHTTPError(
                self._format_error(endpoint, exc, status_code)
            ) from exc
        except ValueError as exc:
            raise DadosAbertosSetorEletricoResponseError(
                self._format_error(endpoint, exc)
            ) from exc

        if not isinstance(data, dict):
            raise DadosAbertosSetorEletricoResponseError(
                f"Resposta inválida de {self.instituicao.upper()} no endpoint {endpoint!r}: JSON não é objeto."
            )
        return data

    def _validate_success(self, data: Dict[str, Any], endpoint: str) -> Any:
        if data.get("success") is False:
            raise DadosAbertosSetorEletricoResponseError(
                f"API CKAN retornou success=false para {self.instituicao.upper()} no endpoint {endpoint!r}: "
                f"{data.get('error')}"
            )
        if data.get("success") is not True or "result" not in data:
            raise DadosAbertosSetorEletricoResponseError(
                f"Resposta CKAN inválida de {self.instituicao.upper()} no endpoint {endpoint!r}: "
                "esperado success=true e campo result."
            )
        return data["result"]

    def listar_produtos_disponiveis(self) -> Dict[str, Any]:
        """Lista produtos disponíveis e retorna a resposta CKAN completa."""
        endpoint = "package_list"
        data = self._get_json(endpoint)
        result = self._validate_success(data, endpoint)
        if not isinstance(result, list):
            raise DadosAbertosSetorEletricoResponseError(
                f"Resposta CKAN inválida de {self.instituicao.upper()} no endpoint {endpoint!r}: result deve ser lista."
            )
        return data

    def __buscar_resource_ids_por_produto(self, produto: str) -> List[str]:
        """Retorna os IDs dos resources de um produto CKAN."""
        endpoint = "package_show"
        data = self._get_json(endpoint, params={"id": produto})
        result = self._validate_success(data, endpoint)
        resources = result.get("resources") if isinstance(result, dict) else None
        if resources is None:
            raise DadosAbertosSetorEletricoResponseError(
                f"Resposta CKAN inválida de {self.instituicao.upper()} no endpoint {endpoint!r}: resources ausente."
            )
        if not isinstance(resources, list):
            raise DadosAbertosSetorEletricoResponseError(
                f"Resposta CKAN inválida de {self.instituicao.upper()} no endpoint {endpoint!r}: resources deve ser lista."
            )
        return [item["id"] for item in resources if isinstance(item, dict) and item.get("id")]

    async def __fetch_offset(self, client: httpx.AsyncClient, resource_id: str, offset: int, limit: int) -> Tuple[List[Dict[str, Any]], Optional[int]]:
        endpoint = "datastore_search"
        try:
            response = await client.get(
                self._build_url(endpoint),
                params={"resource_id": resource_id, "limit": limit, "offset": offset},
            )
            response.raise_for_status()
            data = response.json()
        except httpx.TimeoutException as exc:
            raise DadosAbertosSetorEletricoHTTPError(self._format_error(endpoint, exc)) from exc
        except httpx.HTTPStatusError as exc:
            raise DadosAbertosSetorEletricoHTTPError(
                self._format_error(endpoint, exc, exc.response.status_code)
            ) from exc
        except httpx.HTTPError as exc:
            raise DadosAbertosSetorEletricoHTTPError(self._format_error(endpoint, exc)) from exc
        except ValueError as exc:
            raise DadosAbertosSetorEletricoResponseError(self._format_error(endpoint, exc)) from exc

        result = self._validate_success(data, endpoint)
        records = result.get("records") if isinstance(result, dict) else None
        if records is None or not isinstance(records, list):
            raise DadosAbertosSetorEletricoResponseError(
                f"Resposta CKAN inválida de {self.instituicao.upper()} no endpoint {endpoint!r}: records ausente ou inválido."
            )
        total = result.get("total")
        return records, total if isinstance(total, int) else None

    async def __baixar_resource_completo(self, client: httpx.AsyncClient, resource_id: str, limit: int = 10000) -> List[Dict[str, Any]]:
        offset = 0
        todos_registros: List[Dict[str, Any]] = []
        while True:
            registros, total = await self.__fetch_offset(client, resource_id, offset, limit)
            if not registros:
                break
            todos_registros.extend(registros)
            offset += limit
            if total is not None and offset >= total:
                break
        return todos_registros

    async def baixar_dados_produto_completo_async(self, produto: str) -> pd.DataFrame:
        """Baixa todos os resources de um produto e retorna sempre um DataFrame.

        Se apenas alguns resources falharem, os dados válidos são retornados e
        um ``warnings.warn`` informa os resources com falha. Se todos falharem,
        uma exceção agregada é lançada. Produtos sem registros retornam
        ``pandas.DataFrame()``.
        """
        ids = self.__buscar_resource_ids_por_produto(produto)
        if not ids:
            return pd.DataFrame()

        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            resultados = await asyncio.gather(
                *(self.__baixar_resource_completo(client, rid) for rid in ids),
                return_exceptions=True,
            )

        todos_registros: List[Dict[str, Any]] = []
        falhas = []
        for resource_id, resultado in zip(ids, resultados):
            if isinstance(resultado, Exception):
                falhas.append(f"{resource_id}: {resultado}")
            else:
                todos_registros.extend(resultado)

        if falhas and len(falhas) == len(ids):
            raise DadosAbertosSetorEletricoError(
                f"Nenhum resource de {produto!r} foi baixado com sucesso. Falhas: " + "; ".join(falhas)
            )
        if falhas:
            warnings.warn(
                f"Alguns resources de {produto!r} falharam e foram ignorados: " + "; ".join(falhas),
                RuntimeWarning,
                stacklevel=2,
            )
        return pd.DataFrame(todos_registros)

    def baixar_dados_produto_completo(self, produto: str) -> pd.DataFrame:
        """Versão síncrona do download completo.

        Em ambientes com event loop ativo (por exemplo, Jupyter), este método
        levanta ``RuntimeError`` para evitar retornar ``asyncio.Task``. Use
        ``await cliente.baixar_dados_produto_completo_async(produto)`` nesses
        casos.
        """
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.baixar_dados_produto_completo_async(produto))
        raise RuntimeError(
            "Há um event loop ativo. Use: await cliente.baixar_dados_produto_completo_async(produto)."
        )
