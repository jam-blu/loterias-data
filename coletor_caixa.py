import requests
import json
import os
import time
from datetime import datetime, timedelta
import urllib3

# Alterado em 06-05-2026 para eliminar caracteres nulos do arquivo gerado.

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ColetorEvoluido:
    def __init__(self):
        self.diretorio = os.path.dirname(os.path.abspath(__file__))
        self.arquivo_final = os.path.join(self.diretorio, "numeros_lot.json")
        self.base_url = "https://loteriascaixa-api.herokuapp.com/api/"
        # AJUSTE: Mudamos para 92 dias para garantir a margem de segurança jurídica
        self.data_corte = datetime.now() - timedelta(days=92)

    def ajustar_super_sete(self, dezenas):
        return [f"{i+1}{valor}" for i, valor in enumerate(dezenas)]

    def formatar_valor(self, dado_premio):
        chaves_possiveis = ['valor_total', 'valorIndividual', 'valor', 'rateio', 'valorPremio']
        valor_bruto = 0
        for chave in chaves_possiveis:
            if chave in dado_premio and dado_premio[chave] is not None:
                valor_bruto = dado_premio[chave]
                break
        
        if isinstance(valor_bruto, str):
            try:
                return float(valor_bruto.replace('R$', '').replace('.', '').replace(',', '.').strip())
            except: return 0.0
        return float(valor_bruto or 0.0)

    def processar_concurso(self, dados, loteria_id):
        premios = []
        for p in dados.get('premiacoes', []):
            premios.append({
                "faixa_nome": p.get('descricao', 'Outros'),
                "ganhadores": p.get('ganhadores', 0),
                "valor_individual": self.formatar_valor(p)
            })

        dezenas = dados.get('dezenas', [])
        if loteria_id == "supersete":
            dezenas = self.ajustar_super_sete(dezenas)

        """
        especial = []
        if loteria_id == "maismilionaria": especial = dados.get('trevos', [])
        elif loteria_id == "timemania": especial = [dados.get('timeCoracao', "")]
        elif loteria_id == "diadesorte": especial = [dados.get('mesSorte', "")]
        """

        especial = []
        if loteria_id == "maismilionaria":
            especial = dados.get('trevos', [])
        elif loteria_id == "timemania":
            time_bruto = dados.get('timeCoracao', "").replace('\x00', '').strip()
            if "/" in time_bruto:
                p = time_bruto.split("/")
                time_limpo = f"{p[0].strip()} /{p[1].strip()}"
            else:
                time_limpo = time_bruto
            especial = [time_limpo]
        elif loteria_id == "diadesorte":
            especial = [dados.get('mesSorte', "").replace('\x00', '').strip()]

        return {
            "identificacao": {
                "concurso": dados.get('concurso'),
                "data": dados.get('data'),
                "local": dados.get('local', "Espaço da Sorte")
            },
            "resultados": {
                "dezenas": dezenas,
                "campos_especiais": especial
            },
            "financeiro": premios
        }

    def limpar_dados_antigos(self, lista_concursos):
        """Remove concursos com data anterior ao prazo de segurança."""
        nova_lista = []
        for c in lista_concursos:
            try:
                data_c = datetime.strptime(c['identificacao']['data'], "%d/%m/%Y")
                if data_c >= self.data_corte:
                    nova_lista.append(c)
            except: continue
        return nova_lista

    def carregar_arquivo_atual(self):
        if os.path.exists(self.arquivo_final):
            with open(self.arquivo_final, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def atualizar_loteria(self, loteria_id, dados_atuais):
        print(f"📡 Analisando {loteria_id}...")
        
        historico = dados_atuais.get(loteria_id, [])
        
        ultimo_concurso = 0
        if historico:
            ultimo_concurso = historico[0]['identificacao']['concurso']
        
        concursos_novos = []
        proximo = ultimo_concurso + 1
        tentativas_vazias = 0

        while tentativas_vazias < 2:
            print(f"  -> Verificando #{proximo}...", end="\r")
            try:
                res = requests.get(f"{self.base_url}{loteria_id}/{proximo}", timeout=15)
                if res.status_code == 200:
                    dados = res.json()
                    concursos_novos.insert(0, self.processar_concurso(dados, loteria_id))
                    proximo += 1
                    tentativas_vazias = 0
                    time.sleep(0.5)
                else:
                    tentativas_vazias += 1
                    proximo += 1
            except:
                break
        
        resultado_final = concursos_novos + historico
        resultado_final = self.limpar_dados_antigos(resultado_final)
        
        print(f"  -> Finalizado. {len(concursos_novos)} novos adicionados.")
        return resultado_final

if __name__ == "__main__":
    coletor = ColetorEvoluido()
    loterias = ["megasena", "maismilionaria", "timemania", "diadesorte", "supersete", "quina", "lotofacil", "lotomania", "duplasena"]
    
    dados_arquivo = coletor.carregar_arquivo_atual()
    base_final = {}

    for l in loterias:
        base_final[l] = coletor.atualizar_loteria(l, dados_arquivo)

    novo_json = json.dumps(base_final, indent=4, ensure_ascii=False)
    
    try:
        with open(coletor.arquivo_final, "r", encoding="utf-8") as f:
            antigo_json = f.read()
    except: antigo_json = ""

    if novo_json != antigo_json:
        with open(coletor.arquivo_final, "w", encoding="utf-8") as f:
            f.write(novo_json)
        print("\n🚀 ARQUIVO ATUALIZADO COM SUCESSO!")
    else:
        print("\nℹ️ Nenhuma mudança necessária.")
