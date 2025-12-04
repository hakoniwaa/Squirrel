# Installation

## Requirements

- Python 3.8+
- OpenAI API key (for memory processing)

## Install from PyPI

```bash
pip install memorisdk
```

## Install from Source

```bash
git clone https://github.com/GibsonAI/memori.git
cd memori
pip install -e .
```

## Development Installation

```bash
git clone https://github.com/GibsonAI/memori.git
cd memori
pip install -e ".[dev]"
```

## Verify Installation

```python
from memori import Memori
print("Memoriai installed successfully!")
```

## Database Setup

### SQLite (Default)
No additional setup required - SQLite database will be created automatically.

### PostgreSQL
```bash
pip install psycopg2-binary
```

### MySQL
```bash
pip install mysqlclient
# or
pip install PyMySQL
```

## API Key Setup

### Option 1: Environment Variable
```bash
export OPENAI_API_KEY="sk-your-openai-key-here"
```

### Option 2: .env File
Create `.env` file in your project:
```
OPENAI_API_KEY=sk-your-openai-key-here
```

### Option 3: Direct Configuration
```python
from memori import Memori

memori = Memori(openai_api_key="sk-your-openai-key-here")
```