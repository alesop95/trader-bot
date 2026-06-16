"""
Configurazione globale per il test suite.

Le variabili d'ambiente vengono impostate prima che pytest importi i moduli
di test, così Settings() di Pydantic può istanziarsi senza un .env reale.
I valori sono fittizi: i test unitari non effettuano I/O reale verso IBKR o DB.
"""

import os

os.environ.setdefault("IBKR_USERNAME", "test_user")
os.environ.setdefault("IBKR_PASSWORD", "test_pass")
os.environ.setdefault("IBKR_ACCOUNT", "DU000000")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_trader")
