import subprocess
from audio.recorder import record_until_silence
from audio.player import play_audio
from stt import transcribe
from llm import Brain
from tts import speak
from intent_router import route

brain = Brain()


def main():
    print()
    print("╔══════════════════════════════════════╗")
    print("║          M I C K E Y                 ║")
    print("║    Local AI Assistant — Terminal      ║")
    print("╚══════════════════════════════════════╝")
    print()
    print("  Press Enter to speak, type text, or 'q' to quit.")
    print()

    while True:
        user_input = input("\n[Enter=voice | type text | q=quit]: ").strip()

        if user_input.lower() == "q":
            print("\nMICKEY signing off. 👋")
            break
        elif user_input == "":
            audio_path = record_until_silence()
            user_text = transcribe(audio_path)
            if not user_text or user_text.startswith("["):
                print(f"  ⚠  Could not understand: {user_text}")
                continue
            print(f"  You said: {user_text}")
        else:
            user_text = user_input

        print("  🧠 Thinking...")
        llm_response = brain.think(user_text)
        result = route(llm_response)

        if result["type"] == "action_result":
            print(f"  ⚡ [ACTION] {result['result']}")
            summary = brain.think(
                f"Action result: {result['result']}. Tell the user what happened in one sentence."
            )
            print(f"  MICKEY: {summary}")
            audio = speak(summary)
        elif result["type"] == "error":
            print(f"  ❌ Error: {result['result']}")
            continue
        else:
            print(f"  MICKEY: {result['result']}")
            audio = speak(result["result"])

        play_audio(audio)


if __name__ == "__main__":
    main()
