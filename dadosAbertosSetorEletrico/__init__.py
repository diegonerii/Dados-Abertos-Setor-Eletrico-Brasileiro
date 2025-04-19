import asyncio      
import httpx        
import pandas as pd 
import requests     


class dadosAbertosSetorEletrico:

    def __init__(self, instituicao: str):
        """
        Inicializa a classe com a instituição desejada: CCEE, ONS ou ANEEL.
        Define a URL base (host) de onde os dados serão buscados.
        """
        self.api = '/api/3/action/'  # Caminho comum da API CKAN usada por todas as instituições

        # Define a URL base dependendo da instituição informada
        if str.lower(instituicao) == "ccee":
            self.host = 'https://dadosabertos.ccee.org.br'
        elif str.lower(instituicao) == "ons":
            self.host = 'https://dados.ons.org.br'
        elif str.lower(instituicao) == "aneel":
            self.host = 'https://dadosabertos.aneel.gov.br/'
        else:
            raise ValueError("Instituição não encontrada!")  # Gera erro se a instituição for inválida

    def listar_produtos_disponiveis(self):
        """
        Retorna uma lista com todos os produtos disponíveis na API.
        Cada produto representa um conjunto de dados públicos que pode ser consultado.
        """
        r = requests.get(self.host + self.api + "package_list")
        return r.json()

    def __buscar_resource_ids_por_produto(self, produto: str):
        """
        Retorna os IDs dos arquivos (resources) relacionados a um produto.
        Cada resource_id representa uma tabela acessível via API.
        """
        r = requests.get(self.host + self.api + f"package_show?id={produto}")
        return [item['id'] for item in r.json()['result']['resources'] if 'id' in item]

    async def __fetch_offset(self, client, resource_id, offset, limit):
        """
        Função assíncrona que busca um pedaço (pagina) dos dados de um resource_id específico.
        Trabalha com paginação (offset) e número máximo de registros (limit).
        """
        url = f"{self.host}{self.api}datastore_search?resource_id={resource_id}&limit={limit}&offset={offset}"
        try:
            resp = await client.get(url, timeout=30)  # Realiza a requisição de forma assíncrona
            data = resp.json()
            return data.get("result", {}).get("records", [])  # Retorna apenas os dados (registros)
        except Exception as e:
            print(f"[{resource_id}] Offset {offset} falhou: {e}")
            return []  # Retorna lista vazia em caso de erro

    async def __baixar_resource_completo(self, client, resource_id, limit=10000):
        """
        Função assíncrona que baixa todos os dados de um único resource_id, lidando com paginação.
        """
        offset = 0
        todos_registros = []

        # Laço que busca página por página (de 10 mil em 10 mil)
        while True:
            registros = await self.__fetch_offset(client, resource_id, offset, limit)
            if not registros:
                break  # Para quando não houver mais dados
            todos_registros.extend(registros)  # Junta os dados
            offset += limit  # Vai para a próxima página

        return todos_registros

    async def baixar_dados_produto_completo_async(self, produto: str):
        """
        Função principal assíncrona para baixar todos os dados de um produto.
        Acessa vários resource_ids em paralelo e junta os dados num único DataFrame (tabela).
        """
        print("Iniciando download assíncrono...")
        ids = self.__buscar_resource_ids_por_produto(produto)  # Busca os IDs dos arquivos (resources)

        # Cria um cliente HTTP assíncrono
        async with httpx.AsyncClient() as client:
            # Cria uma lista de tarefas assíncronas, uma para cada resource_id
            tarefas = [self.__baixar_resource_completo(client, rid) for rid in ids]
            # Executa todas as tarefas ao mesmo tempo
            resultados = await asyncio.gather(*tarefas)

        # Junta todos os registros em uma única lista
        todos_registros = [item for sublist in resultados for item in sublist]

        # Retorna um DataFrame com os dados (ou None se não houver nada)
        return pd.DataFrame(todos_registros) if todos_registros else None

    def baixar_dados_produto_completo(self, produto: str):
        """
        Versão compatível com ambientes normais (como scripts Python).
        Detecta se já existe um loop assíncrono rodando (como no Jupyter) e se adapta.
        """
        try:
            # Se já existe um loop (ex: Jupyter), cria uma tarefa
            loop = asyncio.get_running_loop()
            return loop.create_task(self.baixar_dados_produto_completo_async(produto))
        except RuntimeError:
            # Caso contrário, executa o método assíncrono do zero
            return asyncio.run(self.baixar_dados_produto_completo_async(produto))
