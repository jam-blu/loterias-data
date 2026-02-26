import requests
import json
import os
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class AtualizadorHistorico:
    def __init__(self):
        caminho_base = os.path.dirname(os.path.abspath(__file__))
        self.arquivo_historico = os.path.join(caminho_base, "historico_total.json")
        self.base_url = "https://loteriascaixa-api.herokuapp.com/api/"
        self.session = requests.Session()

    def ajustar_super_sete(self, dezenas):
        return [f"{i+1}{valor}" for i, valor in enumerate(dezenas)]

    def processar_concurso(self, dados, loteria_id):
        dezenas = dados.get('dezenas', [])
        if loteria_id == "supersete":
            dezenas = self.ajustar_super_sete(dezenas)
        especial = []
        if loteria_id == "maismilionaria": especial = dados.get('trevos', [])
        elif loteria_id == "timemania": especial = [dados.get('timeCoracao', "")]
        elif loteria_id == "diadesorte": especial = [dados.get('mesSorte', "")]
        return {
            "concurso": dados.get('concurso'), 
            "data": dados.get('data'), 
            "dezenas": dezenas, 
            "especial": especial
        }

    def atualizar(self):
        if not os.path.exists(self.arquivo_historico):
            print(f"❌ Arquivo não encontrado!")
            return

        with open(self.arquivo_historico, "r", encoding="utf-8") as f:
            historico = json.load(f)

        for loteria in historico.keys():
            # Pega o último concurso que já temos no histórico
            ultimo_no_arquivo = int(historico[loteria][0]['concurso'])
            
            print(f"\n📊 {loteria}: Iniciando busca a partir do #{ultimo_no_arquivo + 1}")
            
            novos = []
            proximo = ultimo_no_arquivo + 1
            tentativas_vazias = 0

            # Lógica de Busca Incremental: Tenta o próximo até a API falhar 2 vezes
            while tentativas_vazias < 2:
                print(f"  -> Tentando concurso #{proximo}...", end="\r")
                try:
                    res = self.session.get(f"{self.base_url}{loteria}/{proximo}", timeout=15, verify=False)
                    if res.status_code == 200:
                        dados_concurso = res.json()
                        novos.append(self.processar_concurso(dados_concurso, loteria))
                        proximo += 1
                        tentativas_vazias = 0
                        time.sleep(0.3) # Gentileza com o servidor
                    else:
                        tentativas_vazias += 1
                        proximo += 1
                except:
                    break

            if novos:
                # Ordena para garantir que o mais novo fique no topo (reverse=True)
                novos.sort(key=lambda x: int(x['concurso']), reverse=True)
                historico[loteria] = novos + historico[loteria]
                print(f"✅ {loteria}: +{len(novos)} concursos novos adicionados.")
            else:
                print(f"✅ {loteria}: Já está totalmente atualizada.")

        # Salva o arquivo histórico atualizado
        with open(self.arquivo_historico, "w", encoding="utf-8") as f:
            json.dump(historico, f, indent=4, ensure_ascii=False)
        print("\n✨ Histórico Total atualizado com sucesso.")

if __name__ == "__main__":
    AtualizadorHistorico().atualizar()
