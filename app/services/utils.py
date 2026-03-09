from urllib.parse import urlparse, urldefrag
import re

# =============================================================================
# UTILITÁRIOS DE URL
# =============================================================================

class UrlUtils:
    """Funções utilitárias para manipulação e validação de URLs."""
    
    BLOCKED_EXTENSIONS = (
        ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp",
        ".pdf", ".zip", ".rar", ".7z", ".mp4", ".mp3", ".avi", ".mov",
        ".css", ".js", ".json", ".xml", ".ico", ".woff", ".woff2", ".ttf", ".eot"
    )
    
    @staticmethod
    def normalize(url: str) -> str:
        """
        Normaliza uma URL: remove fragmentos, padroniza esquema/host,
        e remove slash final redundante.
        """
        clean, _ = urldefrag(url.strip())
        parsed = urlparse(clean)
        
        scheme = parsed.scheme or "https"
        netloc = parsed.netloc.lower()
        path = parsed.path or "/"
        
        # Remove slash final, exceto na raiz
        if path != "/" and path.endswith("/"):
            path = path[:-1]
        
        normalized = f"{scheme}://{netloc}{path}"
        if parsed.query:
            normalized += f"?{parsed.query}"
            
        return normalized
    
    @staticmethod
    def is_internal(url: str, domain: str) -> bool:
        """Verifica se a URL pertence ao domínio alvo."""
        return urlparse(url).netloc.lower() == domain
    
    @staticmethod
    def should_visit(url: str, domain: str) -> bool:
        """
        Decide se uma URL deve ser visitada:
        - Deve ser do domínio alvo
        - Não deve ser arquivo estático bloqueado
        """
        if not UrlUtils.is_internal(url, domain):
            return False
        
        lowered = url.lower()
        return not lowered.endswith(UrlUtils.BLOCKED_EXTENSIONS)


# =============================================================================
# UTILITÁRIOS DE TEXTO E ARQUIVOS
# =============================================================================

class TextUtils:
    """Funções para processamento de texto e geração de nomes de arquivo."""
    
    @staticmethod
    def slugify(text: str, max_length: int = 120) -> str:
        """Converte texto para slug URL-safe."""
        text = text.lower().strip()
        text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
        text = re.sub(r"[-\s]+", "-", text, flags=re.UNICODE)
        return text[:max_length].strip("-") or "pagina"
    
    @staticmethod
    def make_filename(url: str, title: str) -> str:
        """Gera nome de arquivo seguro a partir da URL e título."""
        parsed = urlparse(url)
        path_part = parsed.path.strip("/").replace("/", "-") or "home"
        title_part = TextUtils.slugify(title)
        filename = f"{path_part}__{title_part}.md"
        return re.sub(r"[^\w\-.]", "_", filename, flags=re.UNICODE)
    
    @staticmethod
    def collapse_blank_lines(text: str) -> str:
        """Remove linhas em branco excessivas."""
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip() + "\n"
    
    @staticmethod
    def clean(text: str) -> str:
        """Limpa espaços em branco e caracteres especiais."""
        text = text.replace("\xa0", " ")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s+\n", "\n\n", text)
        return text.strip()
