"""HTTP header builder for constructing request headers"""

from typing import Dict, Optional

from src.server.base.constants import AuthScheme, ContentType, HTTPHeader


class HTTPHeaderBuilder:
    """
    Builder Pattern for constructing HTTP headers

    Single Responsibility: Only builds HTTP headers
    Uses Enumerator Pattern for all header names and values
    """

    @staticmethod
    def build_headers(
        auth_token: Optional[str] = None,
        content_type: str = ContentType.JSON.value
    ) -> Dict[str, str]:
        """
        Build HTTP headers with optional authentication

        Args:
            auth_token: Optional bearer token for authentication
            content_type: Content type (default: application/json)

        Returns:
            Dictionary of HTTP headers
        """
        headers = {HTTPHeader.CONTENT_TYPE.value: content_type}

        if auth_token:
            headers[HTTPHeader.AUTHORIZATION.value] = (
                f"{AuthScheme.BEARER.value} {auth_token}"
            )

        return headers
