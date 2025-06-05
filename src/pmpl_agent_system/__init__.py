"""PMPL エージェントシステム - プロダクトマネージャー・リーダーの課題議論・分析システム"""

__version__ = "0.1.0"
__author__ = "PMPL Agent System"
__email__ = "info@pmpl-agent-system.com"

from .core.system import PMPLAgentSystem
from .config.settings import Settings

__all__ = ["PMPLAgentSystem", "Settings"] 