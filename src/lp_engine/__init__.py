__version__ = "0.7.0"

# Issue #129 runtime adapter keeps legacy Issue #111 source-binding cardinality
# audits separate from authored Media Narrative reuses while preserving all
# rights/evidence data attributes. Import for its deterministic installation
# side effect before production submodules render.
from .premium_perception_runtime import install_runtime_adapter as _install_issue129_runtime_adapter

_install_issue129_runtime_adapter()
del _install_issue129_runtime_adapter

# Issue #132 wraps the accepted Issue #129 pixel layer and structurally
# re-authors only the six continuation variants RETURNed by Aoi Issue #131.
# The three PASS continuation variants remain byte-identical at owner HTML.
from .premium_perception_reauthorship_runtime import install_runtime_adapter as _install_issue132_runtime_adapter

_install_issue132_runtime_adapter()
del _install_issue132_runtime_adapter
