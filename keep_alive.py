import aiohttp
from aiohttp import web
import asyncio
import logging

logger = logging.getLogger(__name__)

async def handle(request):
    return web.Response(text="Music Bot is Running!")

async def start_web_server():
    """Start a dummy web server to keep Render happy."""
    app = web.Application()
    app.router.add_get('/', handle)
    
    # We need to setup the runner
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Bind to port 10000 (Render default) or 8080
    import os
    port = int(os.environ.get("PORT", 8080))
    
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"Web server started on port {port}")
