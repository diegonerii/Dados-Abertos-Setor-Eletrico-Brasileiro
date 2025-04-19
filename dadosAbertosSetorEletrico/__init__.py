import asyncio
import httpx
import pandas as pd
import requests

class dadosAbertosSetorEletrico:
    def __init__(self, instituicao: str):
        self.api = '/api/3/action/'
        if str.lower(instituicao) == "ccee":
            self.host = 'https://dadosabertos.ccee.org.br'
        elif str.lower(instituicao) == "ons":
            self.host = 'https://dados.ons.org.br'
        elif str.lower(instituicao) == "aneel":
            self.host = 'https://dadosabertos.aneel.gov.br/'
        else:
            raise ValueError("Instituição não encontrada!")

    def listar_produtos_disponiveis(self):
        r = requests.get(self.host + self.api + "package_list")
        return r.json()

    def __buscar_resource_ids_por_produto(self, produto: str):
        r = requests.get(self.host + self.api + f"package_show?id={produto}")
        return [item['id'] for item in r.json()['result']['resources'] if 'id' in item]

    async def __fetch_offset(self, client, resource_id, offset, limit):
        url = f"{self.host}{self.api}datastore_search?resource_id={resource_id}&limit={limit}&offset={offset}"
        try:
            resp = await client.get(url, timeout=30)
            data = resp.json()
            return data.get("result", {}).get("records", [])
        except Exception as e:
            print(f"[{resource_id}] Offset {offset} falhou: {e}")
            return []

    async def __baixar_resource_completo(self, client, resource_id, limit=10000):
        offset = 0
        todos_registros = []
        while True:
            registros = await self.__fetch_offset(client, resource_id, offset, limit)
            if not registros:
                break
            todos_registros.extend(registros)
            offset += limit
        return todos_registros

    async def baixar_dados_produto_completo_async(self, produto: str):
        print("Iniciando download assíncrono...")
        ids = self.__buscar_resource_ids_por_produto(produto)

        async with httpx.AsyncClient() as client:
            tarefas = [self.__baixar_resource_completo(client, rid) for rid in ids]
            resultados = await asyncio.gather(*tarefas)

        todos_registros = [item for sublist in resultados for item in sublist]
        return pd.DataFrame(todos_registros) if todos_registros else None

    def baixar_dados_produto_completo(self, produto: str):
        try:
            loop = asyncio.get_running_loop()
            return loop.create_task(self.baixar_dados_produto_completo_async(produto))
        except RuntimeError:
            return asyncio.run(self.baixar_dados_produto_completo_async(produto))
