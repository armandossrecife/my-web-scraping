from pathlib import Path
from app.models.data import PageData
import json
from dataclasses import asdict

# =============================================================================
# PERSISTÊNCIA
# =============================================================================

class PersistenceService:
    """Gerencia salvamento de arquivos e geração de índices."""
    
    @staticmethod
    def save_markdown(output_dir: Path, filename: str, content: str) -> Path:
        """Salva conteúdo Markdown em arquivo."""
        output_dir.mkdir(parents=True, exist_ok=True)
        filepath = output_dir / filename
        filepath.write_text(content, encoding="utf-8")
        return filepath
    
    @staticmethod
    def write_index(output_dir: Path, pages: list[PageData]) -> None:
        """Gera arquivo index.md com lista de páginas processadas."""
        lines = [
            "# Índice do conteúdo extraído",
            "",
            f"Total de páginas coletadas: **{len(pages)}**",
            ""
        ]
        
        for page in sorted(pages, key=lambda p: (p.depth, p.title.lower())):
            lines.append(f"- [{page.title}]({page.markdown_file})")
            lines.append(f"  - URL: `{page.url}`")
            lines.append(f"  - Profundidade: `{page.depth}`")
        
        (output_dir / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    
    @staticmethod
    def write_manifest(output_dir: Path, pages: list[PageData]) -> None:
        """Gera manifest.json com metadados das páginas."""
        data = [asdict(page) for page in pages]
        (output_dir / "manifest.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
