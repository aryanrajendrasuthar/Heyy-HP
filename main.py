"""HP Assistant — application entrypoint."""

from __future__ import annotations

import logging
import sys

from app.assistant.machine import AssistantStateMachine
from app.config.settings import AppSettings
from app.ui import HPMainWindow, HPTray, create_app
from app.ui.app import create_app
from app.ui.main_window import HPMainWindow
from app.ui.tray import HPTray
from app.ui.voice_bridge import VoiceBridge

from app.utils.logging import setup_logging
from app.voice.runtime import VoiceRuntime

logger = logging.getLogger(__name__)


def main() -> int:
    settings = AppSettings()
    setup_logging(settings)
    logger.info("HP assistant starting (version 0.1.0, debug=%s)", settings.debug)

    app = create_app(settings)

    window = HPMainWindow(settings)
    tray = HPTray(window)

    bridge.state_changed.connect(window.set_state)
    bridge.transcript_ready.connect(window.set_transcript)
    bridge.response_ready.connect(window.set_response)

    runtime = VoiceRuntime(
        settings,
        state_machine,
        on_transcript=bridge.transcript_ready.emit,
        on_response=bridge.response_ready.emit,
    )

    tray.show()
    window.show()
    runtime.start()
    logger.info("HP ready")
    return app.exec()

    result = app.exec()
    runtime.stop()
    return result


if __name__ == "__main__":
    sys.exit(main())
