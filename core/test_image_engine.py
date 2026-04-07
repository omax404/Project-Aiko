import asyncio
import sys
import os
# Add project root to PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.image_engine import ImageEngine

async def main():
    engine = ImageEngine()
    filename = await engine.generate_image('a futuristic cyberpunk city')
    print('Generated image filename:', filename)

if __name__ == '__main__':
    asyncio.run(main())
