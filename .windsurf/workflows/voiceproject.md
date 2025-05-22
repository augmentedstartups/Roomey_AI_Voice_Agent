---
description: Rules for this project
---

    async with openai.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="coral",
        input=input,
        instructions=instructions,
        response_format="pcm",
    ) as response:
        await LocalAudioPlayer().play(response)

Do not change this

Make only minimal changes to get the functions to work

it must work via main.py with streaming output. 

Any API keys can be found in .env

