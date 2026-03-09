from bs4 import BeautifulSoup, NavigableString, Tag
from app.services.utils import TextUtils

# =============================================================================
# EXTRATOR DE CONTEÚDO (HTML → Markdown)
# =============================================================================

class ContentExtractor:
    """Extrai conteúdo útil de HTML e converte para Markdown."""
    
    # Seletores para encontrar o container principal do conteúdo
    MAIN_CONTAINER_SELECTORS = [
        "main", "article", "[role='main']", ".content", ".main", 
        ".post", ".entry-content", ".container", "body"
    ]
    
    # Elementos a remover por não agregarem ao conteúdo principal
    NOISE_SELECTORS = [
        "script", "style", "noscript", "header", "footer", "nav", 
        "aside", "form", "button", "input", "iframe"
    ]
    
    @staticmethod
    def get_title(soup: BeautifulSoup) -> str:
        """Extrai o título da página (tag <title> ou primeiro <h1>)."""
        if soup.title and (title := soup.title.text.strip()):
            return title
        if (h1 := soup.find("h1")) and (text := h1.get_text(strip=True)):
            return text
        return "Sem título"
    
    @staticmethod
    def _remove_noise(container: Tag) -> None:
        """Remove elementos de ruído do container."""
        for selector in ContentExtractor.NOISE_SELECTORS:
            for tag in container.select(selector):
                tag.decompose()
    
    @staticmethod
    def _find_main_container(soup: BeautifulSoup) -> Tag:
        """Encontra o elemento que contém o conteúdo principal."""
        for selector in ContentExtractor.MAIN_CONTAINER_SELECTORS:
            if found := soup.select_one(selector):
                return found
        return soup
    
    @staticmethod
    def _convert_inline(tag: Tag) -> str:
        """Converte elementos inline para Markdown básico."""
        parts = []
        
        for child in tag.children:
            if isinstance(child, NavigableString):
                parts.append(str(child))
            elif isinstance(child, Tag):
                name = child.name.lower()
                text = TextUtils.clean(child.get_text(" ", strip=True))
                
                if name in {"strong", "b"}:
                    parts.append(f"**{text}**")
                elif name in {"em", "i"}:
                    parts.append(f"*{text}*")
                elif name == "code":
                    parts.append(f"`{text}`")
                elif name == "a" and (href := child.get("href", "").strip()):
                    link_text = text or href
                    parts.append(f"[{link_text}]({href})")
                elif name == "br":
                    parts.append("\n")
                else:
                    parts.append(text)
        
        result = "".join(parts)
        return TextUtils.clean(result)
    
    @staticmethod
    def _convert_list(tag: Tag, level: int = 0) -> str:
        """Converte listas <ul>/<ol> para sintaxe Markdown."""
        lines = []
        indent = "  " * level
        is_ordered = tag.name.lower() == "ol"
        
        for idx, li in enumerate(tag.find_all("li", recursive=False), 1):
            marker = f"{idx}." if is_ordered else "-"
            parts = []
            
            for child in li.children:
                if isinstance(child, NavigableString) and (txt := TextUtils.clean(str(child))):
                    parts.append(txt)
                elif isinstance(child, Tag):
                    if child.name in {"ul", "ol"}:
                        if nested := ContentExtractor._convert_list(child, level + 1):
                            parts.append("\n" + nested.rstrip())
                    elif txt := ContentExtractor._convert_inline(child):
                        parts.append(txt)
            
            if item := " ".join(p for p in parts if p.strip()):
                lines.append(f"{indent}{marker} {TextUtils.clean(item)}")
        
        return "\n".join(lines) + ("\n" if lines else "")
    
    @staticmethod
    def _convert_table(table: Tag) -> str:
        """Converte tabelas HTML para Markdown."""
        rows = []
        for tr in table.find_all("tr"):
            cells = [TextUtils.clean(c.get_text(" ", strip=True)) for c in tr.find_all(["th", "td"])]
            if any(cells):
                rows.append(cells)
        
        if not rows:
            return ""
        
        # Normaliza colunas
        max_cols = max(len(r) for r in rows)
        rows = [r + [""] * (max_cols - len(r)) for r in rows]
        
        header, sep, body = rows[0], ["---"] * max_cols, rows[1:]
        md_rows = [
            f"| {' | '.join(header)} |",
            f"| {' | '.join(sep)} |"
        ] + [f"| {' | '.join(row)} |" for row in body]
        
        return "\n".join(md_rows) + "\n"
    
    @staticmethod
    def _process_block(element: Tag, lines: list[str]) -> None:
        """Processa um elemento de bloco e adiciona ao output Markdown."""
        name = element.name.lower()
        
        if name.startswith("h") and name[1:].isdigit():
            level = int(name[1])
            if heading := TextUtils.clean(element.get_text(" ", strip=True)):
                lines.append(f"{'#' * level} {heading}")
                lines.append("")
                
        elif name == "p":
            if text := ContentExtractor._convert_inline(element):
                lines.append(text)
                lines.append("")
                
        elif name in {"ul", "ol"}:
            if md_list := ContentExtractor._convert_list(element).strip():
                lines.append(md_list)
                lines.append("")
                
        elif name == "blockquote":
            if quote := TextUtils.clean(element.get_text("\n", strip=True)):
                for qline in quote.splitlines():
                    lines.append(f"> {qline}")
                lines.append("")
                
        elif name == "pre":
            if code := element.get_text("\n", strip=False).rstrip():
                lines.extend(["```", code, "```", ""])
                
        elif name == "table":
            if md_table := ContentExtractor._convert_table(element).strip():
                lines.append(md_table)
                lines.append("")
    
    def extract(self, html: str, url: str) -> tuple[str, str]:
        """
        Extrai conteúdo de HTML e converte para Markdown.
        
        Returns:
            Tuple com (título, conteúdo_markdown)
        """
        soup = BeautifulSoup(html, "html.parser")
        title = self.get_title(soup)
        
        container = self._find_main_container(soup)
        self._remove_noise(container)
        
        lines = [f"# {title}", "", f"**Fonte:** {url}", ""]
        
        for element in container.find_all(recursive=False):
            if isinstance(element, Tag):
                self._process_block(element, lines)
        
        markdown = TextUtils.collapse_blank_lines("\n".join(lines))
        return title, markdown