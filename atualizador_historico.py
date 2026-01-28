import requests
import json
import os
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class AtualizadorHistorico:
    def __init__(self):
        # Mantendo sua lógica original de localização de arquivos
        caminho_base = os.path.dirname(os.path.abspath(__file__))
        self.arquivo_historico = os.path.join(caminho_base, "historico_total.json")
        
        # Mantendo sua URL original com /api/
        self.base_url = "https://loteriascaixa-api.herokuapp.com/api/"
        self.session = requests.Session()
        
        # CORREÇÃO 1: Limite realista para evitar loops infinitos
        self.ALVO_CONCURSO = 50000

    def ajustar_super_sete(self, dezenas):
        return [f"{i+1}{valor}" for i, valor in enumerate(dezenas)]

    # CORREÇÃO 2: Adicionado 'ultimo_no_arquivo' aqui para a função saber o valor
    def obter_ultimo_real(self, loteria, ultimo_no_arquivo):
        """Pergunta à API qual o concurso mais recente. Se falhar, retorna o que já temos."""
        try:
            res = self.session.get(f"{self.base_url}{loteria}/latest", timeout=10, verify=False)
            if res.status_code == 200:
                return int(res.json()['concurso'])
        except:
            # Se a API falhar ou cair, o código não tenta buscar nada novo
            return ultimo_no_arquivo 
        return ultimo_no_arquivo

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
            print(f"❌ Arquivo não encontrado em: {self.arquivo_historico}")
            return

        with open(self.arquivo_historico, "r", encoding="utf-8") as f:
            historico = json.load(f)

        for loteria in historico.keys():
            # Acessa o concurso do primeiro item da lista da loteria
            ultimo_no_arquivo = int(historico[loteria][0]['concurso'])
            
            # CORREÇÃO 3: Enviando o valor atual para a checagem
            ultimo_na_api = self.obter_ultimo_real(loteria, ultimo_no_arquivo)
            
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
