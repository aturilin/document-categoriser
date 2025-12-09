# Document Categorizer

LLM-категоризатор документов. Автоматически раскладывает markdown-заметки по [PARA-структуре](https://fortelabs.com/blog/para/) с помощью Claude API.

---

## Зачем это нужно

**Проблема:** За годы накапливаются тысячи заметок в Evernote, Notion, Obsidian. Они лежат в хаосе — без структуры, без тегов, без понимания что важно, а что устарело. Искать что-то невозможно, а разбирать вручную — это недели работы.

**Решение:** Этот инструмент использует Claude (LLM от Anthropic) чтобы автоматически:
- Прочитать каждую заметку
- Понять её содержание и контекст
- Присвоить категорию по методологии PARA
- Добавить теги и краткое описание
- Разложить по папкам

**Результат:** Структурированная база знаний с навигацией, готовая для использования в Obsidian или любом markdown-редакторе.

### Методология PARA

[PARA](https://fortelabs.com/blog/para/) — система организации информации от Tiago Forte, автора книги [Building a Second Brain](https://www.buildingasecondbrain.com/):

| Буква | Категория | Что туда |
|-------|-----------|----------|
| **P** | Projects | Активные проекты с дедлайнами |
| **A** | Areas | Сферы жизни (здоровье, финансы, карьера) |
| **R** | Resources | Справочные материалы на будущее |
| **A** | Archive | Завершённое и неактуальное |

В этом инструменте используются **Areas**, **Resources** и **Archive** (Projects обычно ведутся отдельно в таск-менеджерах).

**Полезные ссылки:**
- [The PARA Method](https://fortelabs.com/blog/para/) — оригинальная статья
- [Building a Second Brain](https://www.buildingasecondbrain.com/) — книга и курс
- [Obsidian](https://obsidian.md/) — редактор для работы с результатом

---

## Что нужно для работы

| Требование | Где взять |
|------------|-----------|
| **Python 3.9+** | `brew install python` или [python.org](https://python.org) |
| **Anthropic API Key** | [console.anthropic.com](https://console.anthropic.com/) → API Keys |
| **Markdown-файлы** | Экспорт из Evernote, Notion, или любые `.md` файлы |

### Про документы

**Если у вас Evernote:**
- Экспортируйте заметки через File → Export → HTML (или ENEX)
- Конвертируйте в Markdown (например, через [evernote2md](https://github.com/wormi4ok/evernote2md))
- Положите `.md` файлы в папку `input/`

**Если у вас Obsidian:**
- Просто скопируйте vault в `input/`
- После категоризации можно открыть `output/` как новый vault
- MOC-файлы (`_MOC/`) будут работать как навигационные хабы

---

## Быстрый старт

### 1. Клонировать и установить

```bash
git clone https://github.com/aturilin/document-categoriser.git
cd document-categoriser
pip install -r requirements.txt
```

### 2. Добавить API ключ

```bash
echo 'ANTHROPIC_API_KEY=sk-ant-ваш-ключ' > .env
```

Ключ берём тут: [console.anthropic.com](https://console.anthropic.com/) → API Keys

### 3. Положить документы

```bash
cp /путь/к/вашим/заметкам/*.md input/
```

### 4. Запустить

```bash
# Сначала тест (ничего не меняет)
python3 categorize.py --dry-run --limit 5

# Обработать 10 файлов
python3 categorize.py --limit 10

# Обработать всё
python3 categorize.py

# Продолжить если прервалось
python3 categorize.py --resume
```

### 5. Построить индекс и навигацию

```bash
python3 build_index.py      # индекс для поиска
python3 generate_moc.py     # MOC-хабы для навигации
```

---

## Структура папок

```
document-categoriser/
├── input/                    # Сюда кладёте файлы
├── output/                   # Тут появятся отсортированные
│   ├── areas/               # Текущие сферы жизни
│   │   ├── health/          # здоровье
│   │   ├── finance/         # финансы
│   │   ├── career/          # карьера
│   │   └── family/          # семья
│   ├── resources/           # Справочные материалы
│   │   ├── data-science/    # ML, аналитика
│   │   ├── programming/     # код
│   │   ├── business/        # бизнес
│   │   └── personal-dev/    # саморазвитие
│   ├── archive/             # Неактуальное
│   │   └── outdated/
│   └── _MOC/                # Навигационные хабы
├── data/                    # Индекс, статистика, чекпоинты
└── *.py                     # Скрипты
```

---

## Категории PARA

| Категория | Описание | Примеры |
|-----------|----------|---------|
| **areas** | Текущие сферы жизни | здоровье, финансы, карьера, семья |
| **resources** | Справочник на потом | программирование, книги, бизнес |
| **archive** | Завершённое/устаревшее | старые проекты, неактуальное |

---

## Команды

### categorize.py

```bash
python3 categorize.py [опции]

--dry-run     Тест без изменений
--limit N     Обработать только N файлов
--resume      Продолжить с чекпоинта
```

### build_index.py

```bash
python3 build_index.py [опции]

--stats       Только статистика (не писать файл)
```

### generate_moc.py

```bash
python3 generate_moc.py [опции]

--preview     Превью без записи файлов
```

---

## Что получается

После обработки файл получает frontmatter:

```markdown
---
title: "Заметки по Python ML"
category: resources
subcategory: data-science
tags: ["machine-learning", "python", "sklearn"]
summary: "Конспект по алгоритмам ML"
processed: 2025-01-15
---

# Оригинальный контент...
```

---

## Стоимость

| Модель | За документ | За 1000 документов |
|--------|-------------|-------------------|
| Claude Sonnet | ~$0.003 | ~$3 |
| Claude Haiku | ~$0.0003 | ~$0.30 |

---

## Настройка

### Изменить категории

Редактируйте `CATEGORIES` в `categorize.py`:

```python
CATEGORIES = {
    "areas": ["health", "finance", "career", "family"],
    "resources": ["programming", "business"],
    "archive": ["outdated"],
}
```

### Сменить модель

```python
CONFIG = {
    "model": "claude-3-haiku-20240307",  # дешевле, быстрее
    # или
    "model": "claude-sonnet-4-20250514",  # качественнее
}
```

---

## Лицензия

MIT
