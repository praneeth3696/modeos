"""
ModeOS Data Models and Configuration Schemas
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

@dataclass
class ModeConfig:
    name: str
    description: str = ""
    brightness: Optional[int] = None
    volume: Optional[int] = None
    night_light: Optional[bool] = None
    cpu_limit: Optional[int] = None
    kill_all_except_allow: bool = False
    allow_apps: List[str] = field(default_factory=list)
    block_apps: List[str] = field(default_factory=list)
    allow_categories: List[str] = field(default_factory=list)
    block_categories: List[str] = field(default_factory=list)
    boost_apps: Dict[str, int] = field(default_factory=dict)
    reduce_apps: Dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> 'ModeConfig':
        if not isinstance(data, dict):
            raise ValueError(f"Mode configuration for '{name}' must be a mapping/dictionary")

        brightness = data.get("brightness")
        if brightness is not None:
            try:
                brightness = max(0, min(100, int(brightness)))
            except (ValueError, TypeError):
                brightness = None

        volume = data.get("volume")
        if volume is not None:
            try:
                volume = max(0, min(100, int(volume)))
            except (ValueError, TypeError):
                volume = None

        night_light = data.get("night_light")
        if night_light is not None:
            night_light = bool(night_light)

        cpu_limit = data.get("cpu_limit")
        if cpu_limit is not None:
            try:
                cpu_limit = max(1, min(100, int(cpu_limit)))
            except (ValueError, TypeError):
                cpu_limit = None

        kill_all = bool(data.get("kill_all_except_allow", False))
        allow_apps = [str(x).strip() for x in (data.get("allow_apps") or []) if x]
        block_apps = [str(x).strip() for x in (data.get("block_apps") or []) if x]
        allow_cats = [str(x).strip() for x in (data.get("allow_categories") or []) if x]
        block_cats = [str(x).strip() for x in (data.get("block_categories") or []) if x]

        def _clean_priorities(p_dict):
            out = {}
            if isinstance(p_dict, dict):
                for k, v in p_dict.items():
                    if k is not None and v is not None:
                        try:
                            val = int(v)
                            # clamp to valid Linux nice range [-20, 19]
                            out[str(k).strip().lower()] = max(-20, min(19, val))
                        except (ValueError, TypeError):
                            pass
            return out

        boost_apps = _clean_priorities(data.get("boost_apps"))
        reduce_apps = _clean_priorities(data.get("reduce_apps"))
        desc = str(data.get("description", "")).strip()

        return cls(
            name=name,
            description=desc,
            brightness=brightness,
            volume=volume,
            night_light=night_light,
            cpu_limit=cpu_limit,
            kill_all_except_allow=kill_all,
            allow_apps=allow_apps,
            block_apps=block_apps,
            allow_categories=allow_cats,
            block_categories=block_cats,
            boost_apps=boost_apps,
            reduce_apps=reduce_apps,
        )

    def validate(self) -> List[str]:
        """Validates configuration and returns a list of warnings or issues."""
        warnings = []
        if self.kill_all_except_allow and not self.allow_apps:
            warnings.append(
                f"Mode '{self.name}' enables 'kill_all_except_allow' but 'allow_apps' is empty. "
                "This could terminate all user applications."
            )
        return warnings
