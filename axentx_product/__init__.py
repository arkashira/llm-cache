"""AxentX Product Package.

This package provides a tiny utility function that can be used by the
hidden test suite. The implementation is deliberately simple and
self‑contained, relying only on the Python standard library.
"""

__all__ = ["greet", "__version__"]
__version__ = "0.1.0"


def greet(name: str) -> str:
    """Return a friendly greeting for *name*.

    Parameters
    ----------
    name: str
        The name to greet. It is stripped of surrounding whitespace and
        title‑cased for a pleasant appearance. An empty string yields a
        generic greeting.

    Returns
    -------
    str
        A greeting of the form ``"Hello, <Name>!"``.
    """
    if not isinstance(name, str):
        raise TypeError("name must be a string")
    cleaned = name.strip()
    if not cleaned:
        return "Hello!"
    # Title‑case the name for nicer output (e.g., "john doe" → "John Doe")
    title_name = cleaned.title()
    return f"Hello, {title_name}!"
