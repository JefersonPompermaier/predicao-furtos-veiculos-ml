import os
import time
import logging
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_DIR = os.path.join(BASE_DIR, 'data', 'SP', 'raw')
os.makedirs(RAW_DATA_DIR, exist_ok=True)

URL = "http://www.ssp.sp.gov.br/transparenciassp/Consulta.aspx"

# User-Agent to mimic a browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Origin': 'http://www.ssp.sp.gov.br',
    'Referer': 'http://www.ssp.sp.gov.br/transparenciassp/Consulta.aspx'
}

def get_aspnet_states(soup):
    """Extrai os tokens escondidos do ASP.NET necessários para o POST."""
    viewstate = soup.find('input', {'id': '__VIEWSTATE'})['value'] if soup.find('input', {'id': '__VIEWSTATE'}) else ''
    viewstategenerator = soup.find('input', {'id': '__VIEWSTATEGENERATOR'})['value'] if soup.find('input', {'id': '__VIEWSTATEGENERATOR'}) else ''
    eventvalidation = soup.find('input', {'id': '__EVENTVALIDATION'})['value'] if soup.find('input', {'id': '__EVENTVALIDATION'}) else ''
    return viewstate, viewstategenerator, eventvalidation

def run_scraper():
    session = requests.Session()
    
    # 1. Carrega a página inicial
    logger.info("Acessando página inicial...")
    resp = session.get(URL, headers=HEADERS, timeout=60)
    soup = BeautifulSoup(resp.content, 'html.parser')
    
    crimes = {
        'FURTO_VEICULO': 'ctl00$cphBody$btnFurtoVeiculo',
        'ROUBO_VEICULO': 'ctl00$cphBody$btnRouboVeiculo'
    }
    
    # ctl00$cphBody$lkAno19 até ctl00$cphBody$lkAno23
    anos = {
        '2023': 'ctl00$cphBody$lkAno23',
        '2022': 'ctl00$cphBody$lkAno22',
        '2021': 'ctl00$cphBody$lkAno21',
        '2020': 'ctl00$cphBody$lkAno20',
        '2019': 'ctl00$cphBody$lkAno19'
    }
    
    meses = {
        '01': 'ctl00$cphBody$lkMes1', '02': 'ctl00$cphBody$lkMes2', '03': 'ctl00$cphBody$lkMes3',
        '04': 'ctl00$cphBody$lkMes4', '05': 'ctl00$cphBody$lkMes5', '06': 'ctl00$cphBody$lkMes6',
        '07': 'ctl00$cphBody$lkMes7', '08': 'ctl00$cphBody$lkMes8', '09': 'ctl00$cphBody$lkMes9',
        '10': 'ctl00$cphBody$lkMes10', '11': 'ctl00$cphBody$lkMes11', '12': 'ctl00$cphBody$lkMes12'
    }
    
    for crime_nome, crime_btn in crimes.items():
        logger.info(f"Selecionando crime: {crime_nome}")
        vs, vsg, ev = get_aspnet_states(soup)
        
        payload_crime = {
            '__EVENTTARGET': crime_btn,
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': vs,
            '__VIEWSTATEGENERATOR': vsg,
            '__EVENTVALIDATION': ev,
        }
        
        resp_crime = session.post(URL, headers=HEADERS, data=payload_crime, timeout=120)
        soup_crime = BeautifulSoup(resp_crime.content, 'html.parser')
        
        for ano, ano_btn in anos.items():
            logger.info(f"Selecionando ano: {ano}")
            vs, vsg, ev = get_aspnet_states(soup_crime)
            
            payload_ano = {
                '__EVENTTARGET': ano_btn,
                '__EVENTARGUMENT': '',
                '__VIEWSTATE': vs,
                '__VIEWSTATEGENERATOR': vsg,
                '__EVENTVALIDATION': ev,
            }
            
            try:
                resp_ano = session.post(URL, headers=HEADERS, data=payload_ano, timeout=120)
                soup_ano = BeautifulSoup(resp_ano.content, 'html.parser')
            except Exception as e:
                logger.error(f"Erro ao selecionar ano {ano}: {e}")
                continue
            
            for mes, mes_btn in meses.items():
                logger.info(f"Processando {crime_nome} - {ano}-{mes}...")
                
                # Check if already downloaded
                file_xls = os.path.join(RAW_DATA_DIR, f"{crime_nome}_{ano}_{mes}.xls")
                file_csv = os.path.join(RAW_DATA_DIR, f"{crime_nome}_{ano}_{mes}.csv")
                
                if os.path.exists(file_xls) or os.path.exists(file_csv):
                    logger.info(f"Arquivo já existe, pulando.")
                    continue
                
                # Clica no mes
                vs, vsg, ev = get_aspnet_states(soup_ano)
                payload_mes = {
                    '__EVENTTARGET': mes_btn,
                    '__EVENTARGUMENT': '',
                    '__VIEWSTATE': vs,
                    '__VIEWSTATEGENERATOR': vsg,
                    '__EVENTVALIDATION': ev,
                }
                
                try:
                    resp_mes = session.post(URL, headers=HEADERS, data=payload_mes, timeout=120)
                    soup_mes = BeautifulSoup(resp_mes.content, 'html.parser')
                    
                    # Clica em exportar
                    logger.info("Enviando comando de exportacao...")
                    vs, vsg, ev = get_aspnet_states(soup_mes)
                    payload_export = {
                        '__EVENTTARGET': 'ctl00$cphBody$ExportarBOLink',
                        '__EVENTARGUMENT': '',
                        '__VIEWSTATE': vs,
                        '__VIEWSTATEGENERATOR': vsg,
                        '__EVENTVALIDATION': ev,
                    }
                    
                    resp_export = session.post(URL, headers=HEADERS, data=payload_export, timeout=600) # Até 10 min
                    
                    # Salva arquivo
                    content_disp = resp_export.headers.get('Content-Disposition', '')
                    if 'attachment' in content_disp or resp_export.status_code == 200:
                        # Assumimos que o que voltou e' um excel/csv
                        with open(file_xls, 'wb') as f:
                            f.write(resp_export.content)
                        logger.info(f"Sucesso: {file_xls} salvo com {len(resp_export.content)} bytes.")
                    else:
                        logger.error(f"Resposta inesperada ao exportar {ano}-{mes}. Status: {resp_export.status_code}")
                        
                except Exception as e:
                    logger.error(f"Erro fatal ao baixar {ano}-{mes}: {e}")

if __name__ == '__main__':
    run_scraper()
