import requests
import json
import pandas as pd

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
            print("Instituição não encontrada!")

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

                if not response.get("success", False) or "result" not in response or "records" not in response["result"]:
                    print(f"Recurso {key} não está disponível via API estruturada.")
                    print("Faça o download manual pelo portal de dados abertos.")
                    print(f"URL do recurso: {self.host}/dataset/{produto}")
                    break  # quebra o while, vai para o próximo resource_id

                registros = response["result"]["records"]
                if not registros:
                    break

                df = pd.DataFrame(registros)
                lista_dfs.append(df)

                offset += limite
                if offset >= response["result"].get("total", 0):
                    break
        
        return pd.concat(lista_dfs, ignore_index=True) if lista_dfs else None


carga = dadosAbertosSetorEletrico()
carga.baixar_dados_produto_completo("parcela_carga_consumo")