import requests
import json
import pandas as pd

class dadosAbertosSetorEletrico:
    def __init__(self):
        
        self.host = 'https://dadosabertos.ccee.org.br'
        self.api = '/api/3/action/'

    def listar_produtos_disponiveis(self):
        r = requests.get(self.host+self.api+f"package_list")
        return r.json()

    def __buscar_resource_ids_por_produto(self, produto: str):
        r = requests.get(self.host+self.api+f"package_show?id={produto}")
        ids = [item['id'] for item in r.json()['result']['resources'] if 'id' in item]
        return ids


    def baixar_dados_produto_completo(self, produto: str):
        limite = 10000
        lista_dfs = []
        print("Preparando para baixar os arquivos...")
        
        for key in self.__buscar_resource_ids_por_produto(produto):
            offset = 0
            while True:
                r = requests.get(
                    self.host + self.api + f"datastore_search?resource_id={key}&limit={limite}&offset={offset}"
                )
                response = r.json()

                registros = response['result']['records']
                if not registros:
                    break

                df = pd.DataFrame(registros)
                lista_dfs.append(df)

                offset += limite
                if offset >= response['result'].get('total', 0):
                    break
        
        return pd.concat(lista_dfs, ignore_index=True)


carga = dadosAbertosSetorEletrico()
carga.baixar_dados_produto_completo("parcela_carga_consumo")