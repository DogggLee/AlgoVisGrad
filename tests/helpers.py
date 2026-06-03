from __future__ import annotations

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import Iterator, Type


@contextmanager
def run_test_server(
    handler_cls: Type[BaseHTTPRequestHandler],
) -> Iterator[ThreadingHTTPServer]:
    """Run a temporary local HTTP server for integration-style tests.

    Args:
        handler_cls: HTTP request handler class used by the temporary server.

    Yields:
        Running ThreadingHTTPServer bound to a free local port.
    """
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
