import re
import os
import time
import urllib.parse
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
try:
    from deep_translator import GoogleTranslator
except ImportError:
    print('Installing deep-translator...')
    import subprocess
    subprocess.check_call(['uv', 'pip', 'install', 'deep-translator'])
    from deep_translator import GoogleTranslator
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
README_SOURCE = PROJECT_ROOT / 'README.md'
README_DIR = PROJECT_ROOT / 'resources' / 'readme'
LANGUAGES = {'zh_CN': {'name': 'Simplified Chinese', 'code': 'zh-CN'}, 'de_DE': {'name': 'German', 'code': 'de'}, 'es_ES': {'name': 'Spanish', 'code': 'es'}, 'fr_FR': {'name': 'French', 'code': 'fr'}, 'ru_RU': {'name': 'Russian', 'code': 'ru'}, 'ja_JP': {'name': 'Japanese', 'code': 'ja'}, 'ko_KR': {'name': 'Korean', 'code': 'ko'}, 'pt_BR': {'name': 'Portuguese (Brazil)', 'code': 'pt'}, 'pt_PT': {'name': 'Portuguese (Portugal)', 'code': 'pt'}}
TRANSLATIONS = {'zh_CN': {'title': 'Palworld \u7684\u7efc\u5408\u4fdd\u5b58\u6587\u4ef6\u7f16\u8f91\u5de5\u5177\u5305', 'download_text': '\u4ece', 'download_link': '\u4e0b\u8f7d\u72ec\u7acb\u7248\u672c', 'toc': '\u76ee\u5f55', 'features': '\u7279\u70b9', 'installation': '\u5b89\u88c5', 'quick_start': '\u5feb\u901f\u5165\u95e8', 'tools_overview': '\u5de5\u5177\u6982\u8ff0', 'guides': '\u6307\u5357', 'troubleshooting': '\u6545\u969c\u6392\u9664', 'building': '\u6784\u5efa\u72ec\u7acb\u53ef\u6267\u884c\u6587\u4ef6', 'contributing': '\u8d21\u732e', 'license': '\u8bb8\u53ef\u8bc1', 'back_to_top': '\u8fd4\u56de\u9876\u90e8', 'made_with_love': '\u7528 \u2764\ufe0f \u4e3a Palworld \u793e\u533a\u5236\u4f5c'}, 'de_DE': {'title': 'Ein umfassendes Toolkit zur Bearbeitung gespeicherter Dateien f\u00fcr Palworld', 'download_text': 'Laden Sie die Standalone-Version von', 'download_link': 'herunter', 'toc': 'Inhaltsverzeichnis', 'features': 'Funktionen', 'installation': 'Installation', 'quick_start': 'Schnellstart', 'tools_overview': 'Tools-\u00dcbersicht', 'guides': 'Anleitungen', 'troubleshooting': 'Fehlerbehebung', 'building': 'Erstellen einer eigenst\u00e4ndigen ausf\u00fchrbaren Datei', 'contributing': 'Mitwirken', 'license': 'Lizenz', 'back_to_top': 'Nach oben', 'made_with_love': 'Hergestellt mit \u2764\ufe0f f\u00fcr die Palworld-Community'}, 'es_ES': {'title': 'Un kit de herramientas completo para editar archivos de guardado de Palworld', 'download_text': 'Descarga la versi\u00f3n independiente de', 'download_link': '', 'toc': '\u00cdndice', 'features': 'Caracter\u00edsticas', 'installation': 'Instalaci\u00f3n', 'quick_start': 'Inicio r\u00e1pido', 'tools_overview': 'Descripci\u00f3n de herramientas', 'guides': 'Gu\u00edas', 'troubleshooting': 'Soluci\u00f3n de problemas', 'building': 'Compilar ejecutable independiente', 'contributing': 'Contribuir', 'license': 'Licencia', 'back_to_top': 'Volver arriba', 'made_with_love': 'Hecho con \u2764\ufe0f para la comunidad de Palworld'}, 'fr_FR': {'title': "Une bo\u00eete \u00e0 outils compl\u00e8te pour l'\u00e9dition de fichiers de sauvegarde Palworld", 'download_text': 'T\u00e9l\u00e9chargez la version autonome depuis', 'download_link': '', 'toc': 'Table des mati\u00e8res', 'features': 'Fonctionnalit\u00e9s', 'installation': 'Installation', 'quick_start': 'D\u00e9marrage rapide', 'tools_overview': 'Aper\u00e7u des outils', 'guides': 'Guides', 'troubleshooting': 'D\u00e9pannage', 'building': "Compiler l'ex\u00e9cutable autonome", 'contributing': 'Contribuer', 'license': 'Licence', 'back_to_top': 'Retour en haut', 'made_with_love': 'Fait avec \u2764\ufe0f pour la communaut\u00e9 Palworld'}, 'ru_RU': {'title': '\u041a\u043e\u043c\u043f\u043b\u0435\u043a\u0441\u043d\u044b\u0439 \u043d\u0430\u0431\u043e\u0440 \u0438\u043d\u0441\u0442\u0440\u0443\u043c\u0435\u043d\u0442\u043e\u0432 \u0434\u043b\u044f \u0440\u0435\u0434\u0430\u043a\u0442\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u044f \u0444\u0430\u0439\u043b\u043e\u0432 \u0441\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u0438\u0439 Palworld', 'download_text': '\u0421\u043a\u0430\u0447\u0430\u0439\u0442\u0435 \u0430\u0432\u0442\u043e\u043d\u043e\u043c\u043d\u0443\u044e \u0432\u0435\u0440\u0441\u0438\u044e \u0441', 'download_link': '', 'toc': '\u0421\u043e\u0434\u0435\u0440\u0436\u0430\u043d\u0438\u0435', 'features': '\u0412\u043e\u0437\u043c\u043e\u0436\u043d\u043e\u0441\u0442\u0438', 'installation': '\u0423\u0441\u0442\u0430\u043d\u043e\u0432\u043a\u0430', 'quick_start': '\u0411\u044b\u0441\u0442\u0440\u044b\u0439 \u0441\u0442\u0430\u0440\u0442', 'tools_overview': '\u041e\u0431\u0437\u043e\u0440 \u0438\u043d\u0441\u0442\u0440\u0443\u043c\u0435\u043d\u0442\u043e\u0432', 'guides': '\u0420\u0443\u043a\u043e\u0432\u043e\u0434\u0441\u0442\u0432\u0430', 'troubleshooting': '\u0423\u0441\u0442\u0440\u0430\u043d\u0435\u043d\u0438\u0435 \u043d\u0435\u043f\u043e\u043b\u0430\u0434\u043e\u043a', 'building': '\u0421\u0431\u043e\u0440\u043a\u0430 \u0430\u0432\u0442\u043e\u043d\u043e\u043c\u043d\u043e\u0433\u043e \u0438\u0441\u043f\u043e\u043b\u043d\u044f\u0435\u043c\u043e\u0433\u043e \u0444\u0430\u0439\u043b\u0430', 'contributing': '\u0423\u0447\u0430\u0441\u0442\u0438\u0435', 'license': '\u041b\u0438\u0446\u0435\u043d\u0437\u0438\u044f', 'back_to_top': '\u041d\u0430\u0432\u0435\u0440\u0445', 'made_with_love': '\u0421\u043e\u0437\u0434\u0430\u043d\u043e \u0441 \u2764\ufe0f \u0434\u043b\u044f \u0441\u043e\u043e\u0431\u0449\u0435\u0441\u0442\u0432\u0430 Palworld'}, 'ja_JP': {'title': 'Palworld \u7528\u306e\u5305\u62ec\u7684\u306a\u30bb\u30fc\u30d6\u30d5\u30a1\u30a4\u30eb\u7de8\u96c6\u30c4\u30fc\u30eb\u30ad\u30c3\u30c8', 'download_text': '\u30b9\u30bf\u30f3\u30c9\u30a2\u30ed\u30f3 \u30d0\u30fc\u30b8\u30e7\u30f3\u3092', 'download_link': '\u304b\u3089\u30c0\u30a6\u30f3\u30ed\u30fc\u30c9\u3057\u307e\u3059', 'toc': '\u76ee\u6b21', 'features': '\u7279\u5fb4', 'installation': '\u30a4\u30f3\u30b9\u30c8\u30fc\u30eb', 'quick_start': '\u30af\u30a4\u30c3\u30af\u30b9\u30bf\u30fc\u30c8', 'tools_overview': '\u30c4\u30fc\u30eb\u306e\u6982\u8981', 'guides': '\u30ac\u30a4\u30c9', 'troubleshooting': '\u30c8\u30e9\u30d6\u30eb\u30b7\u30e5\u30fc\u30c6\u30a3\u30f3\u30b0', 'building': '\u30b9\u30bf\u30f3\u30c9\u30a2\u30ed\u30f3\u5b9f\u884c\u53ef\u80fd\u30d5\u30a1\u30a4\u30eb\u306e\u30d3\u30eb\u30c9', 'contributing': '\u8ca2\u732e\u3059\u308b', 'license': '\u30e9\u30a4\u30bb\u30f3\u30b9', 'back_to_top': '\u30c8\u30c3\u30d7\u306b\u623b\u308b', 'made_with_love': 'Palworld \u30b3\u30df\u30e5\u30cb\u30c6\u30a3\u306e\u305f\u3081\u306b \u2764\ufe0f \u3067\u4f5c\u6210\u3055\u308c\u307e\u3057\u305f'}, 'ko_KR': {'title': 'Palworld\ub97c \uc704\ud55c \ud3ec\uad04\uc801\uc778 \uc800\uc7a5 \ud30c\uc77c \ud3b8\uc9d1 \ud234\ud0b7', 'download_text': '', 'download_link': '\uc5d0\uc11c \ub3c5\ub9bd\ud615 \ubc84\uc804\uc744 \ub2e4\uc6b4\ub85c\ub4dc\ud558\uc138\uc694', 'toc': '\ubaa9\ucc28', 'features': '\uae30\ub2a5', 'installation': '\uc124\uce58', 'quick_start': '\ube60\ub978 \uc2dc\uc791', 'tools_overview': '\ub3c4\uad6c \uac1c\uc694', 'guides': '\uac00\uc774\ub4dc', 'troubleshooting': '\ubb38\uc81c \ud574\uacb0', 'building': '\ub3c5\ub9bd\ud615 \uc2e4\ud589 \ud30c\uc77c \ube4c\ub4dc', 'contributing': '\uae30\uc5ec', 'license': '\ub77c\uc774\uc13c\uc2a4', 'back_to_top': '\ub9e8 \uc704\ub85c', 'made_with_love': 'Palworld \ucee4\ubba4\ub2c8\ud2f0\ub97c \uc704\ud574 \u2764\ufe0f\uc73c\ub85c \uc81c\uc791'}, 'pt_BR': {'title': 'Um kit de ferramentas completo para editar arquivos de salvamento do Palworld', 'download_text': 'Baixe a versao autonoma do', 'download_link': '', 'toc': 'Indice', 'features': 'Recursos', 'installation': 'Instalacao', 'quick_start': 'Inicio rapido', 'tools_overview': 'Visao geral das ferramentas', 'guides': 'Guias', 'troubleshooting': 'Solucao de problemas', 'building': 'Compilar executavel autonomo', 'contributing': 'Contribuir', 'license': 'Licenca', 'back_to_top': 'Voltar ao topo', 'made_with_love': 'Feito com \u2764\ufe0f para a comunidade Palworld'}}
HEADER_SECTION = '<div align="center">\n\n![PalworldSaveTools Logo](../assets/branding/PalworldSaveTools_Blue.png)\n\n# PalworldSaveTools\n\n**{title}**\n\n[![Downloads](https://img.shields.io/github/downloads/CyrixJD115/PalworldSaveTools-Legacy/total)](https://github.com/CyrixJD115/PalworldSaveTools-Legacy/releases/latest)\n[![License](https://img.shields.io/github/license/CyrixJD115/PalworldSaveTools-Legacy)](LICENSE)\n[![Discord](https://img.shields.io/badge/Discord-Join_for_support-blue)](https://discord.gg/YWZFPy9G8J)\n[![NexusMods](https://img.shields.io/badge/NexusMods-Download-orange)](https://www.nexusmods.com/palworld/mods/3190)\n\n[English](../../README.md) | [简体中文](README.zh_CN.md) | [Deutsch](README.de_DE.md) | [Español](README.es_ES.md) | [Français](README.fr_FR.md) | [Русский](README.ru_RU.md) | [日本語](README.ja_JP.md) | [한국어](README.ko_KR.md) | [Português (Brasil)](README.pt_BR.md) | [Português (Portugal)](README.pt_PT.md)\n\n---\n\n### **{download_text} [GitHub Releases](https://github.com/CyrixJD115/PalworldSaveTools-Legacy/releases/latest)** {download_link}\n\n---\n\n</div>\n'
SECTION_HEADERS = ['Features', 'Installation', 'Quick Start', 'Tools Overview', 'Guides', 'Troubleshooting', 'Building Standalone Executable', 'Contributing', 'License']
CODE_BLOCK_PATTERN = re.compile('```[\\s\\S]*?```', re.MULTILINE)
INLINE_CODE_PATTERN = re.compile('`[^`]+`')
URL_PATTERN = re.compile('https?://[^\\s\\)\\]>"]+')
ANCHOR_LINK_PATTERN = re.compile('\\[([^\\]]+)\\]\\(#[^\\)]+\\)')
MD_LINK_PATTERN = re.compile('\\[([^\\]]+)\\]\\([^\\)]+\\)')
IMAGE_PATTERN = re.compile('!\\[([^\\]]*)\\]\\([^\\)]+\\)')
HTML_TAG_PATTERN = re.compile('<(?:details|summary|div|align|br|hr|table|tr|td|th|thead|tbody|ul|ol|li|p|a|img|strong|b|em|i|code|pre|span|sub|sup|h[1-6])[^>]*>', re.IGNORECASE)
HTML_CLOSING_TAG_PATTERN = re.compile('</(?:details|summary|div|table|tr|td|th|thead|tbody|ul|ol|li|p|a|strong|b|em|i|code|pre|span|sub|sup|h[1-6])>', re.IGNORECASE)
class PlaceholderManager:
    def __init__(self):
        self.placeholders: Dict[str, str] = {}
        self.counter = 0
    def add(self, text: str, prefix: str='P') -> str:
        key = f'__{prefix}{self.counter}__'
        self.placeholders[key] = text
        self.counter += 1
        return key
    def restore(self, text: str) -> str:
        def get_counter(item):
            key = item[0]
            match = re.search('(\\d+)', key)
            return int(match.group(1)) if match else 0
        for key, value in sorted(self.placeholders.items(), key=lambda x: -get_counter(x)):
            text = text.replace(key, value)
        return text
    def clear(self):
        self.placeholders = {}
        self.counter = 0
def protect_code_blocks(text: str, pm: PlaceholderManager) -> str:
    def replace_code(match):
        return pm.add(match.group(0), 'C')
    return CODE_BLOCK_PATTERN.sub(replace_code, text)
def protect_inline_code(text: str, pm: PlaceholderManager) -> str:
    def replace_inline(match):
        return pm.add(match.group(0), 'I')
    return INLINE_CODE_PATTERN.sub(replace_inline, text)
def protect_urls(text: str, pm: PlaceholderManager) -> str:
    def replace_url(match):
        return pm.add(match.group(0), 'U')
    return URL_PATTERN.sub(replace_url, text)
def protect_images(text: str, pm: PlaceholderManager) -> str:
    def replace_img(match):
        return pm.add(match.group(0), 'M')
    return IMAGE_PATTERN.sub(replace_img, text)
def protect_markdown_links(text: str, pm: PlaceholderManager) -> str:
    def replace_link(match):
        full = match.group(0)
        if '](' in full and '(#' in full:
            return full
        return pm.add(full, 'L')
    return MD_LINK_PATTERN.sub(replace_link, text)
def protect_anchor_links(text: str, pm: PlaceholderManager) -> str:
    toc_start = text.find('## Table of Contents')
    if toc_start == -1:
        toc_start = text.find('## 目次')
    if toc_start != -1:
        toc_end_pattern = re.compile('\\n## ', re.MULTILINE)
        toc_end_match = toc_end_pattern.search(text, toc_start + 10)
        if toc_end_match:
            before_toc = text[:toc_start]
            toc_section = text[toc_start:toc_end_match.start()]
            after_toc = text[toc_end_match.start():]
            def replace_anchor(match):
                return pm.add(match.group(0), 'A')
            before_toc = ANCHOR_LINK_PATTERN.sub(replace_anchor, before_toc)
            after_toc = ANCHOR_LINK_PATTERN.sub(replace_anchor, after_toc)
            return before_toc + toc_section + after_toc
    def replace_anchor(match):
        return pm.add(match.group(0), 'A')
    return ANCHOR_LINK_PATTERN.sub(replace_anchor, text)
def protect_html_tags(text: str, pm: PlaceholderManager) -> str:
    def replace_tag(match):
        return pm.add(match.group(0), 'H')
    result = HTML_TAG_PATTERN.sub(replace_tag, text)
    result = HTML_CLOSING_TAG_PATTERN.sub(replace_tag, result)
    return result
def protect_platform_terms(text: str, pm: PlaceholderManager) -> str:
    platform_terms = ['Discord', 'GitHub', 'Steam', 'GamePass', 'NexusMods', 'Wiki', 'uv']
    protected_text = text
    for term in platform_terms:
        pattern = re.compile(re.escape(term))
        def replace_platform(match):
            return pm.add(match.group(0), 'P')
        protected_text = pattern.sub(replace_platform, protected_text)
    return protected_text
def protect_game_terms(text: str, pm: PlaceholderManager) -> str:
    game_terms = ['Pal Editor', '\\bpals?\\b', '\\bPal\\b', '\\bIVs\\b', '\\bIV\\b', 'passives', 'private chests', 'PalworldSaveTools']
    for term in sorted(game_terms, key=len, reverse=True):
        pattern = re.compile(term, re.IGNORECASE)
        def replace_game(match):
            return pm.add(match.group(0), 'G')
        text = pattern.sub(replace_game, text)
    return text
def protect_common_terms(text: str, pm: PlaceholderManager) -> str:
    common_terms = [('private', '\\bprivate\\b')]
    for term, pattern_str in common_terms:
        pattern = re.compile(pattern_str)
        def replace_common(match):
            return pm.add(match.group(0), 'C')
        text = pattern.sub(replace_common, text)
    return text
def generate_anchor_id(text: str) -> str:
    anchor = text.lower().strip()
    anchor = re.sub('[^\\w\\s-]', '', anchor, flags=re.UNICODE)
    anchor = re.sub('\\s+', '-', anchor)
    anchor = re.sub('-+', '-', anchor)
    return anchor
def extract_toc_section(content: str) -> Tuple[str, str, str]:
    toc_pattern = re.compile('(## Table of Contents\\s*\\n(?:-+\\s*\\n)?)(.*?)(?=\\n---\\s*\\n## )', re.DOTALL)
    match = toc_pattern.search(content)
    if match:
        toc_header = match.group(1)
        toc_body = match.group(2)
        remaining = content[:match.start()] + content[match.end():]
        return (toc_header, toc_body, remaining)
    return ('', '', content)
def build_toc_from_content(content: str, lang_code: str) -> str:
    translations = TRANSLATIONS.get(lang_code, {})
    heading_pattern = re.compile('^## ([^\\n]+)', re.MULTILINE)
    headings = heading_pattern.findall(content)
    toc_lines = [f"## {translations.get('toc', 'Table of Contents')}", '']
    for heading in headings:
        if heading.lower() in ['table of contents', translations.get('toc', '').lower()]:
            continue
        anchor = generate_anchor_id(heading)
        toc_lines.append(f'- [{heading}](#{anchor})')
    return '\n'.join(toc_lines)
def split_text_for_translation(text: str, max_length: int=4500) -> List[str]:
    if len(text) <= max_length:
        return [text]
    chunks = []
    lines = text.split('\n')
    current_chunk = []
    current_length = 0
    for line in lines:
        line_length = len(line) + 1
        if current_length + line_length > max_length and current_chunk:
            chunks.append('\n'.join(current_chunk))
            current_chunk = []
            current_length = 0
        current_chunk.append(line)
        current_length += line_length
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    return chunks
def translate_text(text: str, target_lang: str, source_lang: str='en') -> str:
    try:
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        chunks = split_text_for_translation(text)
        translated_chunks = []
        for i, chunk in enumerate(chunks):
            if chunk.strip():
                if i > 0:
                    time.sleep(0.5)
                translated = translator.translate(chunk)
                translated_chunks.append(translated)
            else:
                translated_chunks.append(chunk)
        return '\n'.join(translated_chunks)
    except Exception as e:
        print(f'Translation error: {e}')
        return text
def extract_content_after_header(content: str) -> str:
    header_end_pattern = re.compile('</div>\\s*\\n', re.MULTILINE)
    match = header_end_pattern.search(content)
    if match:
        return content[match.end():]
    return content
def fix_section_anchors(content: str) -> str:
    def fix_heading(match):
        level = match.group(1)
        text = match.group(2).strip()
        return f'{level} {text}'
    return re.sub('^(#{2,3})\\s+(.+)$', fix_heading, content, flags=re.MULTILINE)
_print_lock = threading.Lock()
def safe_print(*args, **kwargs):
    with _print_lock:
        try:
            print(*args, **kwargs)
        except UnicodeEncodeError:
            for arg in args:
                try:
                    print(str(arg).encode('utf-8', errors='ignore').decode('utf-8'), **kwargs)
                except:
                    print('[Unicode Error]', **kwargs)
def translate_typing_svgs(body: str, target_lang: str) -> str:
    TYPING_SVG_RE = re.compile(
        r'(<img src="https://readme-typing-svg\.demolab\.com\?lines=)([^"&]+)(&[^>]*/>)'
    )
    all_lines = set()
    for m in TYPING_SVG_RE.finditer(body):
        decoded = urllib.parse.unquote_plus(m.group(2))
        for line in decoded.split(';'):
            all_lines.add(line.strip())
    if not all_lines:
        return body
    sorted_lines = sorted(all_lines)
    translator = GoogleTranslator(source='en', target=target_lang)
    batch = '\n'.join(sorted_lines)
    translated_batch = translator.translate(batch)
    translated_lines = translated_batch.split('\n')
    mapping = dict(zip(sorted_lines, translated_lines))
    for original in sorted_lines:
        mapping.setdefault(original, original)
    def replace_svg(m):
        prefix = m.group(1)
        suffix = m.group(3)
        decoded = urllib.parse.unquote_plus(m.group(2))
        lines = decoded.split(';')
        translated = [mapping.get(line.strip()) or line.strip() for line in lines]
        new_param = urllib.parse.quote_plus(';'.join(translated), safe=';/')
        return f'{prefix}{new_param}{suffix}'
    return TYPING_SVG_RE.sub(replace_svg, body)

def translate_readme(target_lang_code: str, target_file_code: str, lang_name: str, quiet: bool=False):
    if not quiet:
        safe_print(f"\n{'=' * 50}")
        safe_print(f'Translating to {lang_name} ({target_lang_code})...')
        safe_print(f"{'=' * 50}")
    with open(README_SOURCE, 'r', encoding='utf-8') as f:
        content = f.read()
    translations = TRANSLATIONS.get(target_file_code, {})
    header = HEADER_SECTION.format(title=translations.get('title', 'A comprehensive save file editing toolkit for Palworld'), download_text=translations.get('download_text', 'Download the standalone version from'), download_link=translations.get('download_link', ''))
    body_content = extract_content_after_header(content)
    body_content = translate_typing_svgs(body_content, target_lang_code)
    pm = PlaceholderManager()
    protected = protect_code_blocks(body_content, pm)
    protected = protect_inline_code(protected, pm)
    protected = protect_images(protected, pm)
    protected = protect_urls(protected, pm)
    protected = protect_markdown_links(protected, pm)
    protected = protect_anchor_links(protected, pm)
    protected = protect_html_tags(protected, pm)
    protected = protect_platform_terms(protected, pm)
    protected = protect_game_terms(protected, pm)
    if not quiet:
        safe_print(f'  Protected {len(pm.placeholders)} elements')
        safe_print(f'  Translating body content...')
    translated = translate_text(protected, target_lang_code)
    translated = pm.restore(translated)
    translated = re.sub('\\!\\[([^\\]]*)\\]\\(resources/', '![\\1](../', translated)
    translated = re.sub('^(#{2,4})[ \\u00a0\\t]?', '\\1 ', translated, flags=re.MULTILINE)
    translated = re.sub('^(#{2,4})([^\\s#])', '\\1 \\2', translated, flags=re.MULTILINE)
    toc_header = translations.get('toc', 'Table of Contents')
    heading_pattern = re.compile('^## ([^\\n]+)', re.MULTILINE)
    headings = heading_pattern.findall(translated)
    new_toc_items = []
    toc_variants = ['table of contents', 'contents', '目录', 'inhaltsverzeichnis', 'índice', 'indice', 'table des matières', 'содержание', '目次', '목차', 'tabla de contenidos']
    excluded_sections = ['disclaimer', '免責事項', '免责声明', '면책조항', 'haftungsausschluss', 'descargo de responsabilidad', 'exonération de responsabilité', 'avertissement', 'отказ от ответственности', 'support', 'サポート', '지원', '支持', 'unterstützung', 'soporte', 'soutien', 'assistance', 'поддержка', 'acknowledgments', '謝辞', '致谢', 'danksagungen', 'agradecimientos', 'remerciements', 'благодарности', '감사의 말씀']
    for heading in headings:
        heading_lower = heading.lower().strip()
        if heading_lower in [v.lower() for v in toc_variants]:
            continue
        if any((excl in heading_lower for excl in excluded_sections)):
            continue
        anchor = generate_anchor_id(heading)
        new_toc_items.append(f'- [{heading}](#{anchor})')
    new_toc_text = '\n'.join(new_toc_items)
    toc_pattern = re.compile('^## [^\\n]+\\n+(?:-+\\n+)?(?:- \\[[^\\]]+\\]\\([^)]+\\)\\n)+', re.MULTILINE)
    new_toc_section = f'\n## {toc_header}\n\n{new_toc_text}\n'
    translated = toc_pattern.sub(new_toc_section, translated, count=1)
    final_content = header + translated
    output_path = README_DIR / f'README.{target_file_code}.md'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
    if not quiet:
        safe_print(f'  Saved to: {output_path}')
        safe_print(f'  Done!')
    return (target_file_code, True, str(output_path))
def translate_all():
    print('\n' + '=' * 60)
    print('  README AUTO-TRANSLATOR (PARALLEL)')
    print('  Translating README.md to all supported languages')
    print('=' * 60)
    if not README_SOURCE.exists():
        print(f'\nError: Source README not found at {README_SOURCE}')
        return False
    README_DIR.mkdir(parents=True, exist_ok=True)
    print(f'\n  Translating {len(LANGUAGES)} languages in parallel...')
    for lang_code, lang_info in LANGUAGES.items():
        print(f"    - {lang_info['name']} ({lang_info['code']})")
    print()
    start_time = time.time()
    results = []
    with ThreadPoolExecutor(max_workers=len(LANGUAGES)) as executor:
        future_to_lang = {executor.submit(translate_readme, lang_info['code'], lang_code, lang_info['name'], quiet=True): (lang_code, lang_info['name']) for lang_code, lang_info in LANGUAGES.items()}
        for future in as_completed(future_to_lang):
            lang_code, lang_name = future_to_lang[future]
            try:
                result = future.result()
                results.append(result)
                safe_print(f'  ✓ {lang_name} ({lang_code}) completed')
            except Exception as e:
                safe_print(f'  ✗ {lang_name} ({lang_code}) failed: {e}')
                results.append((lang_code, False, str(e)))
    elapsed_time = time.time() - start_time
    print('\n' + '=' * 60)
    print('  TRANSLATION SUMMARY')
    print('=' * 60)
    results.sort(key=lambda x: list(LANGUAGES.keys()).index(x[0]) if x[0] in LANGUAGES else 999)
    for lang_code, success, info in results:
        status = 'SUCCESS' if success else 'FAILED'
        print(f'  {lang_code}: {status}')
    success_count = sum((1 for _, s, _ in results if s))
    print(f'\n  Total: {success_count}/{len(results)} successful')
    print(f'  Time: {elapsed_time:.1f} seconds')
    return all((s for _, s, _ in results))
def translate_single(lang_code: str):
    if lang_code not in LANGUAGES:
        print(f"Error: Unknown language code '{lang_code}'")
        print(f"Available: {', '.join(LANGUAGES.keys())}")
        return False
    lang_info = LANGUAGES[lang_code]
    return translate_readme(lang_info['code'], lang_code, lang_info['name'])
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Translate README.md to supported languages')
    parser.add_argument('language', nargs='?', default='all', help="Language code to translate (e.g., zh_CN, de_DE). Use 'all' for all languages.")
    parser.add_argument('--list', '-l', action='store_true', help='List available languages')
    args = parser.parse_args()
    if args.list:
        print('\nAvailable languages:')
        for code, info in LANGUAGES.items():
            print(f"  {code}: {info['name']}")
        exit(0)
    if args.language == 'all':
        success = translate_all()
    else:
        success = translate_single(args.language)
    exit(0 if success else 1)