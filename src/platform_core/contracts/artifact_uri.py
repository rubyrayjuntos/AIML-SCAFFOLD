from __future__ import annotations

from urllib.parse import parse_qsl, urlsplit, urlunsplit

APPROVED_ARTIFACT_URI_SCHEMES = frozenset({"azure", "azureml", "https"})
_SAS_PARAMETERS = {"sig", "se", "sp", "sv", "skt", "skoid"}
_CREDENTIAL_PARAMETERS = {
    "access_token",
    "api_key",
    "apikey",
    "client_secret",
    "code",
    "credential",
    "key",
    "password",
    "secret",
    "token",
}


def validate_artifact_uri(value: str) -> str:
    """Return a normalized unsigned artifact URI without exposing rejected values."""

    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ValueError("artifact URI contains control characters")
    parsed = urlsplit(value)
    lowered = value.lower()
    if "defaultendpointsprotocol=" in lowered or "accountkey=" in lowered:
        raise ValueError("artifact URI must not contain a connection string")
    scheme = parsed.scheme.lower()
    if scheme not in APPROVED_ARTIFACT_URI_SCHEMES:
        raise ValueError("artifact URI scheme is not approved")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("artifact URI must not contain user information")
    if parsed.query:
        query_names = {name.lower() for name, _ in parse_qsl(parsed.query, keep_blank_values=True)}
        if query_names & (_SAS_PARAMETERS | _CREDENTIAL_PARAMETERS):
            raise ValueError("artifact URI must not contain credential-bearing parameters")
        raise ValueError("artifact URI must be an unsigned canonical reference")
    if parsed.fragment:
        raise ValueError("artifact URI must not contain a fragment")
    if scheme == "https" and not parsed.hostname:
        raise ValueError("HTTPS artifact URI requires a host")
    if scheme in {"azure", "azureml"} and not (parsed.netloc or parsed.path):
        raise ValueError("artifact URI requires a resource path")
    return urlunsplit((scheme, parsed.netloc, parsed.path, "", ""))
