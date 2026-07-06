import socket
from biedaos.__main__ import free_port


def test_free_port_skips_taken():
    # Port przydzielony przez system zamiast 8137 — test nie może się wywalać,
    # gdy BiedaOS akurat działa obok.
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    taken = s.getsockname()[1]
    try:
        assert free_port(taken) != taken
    finally:
        s.close()


def test_free_port_returns_start_when_free():
    port = free_port(18137)
    assert port == 18137


def test_schedule_browser_is_daemon(monkeypatch):
    import webbrowser
    from biedaos.__main__ import schedule_browser

    monkeypatch.setattr(webbrowser, "open", lambda *a, **k: None)
    t = schedule_browser("http://example.invalid")
    try:
        assert t.daemon is True
    finally:
        t.cancel()
