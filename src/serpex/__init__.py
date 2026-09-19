"""
Serpex Python SDK.

`pip install serpex` installs this package; import it as `serpex`:

    from serpex import SerpexClient

The implementation lives in `serpex_sdk`, which stays importable for existing
code (`from serpex_sdk import SerpexClient` keeps working).
"""

from serpex_sdk import *  # noqa: F401,F403
from serpex_sdk import __all__, __version__  # noqa: F401
