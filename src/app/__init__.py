"""Package initializer for app.

This aliasing layer ensures that modules loaded under `src.app` and `app`
resolve to the same module objects when the repository is imported from
both package styles.
"""

import sys

if "src.app" in sys.modules:
    sys.modules["app"] = sys.modules["src.app"]
    for name, module in list(sys.modules.items()):
        if name.startswith("src.app."):
            alias = "app" + name[3:]
            sys.modules.setdefault(alias, module)
else:
    # If src.app is imported later, the aliasing logic will be applied there.
    pass
