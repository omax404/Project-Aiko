import asyncio
import edge_tts

async def synthesize(text, output_file):
    communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
    await communicate.save(output_file)

asyncio.run(synthesize("Hello world", "test.mp3"))
