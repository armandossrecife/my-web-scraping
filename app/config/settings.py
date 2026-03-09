from dataclasses import dataclass
from pathlib import Path

# =============================================================================
# CONFIGURAÇÃO CENTRALIZADA
# =============================================================================

@dataclass(frozen=True)
class CrawlerConfig:
    """Configurações imutáveis do crawler."""
    base_domain: str = "engsoftmoderna.info"
    base_url: str = "https://engsoftmoderna.info/"
    output_dir: Path = Path("output")
    request_timeout: int = 20
    request_delay: float = 0.5
    max_depth: int = 2
    user_agent: str = (
        "Mozilla/5.0 (compatible; EngSoftModernaCrawler/1.0; "
        "+https://engsoftmoderna.info)"
    )
    
    @property
    def seed_urls(self) -> list[str]:
        """Retorna a lista de URLs iniciais para o crawling."""
        chapters = [f"https://engsoftmoderna.info/cap{i}.html" for i in range(1, 11)]
        return [self.base_url] + chapters
    
    @property
    def headers(self) -> dict[str, str]:
        """Retorna os headers HTTP para as requisições."""
        return {"User-Agent": self.user_agent}
