import json
import os
from datetime import datetime

class ProcessadorEstatisticas:
    def __init__(self):
        self.arquivo_historico = "historico_total.json"
        self.arquivo_estatisticas = "estatisticas_lot.json"

    def processar(self):
        if not os.path.exists(self.arquivo_historico):
            print("❌ Erro: Arquivo historico_total.json não encontrado!")
            return

        with open(self.arquivo_historico, "r", encoding="utf-8") as f:
            historico = json.load(f)

        estatisticas_final = {
            "metadados": {
                "ultima_atualizacao": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "total_loterias": len(historico)
            },
            "loterias": {}
        }

        for loteria, concursos in historico.items():
            if not concursos: continue

            # O primeiro da lista é o mais recente (devido ao sort que fizemos no coletor)
            ultimo_concurso_geral = int(concursos[0]['concurso'])
            
            # Dicionários para contar dezenas e campos especiais
            stats_dezenas = {}
            stats_especiais = {}

            for conc in concursos:
                num_conc = int(conc['concurso'])
                
                # Processa Dezenas Normais
                for d in conc['dezenas']:
                    if d not in stats_dezenas:
                        stats_dezenas[d] = {"repeticoes": 0, "ultimo_concurso": 0}
                    
                    stats_dezenas[d]["repeticoes"] += 1
                    if num_conc > stats_dezenas[d]["ultimo_concurso"]:
                        stats_dezenas[d]["ultimo_concurso"] = num_conc

                # Processa Campos Especiais (Trevos, Time, Mês)
                for esp in conc.get('especial', []):
                    if not esp: continue
                    if esp not in stats_especiais:
                        stats_especiais[esp] = {"repeticoes": 0, "ultimo_concurso": 0}
                    
                    stats_especiais[esp]["repeticoes"] += 1
                    if num_conc > stats_especiais[esp]["ultimo_concurso"]:
                        stats_especiais[esp]["ultimo_concurso"] = num_conc

            # Formata o resultado final para esta loteria
            estatisticas_final["loterias"][loteria] = {
                "ultimo_concurso_processado": ultimo_concurso_geral,
                "dezenas": self._formatar_lista(stats_dezenas, ultimo_concurso_geral),
                "especiais": self._formatar_lista(stats_especiais, ultimo_concurso_geral)
            }

        with open(self.arquivo_estatisticas, "w", encoding="utf-8") as f:
            json.dump(estatisticas_final, f, indent=4, ensure_ascii=False)
        
        print(f"✅ Estatísticas geradas com sucesso: {self.arquivo_estatisticas}")

    def _formatar_lista(self, dicionario_stats, ultimo_geral):
        lista = []
        for valor, dados in dicionario_stats.items():
            atraso = ultimo_geral - dados["ultimo_concurso"]
            lista.append({
                "valor": valor,
                "repeticoes": dados["repeticoes"],
                "atraso": atraso,
                "ultimo_concurso": dados["ultimo_concurso"]
            })
        # Ordena por número/valor para facilitar a exibição
        try:
            lista.sort(key=lambda x: int(x['valor']))
        except:
            lista.sort(key=lambda x: x['valor'])
        return lista

if __name__ == "__main__":
    processador = ProcessadorEstatisticas()
    processador.processar()