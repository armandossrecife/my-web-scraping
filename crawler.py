"""
Web Crawler para engsoftmoderna.info

Extrai conteúdo de páginas HTML, converte para Markdown e salva localmente.

Funcionalidades:
- Crawling limitado ao domínio engsoftmoderna.info
- Seeds: home + capítulos 1..10
- Profundidade máxima: 2 níveis
- Extração de conteúdo útil e conversão para Markdown
- Geração de index.md e manifest.json

Uso:
    python crawler.py

Dependências:
    pip install requests beautifulsoup4
"""

from __future__ import annotations

import time
from collections import deque
from typing import Iterable
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from app.config.settings import CrawlerConfig
from app.models.data import PageData
from app.services.utils import UrlUtils
from app.services.http import HttpService
from app.services.utils import TextUtils
from app.services.extractor import ContentExtractor
from app.services.persist import PersistenceService

# =============================================================================
# CRAWLER PRINCIPAL
# =============================================================================

class WebCrawler:
    """Orquestra o processo de crawling, extração e salvamento."""
    
    def __init__(self, config: CrawlerConfig):
        self.config = config
        self.http = HttpService(config)
        self.extractor = ContentExtractor()
    
    def _extract_links(self, html: str, current_url: str) -> list[str]:
        """Extrai links válidos de uma página HTML."""
        soup = BeautifulSoup(html, "html.parser")
        links = []
        
        for a in soup.find_all("a", href=True):
            if href := a.get("href", "").strip():
                abs_url = UrlUtils.normalize(urljoin(current_url, href))
                if UrlUtils.should_visit(abs_url, self.config.base_domain):
                    links.append(abs_url)
        
        # Remove duplicatas mantendo ordem
        seen = set()
        unique = []
        for link in links:
            if link not in seen:
                seen.add(link)
                unique.append(link)
        return unique
    
    def crawl(self, seed_urls: Iterable[str]) -> list[PageData]:
        """
        Executa o crawling a partir das seeds.
        
        Returns:
            Lista de PageData com informações das páginas processadas.
        """
        queue = deque()
        visited: set[str] = set()
        pages: list[PageData] = []
        
        # Inicializa fila com seeds válidas
        for url in seed_urls:
            normalized = UrlUtils.normalize(url)
            if UrlUtils.should_visit(normalized, self.config.base_domain):
                if normalized not in visited:
                    queue.append((normalized, 0))
                    visited.add(normalized)
        
        while queue:
            url, depth = queue.popleft()
            
            if depth > self.config.max_depth:
                continue
            
            print(f"[INFO] Visitando (nível {depth}): {url}")
            
            if not (html := self.http.fetch_html(url)):
                continue
            
            # Extrai e processa conteúdo
            title, markdown = self.extractor.extract(html, url)
            links = self._extract_links(html, url)
            filename = TextUtils.make_filename(url, title)
            
            PersistenceService.save_markdown(self.config.output_dir, filename, markdown)
            
            pages.append(PageData(
                url=url,
                title=title,
                depth=depth,
                markdown_file=filename,
                discovered_links=links
            ))
            
            # Agenda links para crawling (respeitando profundidade)
            if depth < self.config.max_depth:
                for link in links:
                    if link not in visited:
                        visited.add(link)
                        queue.append((link, depth + 1))
            
            time.sleep(self.config.request_delay)
        
        # Gera arquivos de índice
        PersistenceService.write_index(self.config.output_dir, pages)
        PersistenceService.write_manifest(self.config.output_dir, pages)
        
        return pages


# =============================================================================
# ENTRY POINT
# =============================================================================

def main() -> None:
    """Ponto de entrada da aplicação."""
    config = CrawlerConfig()
    crawler = WebCrawler(config)
    
    print("[INFO] Iniciando crawler...")
    pages = crawler.crawl(config.seed_urls)
    
    print(f"[INFO] Concluído. Total de páginas salvas: {len(pages)}")
    print(f"[INFO] Saída em: {config.output_dir.resolve()}")


if __name__ == "__main__":
    main()