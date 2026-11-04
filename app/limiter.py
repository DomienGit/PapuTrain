"""Limiter zapytań (rate limiting) — ochrona przed brute force na logowaniu.

Osobny moduł, żeby main.py i routery mogły go importować bez importu
cyklicznego (routery nie mogą importować z main, bo main sam je ładuje).

slowapi liczy żądania per adres IP — za Caddy wszystkie przychodzą z jednego
IP (Caddy), więc limit jest globalny; dla aplikacji jednoosobowej to zaleta.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
