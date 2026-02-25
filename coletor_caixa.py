import requests
import json
import os
import time
from datetime import datetime, timedelta
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ColetorFinal:
    def __init__(self):
        self.diretorio = os.path.dirname(os.path.abspath(__file__))
        self.arquivo_final = os.path.join(self.diretorio, "numeros_lot.json")
        self.base_url = "https://loteriascaixa-api.herokuapp.com/api/"

    def ajustar_super_sete(self, dezenas):
        return [f"{i+1}{valor}" for i, valor in enumerate(dezenas)]

    def formatar_valor(self, dado_premio):
        """
        Tenta extrair o valor individual testando todas as chaves possíveis 
        da API oficial e das APIs espelho.
        """
        # Lista de chaves possíveis para o valor individual (rateio)
        chaves_possiveis = ['valor_total', 'valorIndividual', 'valor', 'rateio', 'valorPremio']
        
        valor_bruto = 0
        for chave in chaves_possiveis:
            if chave in dado_premio and dado_premio[chave] is not None:
                valor_bruto = dado_premio[chave]
                break
        
        if isinstance(valor_bruto, str):
            try:
                return float(valor_bruto.replace('R$', '').replace('.', '').replace(',', '.').strip())
            except:
                return 0.0
        return float(valor_bruto)

    def processar_concurso(self, dados, loteria_id):
        premios = []
        for p in dados.get('premiacoes', []):
            # --- DEBUG: Se ainda der 0.0, descomente a linha abaixo para ver as chaves no terminal ---
            # print(f"DEBUG {loteria_id}: {p.keys()}") 
            
            premios.append({
                "faixa_nome": p.get('descricao', 'Outros'),
                "ganhadores": p.get('ganhadores', 0),
                "valor_individual": self.formatar_valor(p)
            })

        dezenas = dados.get('dezenas', [])
        if loteria_id == "supersete":
            dezenas = self.ajustar_super_sete(dezenas)

        especial = []
        if loteria_id == "maismilionaria": especial = dados.get('trevos', [])
        elif loteria_id == "timemania": especial = [dados.get('timeCoracao', "")]
        elif loteria_id == "diadesorte": especial = [dados.get('mesSorte', "")]

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

    def coletar_loteria(self, loteria_id, dias=91):
        print(f"📡 Acessando {loteria_id}...")
        resultados = []
        data_limite = datetime.now() - timedelta(days=dias)

        try:
            res = requests.get(f"{self.base_url}{loteria_id}/latest", timeout=20)
            if res.status_code != 200: return []
            
            dados = res.json()
            resultados.append(self.processar_concurso(dados, loteria_id))
            
            num = dados['concurso'] - 1
            
            # Aumentamos de 20 para 60 para garantir que chegue aos 100 dias
            # (Loterias diárias como a Quina precisam de mais iterações)
            for _ in range(110): 
                print(f"  -> {loteria_id} #{num}", end="\r")
                res = requests.get(f"{self.base_url}{loteria_id}/{num}", timeout=20)
                
                # Se o concurso não existir ou a API falhar, interrompe este loop
                if res.status_code != 200: 
                    break
                
                con_dados = res.json()
                try:
                    # Tenta converter a data para verificar o limite
                    data_con = datetime.strptime(con_dados['data'], "%d/%m/%Y")
                    if data_con < data_limite: 
                        break # Se chegou na data desejada, para a busca
                except: 
                    break
                
                resultados.append(self.processar_concurso(con_dados, loteria_id))
                num -= 1
                time.sleep(0.3) # Delay para evitar bloqueio por excesso de chamadas
            
            return resultados
        except Exception as e:
            print(f"Erro ao coletar {loteria_id}: {e}")
            return []

if __name__ == "__main__":
    coletor = ColetorFinal()
    loterias = ["megasena", "maismilionaria", "timemania", "diadesorte", "supersete", "quina", "lotofacil", "lotomania", "duplasena"]
    
    base_final = {}
    for l in loterias:
        dados_loteria = coletor.coletar_loteria(l, dias=91)
        if dados_loteria:
            base_final[l] = dados_loteria

    if base_final:
        # Prepara os dados novos para comparar
        novo_conteudo = json.dumps(base_final, indent=4, ensure_ascii=False)
        
        # Tenta ler o que já existe no arquivo atual
        conteudo_atual = ""
        if os.path.exists(coletor.arquivo_final):
            with open(coletor.arquivo_final, "r", encoding="utf-8") as f:
                conteudo_atual = f.read()
        
        # SÓ SALVA SE FOR DIFERENTE. Se for igual, o arquivo nem é tocado.
        if novo_conteudo != conteudo_atual:
            with open(coletor.arquivo_final, "w", encoding="utf-8") as f:
                f.write(novo_conteudo)
            print(f"\n🚀 DADOS NOVOS ENCONTRADOS! Arquivo atualizado.")
        else:
            print("\nℹ️ Tudo igual. Nenhum sorteio novo publicado ainda.")
    else:
        print("\n❌ ERRO CRÍTICO: Nenhum dado foi coletado.")
