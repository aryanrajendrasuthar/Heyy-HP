"""HP Assistant — application entry point."""

from __future__ import annotations

import sys


def main() -> int:
    from app.assistant.dispatcher import CommandDispatcher
    from app.assistant.machine import AssistantStateMachine
    from app.config.settings import AppSettings
    from app.llm.conversation import ConversationBuffer
    from app.llm.factory import get_provider
    from app.memory.db import get_connection
    from app.memory.history import ConversationHistory
    from app.memory.routines import RoutineRepository
    from app.ui.app import create_app
    from app.ui.main_window import HPMainWindow
    from app.ui.tray import HPTray
    from app.ui.voice_bridge import VoiceBridge
    from app.utils.logging import setup_logging
    from app.vision.pipeline import VisionPipeline
    from app.voice.runtime import VoiceRuntime

    settings = AppSettings()
    setup_logging(settings)

    db = get_connection(settings)
    history = ConversationHistory(db)
    routines = RoutineRepository(db)
    vision = VisionPipeline(settings)

    app = create_app(settings)
    state_machine = AssistantStateMachine(settings)
    bridge = VoiceBridge()
    dispatcher = CommandDispatcher(vision=vision, routines=routines)
    llm = get_provider(settings)
    conv = ConversationBuffer(max_turns=settings.llm_max_history)

    state_machine.add_state_callback(bridge.state_changed.emit)

    window = HPMainWindow(settings)
    tray = HPTray(window)

    bridge.state_changed.connect(window.set_state)
    bridge.transcript_ready.connect(window.set_transcript)
    bridge.response_ready.connect(window.set_response)

    def _on_transcript(text: str) -> None:
        bridge.transcript_ready.emit(text)
        history.save("user", text)

    def _on_response(text: str) -> None:
        bridge.response_ready.emit(text)
        history.save("assistant", text)

    runtime = VoiceRuntime(
        settings,
        state_machine,
        on_transcript=_on_transcript,
        on_response=_on_response,
        on_command=dispatcher.dispatch,
        llm=llm,
        conversation=conv,
    )

    tray.show()
    window.show()
    runtime.start()

    result = app.exec()
    runtime.stop()
    db.close()
    return result


if __name__ == "__main__":
    sys.exit(main())
