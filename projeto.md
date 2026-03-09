# 📚 Explicação Passo a Passo do Código Refatorado

Vou explicar o código refatorado em camadas, do geral para o específico, mostrando **o que cada parte faz** e **por que foi organizada assim**.


## 🗂️ 1. Estrutura Geral do Projeto

```
app
├── __init__.py
├── config
│   ├── __init__.py
│   └── settings.py
├── models
│   ├── __init__.py
│   └── data.py
└── services
    ├── __init__.py
    ├── extractor.py
    ├── http.py
    ├── persist.py
    └── utils.py
crawler.py
projeto.md
pyproject.toml
README.md
uv.lock
```

Dependências do script principal (crawler)

```
crawler.py
├── Configuração (CrawlerConfig)                        # app.config.setting.py
├── Modelos de Dados (PageData)                         # app.models.data.py
├── Serviços Especializados
│   ├── HttpService        → Requisições HTTP           # app.services.http.py
│   ├── UrlUtils           → Manipulação de URLs        # app.services.utils.py
│   ├── TextUtils          → Processamento de texto     # app.services.utils.py
│   ├── ContentExtractor   → HTML → Markdown            # app.services.extractor.py
│   └── PersistenceService → Salvamento de arquivos     # app.services.persist.py
├── Orquestrador (WebCrawler)
└── Entry Point (main)
```

> ✅ **Por que essa estrutura?**  
> Cada classe tem uma única responsabilidade (princípio SRP). Isso facilita testes, manutenção e entendimento.


## ⚙️ 2. Configuração Centralizada (`CrawlerConfig`)

```python
@dataclass(frozen=True)
class CrawlerConfig:
    base_domain: str = "engsoftmoderna.info"
    base_url: str = "https://engsoftmoderna.info/"
    output_dir: Path = Path("output")
    request_timeout: int = 20
    request_delay: float = 0.5
    max_depth: int = 2
    user_agent: str = "Mozilla/5.0 (...)"
    
    @property
    def seed_urls(self) -> list[str]:
        chapters = [f"https://engsoftmoderna.info/cap{i}.html" for i in range(1, 11)]
        return [self.base_url] + chapters
```

### 🔍 O que faz:
- Agrupa **todas as configurações** em um único lugar
- `@dataclass(frozen=True)` → torna a configuração imutável (segurança)
- `seed_urls` e `headers` são **properties calculadas**, evitando repetição

### 💡 Vantagem:
Se precisar mudar o domínio ou profundidade, altera em **um lugar só**.


## 📦 3. Modelo de Dados (`PageData`)

```python
@dataclass
class PageData:
    url: str
    title: str
    depth: int
    markdown_file: str
    discovered_links: list[str]
```

### 🔍 O que faz:
- Representa os metadados de uma página processada
- Usado para gerar `index.md` e `manifest.json`

> ✅ `@dataclass` gera automaticamente `__init__`, `__repr__`, etc.


## 🌐 4. Serviço HTTP (`HttpService`)

```python
class HttpService:
    def __init__(self, config: CrawlerConfig):
        self.session = requests.Session()  # Reutiliza conexão
        self.config = config
    
    def fetch_html(self, url: str) -> Optional[str]:
        try:
            response = self.session.get(url, headers=self.config.headers, timeout=...)
            response.raise_for_status()
            
            if "text/html" not in response.headers.get("Content-Type", ""):
                return None  # Ignora PDFs, imagens, etc.
            return response.text
        except requests.RequestException as e:
            print(f"[ERRO] Falha ao baixar {url}: {e}")
            return None
```

### 🔍 O que faz:
- Centraliza lógica de requisição HTTP
- Reutiliza conexão com `Session()` (mais eficiente)
- Filtra apenas conteúdo HTML
- Trata erros de rede de forma graciosa

### 💡 Por que uma classe?
Permite **mockar** em testes e trocar a implementação futuramente (ex: usar `httpx`).


## 🔗 5. Utilitários de URL (`UrlUtils`)

```python
class UrlUtils:
    BLOCKED_EXTENSIONS = (".jpg", ".pdf", ".css", ...)  # Arquivos ignorados
    
    @staticmethod
    def normalize(url: str) -> str:
        # Remove fragmentos (#), padroniza https, remove slash final
        ...
    
    @staticmethod
    def is_internal(url: str, domain: str) -> bool:
        # Verifica se URL é do domínio alvo
        ...
    
    @staticmethod
    def should_visit(url: str, domain: str) -> bool:
        # Combina as duas validações acima
        ...
```

### 🔍 O que faz:
- `normalize`: Garante que URLs equivalentes sejam tratadas como iguais
  - `https://engsoftmoderna.info/` ≡ `https://engsoftmoderna.info`
- `should_visit`: Decide se uma URL deve ser crawling (filtra estáticos e domínios externos)

### 💡 Exemplo prático:
```python
UrlUtils.normalize("https://engsoftmoderna.info/cap1.html#top")
# Retorna: "https://engsoftmoderna.info/cap1.html"

UrlUtils.should_visit("https://engsoftmoderna.info/img/logo.png", "engsoftmoderna.info")
# Retorna: False (extensão .png está bloqueada)
```


## ✍️ 6. Utilitários de Texto (`TextUtils`)

```python
class TextUtils:
    @staticmethod
    def slugify(text: str) -> str:
        # "Capítulo 1: Introdução" → "capitulo-1-introducao"
        ...
    
    @staticmethod
    def make_filename(url: str, title: str) -> str:
        # Gera: "cap1__capitulo-1-introducao.md"
        ...
    
    @staticmethod
    def clean(text: str) -> str:
        # Remove espaços extras, &nbsp;, tabs
        ...
    
    @staticmethod
    def collapse_blank_lines(text: str) -> str:
        # 3+ quebras de linha → 2 quebras
        ...
```

### 🔍 O que faz:
- Garante nomes de arquivo seguros e legíveis
- Normaliza texto para Markdown limpo


## 🔄 7. Extrator de Conteúdo (`ContentExtractor`)

Esta é a parte mais complexa. Vamos dividir:

### 7.1. Encontrar e Limpar o Conteúdo Principal

```python
@staticmethod
def _find_main_container(soup: BeautifulSoup) -> Tag:
    # Tenta encontrar <main>, <article>, .content, etc.
    # Fallback: <body>
    ...

@staticmethod
def _remove_noise(container: Tag) -> None:
    # Remove <script>, <style>, <nav>, <footer>, etc.
    ...
```

### 7.2. Conversão de Elementos HTML → Markdown

| HTML | Markdown |
|------|----------|
| `<h2>Título</h2>` | `## Título` |
| `<p>Texto <strong>negrito</strong></p>` | `Texto **negrito**` |
| `<ul><li>Item</li></ul>` | `- Item` |
| `<blockquote>Citação</blockquote>` | `> Citação` |
| `<pre><code>...` | ` ``` ` |

```python
@staticmethod
def _convert_inline(tag: Tag) -> str:
    # Processa <strong>, <em>, <code>, <a> dentro de parágrafos
    ...

@staticmethod
def _convert_list(tag: Tag, level: int = 0) -> str:
    # Converte listas aninhadas com indentação correta
    ...

@staticmethod
def _convert_table(table: Tag) -> str:
    # Gera tabela Markdown com alinhamento
    | Col1 | Col2 |
    |------|------|
    | A    | B    |
    ...
```

### 7.3. Método Principal: `extract()`

```python
def extract(self, html: str, url: str) -> tuple[str, str]:
    # 1. Parse HTML
    # 2. Extrai título
    # 3. Encontra container principal e remove ruído
    # 4. Percorre elementos de bloco e converte um a um
    # 5. Retorna (título, markdown)
    ...
```

### 💡 Design Pattern usado:
- **Visitor implícito**: `_process_block` "visita" cada tipo de tag e aplica a conversão adequada


## 💾 8. Persistência (`PersistenceService`)

```python
class PersistenceService:
    @staticmethod
    def save_markdown(output_dir, filename, content) -> Path:
        # Cria diretório se necessário e salva arquivo .md
        ...
    
    @staticmethod
    def write_index(output_dir, pages) -> None:
        # Gera index.md com lista navegável das páginas
        # Exemplo:
        # - [Capítulo 1](cap1__capitulo-1.md)
        #   - URL: `https://...`
        #   - Profundidade: `0`
        ...
    
    @staticmethod
    def write_manifest(output_dir, pages) -> None:
        # Gera manifest.json com todos os metadados
        # Útil para processamento posterior ou debugging
        ...
```


## 🕷️ 9. Orquestrador (`WebCrawler`)

```python
class WebCrawler:
    def __init__(self, config: CrawlerConfig):
        self.config = config
        self.http = HttpService(config)           # Injeção de dependência
        self.extractor = ContentExtractor()
    
    def _extract_links(self, html: str, current_url: str) -> list[str]:
        # Usa BeautifulSoup para encontrar <a href="...">
        # Filtra com UrlUtils.should_visit()
        # Remove duplicatas mantendo ordem
        ...
    
    def crawl(self, seed_urls: Iterable[str]) -> list[PageData]:
        # Algoritmo BFS (Breadth-First Search) com fila
        queue = deque()
        visited = set()
        
        # 1. Inicializa com seeds
        # 2. Enquanto houver URLs na fila:
        #    a. Respeita profundidade máxima
        #    b. Baixa HTML
        #    c. Extrai conteúdo e links
        #    d. Salva arquivo .md
        #    e. Agenda novos links (se dentro da profundidade)
        #    f. Aguarda REQUEST_DELAY para não sobrecarregar servidor
        # 3. Gera index.md e manifest.json
        ...
```

### 🔍 Fluxo Visual:
```
seed_urls → [Fila]
            ↓
     [URL + depth=0] → fetch_html → extract → save
            ↓
     links descobertos → [Fila] (depth+1)
            ↓
     Repete até fila vazia ou depth > MAX
```

### 💡 Por que BFS (fila) e não DFS (recursão)?
- Mais controle sobre profundidade
- Menos risco de estouro de pilha
- Processamento mais previsível


## 🚀 10. Entry Point (`main`)

```python
def main() -> None:
    config = CrawlerConfig()          # 1. Carrega configuração
    crawler = WebCrawler(config)      # 2. Cria orquestrador
    
    print("[INFO] Iniciando crawler...")
    pages = crawler.crawl(config.seed_urls)  # 3. Executa
    print(f"[INFO] Concluído. Total: {len(pages)}")
```

### 🔍 Por que não colocar tudo em `main`?
- `main` fica leve e legível
- Facilita reutilização (ex: chamar `crawl()` de outro script)
- Permite testes da lógica sem executar o programa inteiro


## 🧩 Diagrama de Dependências

```
main()
  │
  ▼
CrawlerConfig ← (dados imutáveis)
  │
  ▼
WebCrawler
  ├── HttpService → requests
  ├── ContentExtractor → BeautifulSoup
  ├── UrlUtils / TextUtils (estáticos)
  └── PersistenceService → json, Path
```

> ✅ **Baixo acoplamento**: Cada componente pode ser testado ou substituído isoladamente.


## 🎯 Resumo: Por que esta versão é mais legível?

| Critério | Versão Original | Versão Refatorada |
|----------|----------------|-------------------|
| **Organização** | Funções soltas | Classes por responsabilidade |
| **Configuração** | Variáveis globais | `CrawlerConfig` centralizado |
| **Nomenclatura** | Nomes longos/descritivos | Nomes curtos + contexto da classe |
| **Reutilização** | Código duplicado em `_process_block` | Métodos privados compartilhados |
| **Testabilidade** | Difícil de mockar | Injeção de dependência + métodos estáticos |
| **Extensibilidade** | Alterar comportamento = mexer em tudo | Substituir uma classe sem afetar outras |


## 🛠️ Como evoluir este código no futuro?

1. **Adicionar logging**:
   ```python
   import logging
   logger = logging.getLogger(__name__)
   logger.info(f"Visitando {url}")  # Ao invés de print()
   ```

2. **Suporte a proxies/autenticação**:
   ```python
   # Em CrawlerConfig:
   proxy: Optional[str] = None
   # Em HttpService:
   if self.config.proxy:
       self.session.proxies = {"http": self.config.proxy, "https": self.config.proxy}
   ```

3. **Cache de requisições** (evita re-baixar páginas):
   ```python
   from requests_cache import CachedSession
   self.session = CachedSession('crawler_cache', expire_after=3600)
   ```

4. **Parallelismo** (para crawling mais rápido):
   ```python
   from concurrent.futures import ThreadPoolExecutor
   # Processar múltiplas URLs simultaneamente (respeitando rate limit)
   ```

# 🚀 Como Executar o Código Refatorado

Siga este guia passo a passo para rodar o crawler no seu ambiente:

## 📋 Pré-requisitos

| Item | Versão Mínima | Como verificar |
|------|--------------|----------------|
| **Python** | 3.10+ | `python --version` |
| **pip** | 21.0+ | `pip --version` |
| **Git** (opcional) | Qualquer | `git --version` |

> 💡 **Dica para UFPI**: Se estiver nos laboratórios da universidade, verifique se o Python 3.10+ está disponível. Se não, considere usar um ambiente virtual ou conda.


## 🔧 Passo 1: Preparar o Ambiente

### Opção A: Ambiente Virtual (Recomendado)

```bash
# 1. Crie uma pasta para o projeto
mkdir engsoft-crawler
cd engsoft-crawler

# 2. Crie o ambiente virtual
python -m venv venv

# 3. Ative o ambiente
# No Linux/Mac:
source venv/bin/activate
# No Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# No Windows (CMD):
venv\Scripts\activate.bat
```

## 📦 Passo 2: Instalar Dependências

```bash
# Instale as bibliotecas necessárias
pip install requests beautifulsoup4

# (Opcional) Para desenvolvimento, adicione:
pip install black mypy pytest
```

> ✅ **Verificação rápida**:
> ```bash
> python -c "import requests, bs4; print('✓ Dependências OK')"
> ```

## 📄 Passo 3: Salvar o Código

1. Crie um arquivo chamado `crawler.py` na pasta do projeto
2. Cole **todo o código refatorado** que forneci anteriormente
3. Salve o arquivo

> 💡 **Dica**: Use um editor como VS Code ou PyCharm para evitar erros de indentação.


## ▶️ Passo 4: Executar o Crawler

```bash
# Com o ambiente virtual ativado:
python crawler.py
```

### 📊 Saída Esperada:
```
[INFO] Iniciando crawler...
[INFO] Visitando (nível 0): https://engsoftmoderna.info/
[INFO] Visitando (nível 0): https://engsoftmoderna.info/cap1.html
[INFO] Visitando (nível 1): https://engsoftmoderna.info/cap1.html#secao-1
...
[INFO] Concluído. Total de páginas salvas: 23
[INFO] Saída em: /caminho/para/engsoft-crawler/output
```


## 📁 Estrutura de Saída

Após a execução, você encontrará:

```
output/
├── index.md                 # Índice navegável das páginas
├── manifest.json            # Metadados em formato estruturado
├── home__engsoft-moderna.md # Página inicial convertida
├── cap1__capitulo-1.md      # Capítulo 1
├── cap2__capitulo-2.md      # Capítulo 2
└── ...                      # Demais páginas encontradas
```

### 🔍 Exemplo de `index.md`:
```markdown
# Índice do conteúdo extraído

Total de páginas coletadas: **23**

- [EngSoft Moderna](home__engsoft-moderna.md)
  - URL: `https://engsoftmoderna.info/`
  - Profundidade: `0`
- [Capítulo 1: Introdução](cap1__capitulo-1.md)
  - URL: `https://engsoftmoderna.info/cap1.html`
  - Profundidade: `0`
- [Seção 1.1: O que é ES?](cap1-secao1__o-que-e-es.md)
  - URL: `https://engsoftmoderna.info/cap1.html#secao-1`
  - Profundidade: `1`
```

## ⚙️ Personalizar a Execução (Opcional)

### Alterar Configurações Diretamente no Código

Edite a classe `CrawlerConfig` em `crawler.py`:

```python
@dataclass(frozen=True)
class CrawlerConfig:
    base_domain: str = "engsoftmoderna.info"
    max_depth: int = 3              # ← Aumentar profundidade
    request_delay: float = 1.0      # ← Mais lento = mais educado
    output_dir: Path = Path("meus_arquivos")  # ← Mudar pasta de saída
    ...
```

### Executar com Parâmetros via Linha de Comando (Avançado)

Se quiser tornar o script mais flexível, adicione este bloco no final do arquivo:

```python
# === Adicionar antes de if __name__ == "__main__": ===

import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Crawler para engsoftmoderna.info")
    parser.add_argument("--depth", type=int, default=2, help="Profundidade máxima")
    parser.add_argument("--output", type=str, default="output", help="Pasta de saída")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay entre requisições (s)")
    return parser.parse_args()

# === Substituir o main() por: ===

def main() -> None:
    args = parse_args()
    
    # Cria configuração personalizada
    config = CrawlerConfig(
        max_depth=args.depth,
        output_dir=Path(args.output),
        request_delay=args.delay
    )
    
    crawler = WebCrawler(config)
    print(f"[INFO] Iniciando crawler (profundidade={config.max_depth})...")
    pages = crawler.crawl(config.seed_urls)
    print(f"[INFO] Concluído. Total: {len(pages)} páginas em {config.output_dir}")
```

Agora você pode executar com opções:
```bash
# Profundidade 3, salvar em "meus_dados", delay de 1 segundo
python crawler.py --depth 3 --output meus_dados --delay 1.0
```


## 🐛 Solução de Problemas Comuns

| Problema | Causa Provável | Solução |
|----------|---------------|---------|
| `ModuleNotFoundError: No module named 'requests'` | Dependências não instaladas | `pip install requests beautifulsoup4` |
| `PermissionError` ao salvar arquivos | Pasta de saída sem permissão | Use `--output /tmp/crawler` ou execute com usuário adequado |
| Crawling muito lento | Delay alto ou rede lenta | Ajuste `request_delay` para 0.2 (mas seja educado!) |
| Nenhuma página salva | URLs bloqueadas ou domínio incorreto | Verifique `BASE_DOMAIN` e `should_visit()` |
| `SSL: CERTIFICATE_VERIFY_FAILED` | Problema com certificados SSL | `pip install certifi` ou use `REQUESTS_CA_BUNDLE` |


## 🧪 Testar Rapidamente (Modo Debug)

Para validar sem baixar tudo, edite temporariamente:

```python
# Em CrawlerConfig:
max_depth: int = 0              # Só as seeds
request_delay: float = 0.1      # Mais rápido para testes

# Ou use apenas uma seed:
def crawl(self, seed_urls: Iterable[str]) -> ...:
    # Adicione um break após a primeira página para teste
    if len(pages) >= 1:
        break  # ← Remova depois!
```

## 📦 Empacotar para Distribuição (Opcional)

Se quiser compartilhar com colegas ou alunos:

1. Crie um `requirements.txt`:
   ```bash
   pip freeze > requirements.txt
   ```

2. Adicione um `README.md` com instruções

3. (Opcional) Crie um `pyproject.toml` para instalação via pip:
   ```toml
   [project]
   name = "engsoft-crawler"
   version = "0.1.0"
   dependencies = ["requests", "beautifulsoup4"]
   ```

## ✅ Checklist de Verificação

- [ ] Python 3.10+ instalado
- [ ] Ambiente virtual ativado
- [ ] Dependências instaladas (`requests`, `beautifulsoup4`)
- [ ] Arquivo `crawler.py` salvo sem erros de sintaxe
- [ ] Permissão de escrita na pasta de saída
- [ ] Conexão com a internet ativa


> 🎓 **Dica para uso em aula**:  
> Você pode usar este crawler como exemplo prático em disciplinas de:
> - **Web Scraping** (mostrando ética e boas práticas)
> - **Engenharia de Software** (refatoração, SRP, testes)
> - **Processamento de Linguagem Natural** (pré-processamento de texto)

## Sugestões:

**adaptar o código para outro site**, **adicionar testes automatizados** ou **criar uma interface CLI mais completa**