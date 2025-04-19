# tests/conftest.py
import sys
import os

# Garante que o diretório raiz do projeto esteja no sys.path
# Isso permite que o pytest encontre o módulo "dadosAbertosSetorEletrico"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
