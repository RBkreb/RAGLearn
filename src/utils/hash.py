"""Hash computation utilities."""

import hashlib


def compute_hash(text: str, algorithm: str = "sha256") -> str:
    """Compute hash of a string.

    Args:
        text: The input string to hash.
        algorithm: Hash algorithm to use (default: sha256).
                   Supported: md5, sha1, sha256, sha512.

    Returns:
        Hexadecimal string representation of the hash.

    Raises:
        ValueError: When algorithm is not supported.
    """
    if algorithm not in ("md5", "sha1", "sha256", "sha512"):
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    hasher = hashlib.new(algorithm)
    hasher.update(text.encode("utf-8"))
    return hasher.hexdigest()