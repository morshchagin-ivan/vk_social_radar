"""Same-origin local web policy, not application authentication."""
from urllib.parse import urlsplit

from starlette.responses import JSONResponse, PlainTextResponse


def authority(value, scheme):
    try:
        if not value or value.endswith(':') or any(c.isspace() for c in value) or any(c in value for c in '/\\@?#%'):
            return None
        parsed = urlsplit(f'{scheme}://{value}')
        if parsed.hostname not in {'127.0.0.1','localhost','::1'}:
            return None
        port = parsed.port
        if port == 0: return None
        return parsed.hostname, port or (443 if scheme == 'https' else 80)
    except ValueError:
        return None


class LocalAccessMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        headers = scope.get('headers', [])
        hosts = [v.decode('latin1') for k,v in headers if k.lower() == b'host']
        origins = [v.decode('latin1') for k,v in headers if k.lower() == b'origin']
        host = authority(hosts[0], scope['scheme']) if len(hosts) == 1 else None
        if host is None:
            return await JSONResponse({'detail':'Local Host required'}, status_code=400)(scope, receive, send)
        blocked = len(origins) > 1
        if origins:
            try:
                origin = urlsplit(origins[0])
                blocked |= (any(c in origins[0] for c in '?\\#') or origin.scheme != scope['scheme'] or origin.path != '' or bool(origin.query or origin.fragment) or
                            authority(origin.netloc, origin.scheme) != host)
            except ValueError:
                blocked = True
        blocked |= any(k.lower() == b'sec-fetch-site' and v.lower() == b'cross-site' for k,v in headers)
        if blocked:
            return await JSONResponse({'detail':'Same-origin request required'}, status_code=403)(scope, receive, send)
        started = False
        async def safe_send(message):
            nonlocal started
            if message['type'] == 'http.response.start':
                started = True
                message.setdefault('headers', []).extend([(b'x-content-type-options',b'nosniff'),(b'referrer-policy',b'no-referrer')])
            await send(message)
        try:
            await self.app(scope, receive, safe_send)
        except Exception:
            # Suppress raw exception propagation to ordinary server error logging.
            if not started:
                await PlainTextResponse('Internal Server Error', status_code=500)(scope, receive, safe_send)
