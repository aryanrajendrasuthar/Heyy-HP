"""HP Assistant — application entrypoint."""

from __future__ import annotations

import logging
import sys

from app.assistant.machine import AssistantStateMachine
from app.config.settings import AppSettings
<<<<<<< HEAD
from app.ui import HPMainWindow, HPTray, create_app
=======
from app.ui.app import create_app
from app.ui.main_window import HPMainWindow
from app.ui.tray import HPTray
from app.ui.voice_bridge import VoiceBridge
>>>>>>> e82e590 (All of sprint 2)
from app.utils.logging import setup_logging
from app.voice.runtime import VoiceRuntime

logger = logging.getLogger(__name__)


def main() -> int:
    settings = AppSettings()
    setup_logging(settings)
    logger.info("HP assistant starting (version 0.1.0, debug=%s)", settings.debug)

    app = create_app(settings)
<<<<<<< HEAD

    window = HPMainWindow(settings.app_name)
    tray = HPTray(window)
    tray.show()
    window.show()

    logger.info("HP ready")
    return app.exec()
=======
    state_machine = AssistantStateMachine(settings)
    bridge = VoiceBridge()
    state_machine.add_state_callback(bridge.state_changed.emit)

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

    result = app.exec()
    runtime.stop()
    return result
>>>>>>> e82e590 (All of sprint 2)


if __name__ == "__main__":
    sys.exit(main())
