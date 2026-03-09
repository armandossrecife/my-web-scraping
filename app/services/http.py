from app.config.settings import CrawlerConfig
from typing import Optional
import requests

# =============================================================================
# SERVIÇO DE HTTP
# =============================================================================

class HttpService:
    """Responsável por requisições HTTP com tratamento de erros."""
    
    def __init__(self, config: CrawlerConfig):
        self.session = requests.Session()
        self.config = config
    
    def fetch_html(self, url: str) -> Optional[str]:
        """
        Baixa o HTML de uma URL.
        
        Returns:
            Conteúdo HTML como string, ou None em caso de erro.
        """
        try:
            response = self.session.get(
                url, 
                headers=self.config.headers, 
                timeout=self.config.request_timeout
            )
            response.raise_for_status()
            
            if "text/html" not in response.headers.get("Content-Type", ""):
                return None
                
            return response.text
            
        except requests.RequestException as e:
            print(f"[ERRO] Falha ao baixar {url}: {e}")
            return None