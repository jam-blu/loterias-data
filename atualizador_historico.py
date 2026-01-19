import requests
import json
import os
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class AtualizadorHistorico:
    def __init__(self):
        self.arquivo_historico = "historico_total.json"
        self.base_url = "https://loteriascaixa-api.herokuapp.com/api/"
        self.session = requests.Session()
        # --- CONFIGURAÇÃO DO TESTE ---
        self.ALVO_CONCURSO = 150000 

    def ajustar_super_sete(self, dezenas):
        return [f"{i+1}{valor}" for i, valor in enumerate(dezenas)]

    def obter_ultimo_real(self, loteria):
        """Pergunta à API qual o concurso mais recente que existe de verdade"""
        try:
            res = self.session.get(f"{self.base_url}{loteria}/latest", timeout=10, verify=False)
            if res.status_code == 200:
                return int(res.json()['concurso'])
        except:
            return 99999 # Se falhar, assume um número alto
        return 99999

    def processar_concurso(self, dados, loteria_id):
        dezenas = dados.get('dezenas', [])
        if loteria_id == "supersete":
            dezenas = self.ajustar_super_sete(dezenas)
        especial = []
        if loteria_id == "maismilionaria": especial = dados.get('trevos', [])
        elif loteria_id == "timemania": especial = [dados.get('timeCoracao', "")]
        elif loteria_id == "diadesorte": especial = [dados.get('mesSorte', "")]
        return {"concurso": dados.get('concurso'), "data": dados.get('data'), "dezenas": dezenas, "especial": especial}

    def atualizar(self):
        if not os.path.exists(self.arquivo_historico):
            print("❌ Arquivo não encontrado.")
            return

        with open(self.arquivo_historico, "r", encoding="utf-8") as f:
            historico = json.load(f)

        for loteria in historico.keys():
            ultimo_no_arquivo = int(historico[loteria][0]['concurso'])
            ultimo_na_api = self.obter_ultimo_real(loteria)
            
            # Define o limite: ou o que você pediu (500) ou o que existe na API
            limite_real = min(self.ALVO_CONCURSO, ultimo_na_api)
            
            print(f"\n📊 {loteria}: No arquivo: #{ultimo_no_arquivo} | Na API: #{ultimo_na_api} | Alvo: #{limite_real}")
            
            if ultimo_no_arquivo >= limite_real:
                print(f"✅ {loteria} já está atualizada até o limite.")
                continue

            novos = []
            for i in range(ultimo_no_arquivo + 1, limite_real + 1):
                print(f"  -> Buscando #{i} de #{limite_real}", end="\r")
                try:
                    res = self.session.get(f"{self.base_url}{loteria}/{i}", timeout=15, verify=False)
                    if res.status_code == 200:
                        novos.append(self.processar_concurso(res.json(), loteria))
                    time.sleep(0.1)
                except: continue

            if novos:
                novos.sort(key=lambda x: int(x['concurso']), reverse=True)
                historico[loteria] = novos + historico[loteria]
                print(f"✅ {loteria}: +{len(novos)} concursos adicionados.")

        with open(self.arquivo_historico, "w", encoding="utf-8") as f:
            json.dump(historico, f, indent=4, ensure_ascii=False)
        print("\n✨ Atualização concluída.")

if __name__ == "__main__":
    AtualizadorHistorico().atualizar()