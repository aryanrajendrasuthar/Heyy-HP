"""HP Assistant — application entry point."""

from __future__ import annotations

import sys


def main() -> int:
    from app.assistant.dispatcher import CommandDispatcher
    from app.assistant.machine import AssistantStateMachine
    from app.config.settings import AppSettings
    from app.llm.conversation import ConversationBuffer
    from app.llm.factory import get_provider
    from app.ui.app import create_app
    from app.ui.main_window import HPMainWindow
    from app.ui.tray import HPTray
    from app.ui.voice_bridge import VoiceBridge
    from app.utils.logging import setup_logging
    from app.voice.runtime import VoiceRuntime

    settings = AppSettings()
    setup_logging(settings)

    app = create_app(settings)
    state_machine = AssistantStateMachine(settings)
    bridge = VoiceBridge()
    dispatcher = CommandDispatcher()
    llm = get_provider(settings)
    conv = ConversationBuffer(max_turns=settings.llm_max_history)

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
        on_command=dispatcher.dispatch,
        llm=llm,
        conversation=conv,
    )

    tray.show()
    window.show()
    runtime.start()

    result = app.exec()
    runtime.stop()
    return result


if __name__ == "__main__":
    sys.exit(main())
