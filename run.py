import sys
import asyncio
import nest_asyncio

# Para Windows, forzamos a usar la política del Selector en vez del Proactor.
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Aplica nest_asyncio para que sea posible reentrar en el event loop.
nest_asyncio.apply()

from bot_telegramv2 import main

# Ejecuta la función main() de forma asíncrona.
asyncio.run(main())
