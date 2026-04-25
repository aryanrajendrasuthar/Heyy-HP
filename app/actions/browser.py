"""Open URLs and perform web searches in the default browser."""

from __future__ import annotations

import logging
import urllib.parse
import webbrowser

logger = logging.getLogger(__name__)


class BrowserRouter:
    def open_url(self, url: str) -> bool:
        try:
            webbrowser.open(url)
            logger.info("Opened URL: %s", url)
            return True
        except Exception:
            logger.exception("Failed to open URL %s", url)
            return False

    def google(self, query: str) -> bool:
        url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(query)
        return self.open_url(url)

    def youtube(self, query: str) -> bool:
        url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(query)
        return self.open_url(url)
