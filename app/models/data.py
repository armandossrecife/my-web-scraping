from dataclasses import dataclass

# =============================================================================
# MODELOS DE DADOS
# =============================================================================

@dataclass
class PageData:
    """Representa os dados extraídos de uma página."""
    url: str
    title: str
    depth: int
    markdown_file: str
    discovered_links: list[str]
