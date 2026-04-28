"""Open URLs and perform web searches in the default browser."""

from __future__ import annotations

import logging
import re
import urllib.parse
import urllib.request
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
        """Search YouTube and open the top matching video directly."""
        try:
            search_url = (
                "https://www.youtube.com/results?search_query="
                + urllib.parse.quote_plus(query)
            )
            req = urllib.request.Request(
                search_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="replace")
            ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
            if ids:
                video_url = f"https://www.youtube.com/watch?v={ids[0]}"
                logger.info("YouTube play: %s -> %s", query, video_url)
                return self.open_url(video_url)
        except Exception:
            logger.exception("YouTube video lookup failed, falling back to search page")
        # Fallback: open search results page
        url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(query)
        return self.open_url(url)
