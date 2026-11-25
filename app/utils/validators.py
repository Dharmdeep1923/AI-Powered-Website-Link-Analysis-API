import asyncio
import ipaddress
import socket
from urllib.parse import urlsplit

import httpx


class WebsiteError(Exception):
    pass


async def public_target(url: str) -> tuple[httpx.URL, str, str]:
    try:
        parsed = urlsplit(url)
        port = parsed.port
        host = parsed.hostname
        if (
            parsed.scheme not in {"http", "https"}
            or not host
            or parsed.username is not None
            or port not in {None, 443 if parsed.scheme == "https" else 80}
            or "%" in host
        ):
            raise WebsiteError("Use a public HTTP or HTTPS URL on its default port.")

        records = await asyncio.get_running_loop().getaddrinfo(
            host, port or (443 if parsed.scheme == "https" else 80),
            type=socket.SOCK_STREAM,
        )
        addresses = [ipaddress.ip_address(record[4][0]) for record in records]
        if not addresses or any(
            not address.is_global
            or address.is_multicast
            or (isinstance(address, ipaddress.IPv6Address) and (
                address not in ipaddress.ip_network("2000::/3") or address.sixtofour
            ))
            for address in addresses
        ):
            raise WebsiteError("The website must resolve only to public addresses.")

        target = httpx.URL(url).copy_with(host=str(addresses[0]), fragment=None)
        return target, parsed.netloc, host
    except (ValueError, OSError, httpx.InvalidURL) as exc:
        raise WebsiteError("The website address could not be resolved.") from exc
