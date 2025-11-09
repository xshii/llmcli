"""
数据验证工具
"""

from typing import Any, Dict, List, Optional

from aicode.config.constants import MAX_SCORE, MIN_SCORE, SPECIALTIES
from aicode.llm.exceptions import ValidationError


def validate_model_name(name: Any) -> str:
    """验证模型名称"""
    if not name:
        raise ValidationError("Model name is required")

    if not isinstance(name, str):
        raise ValidationError("Model name must be a string")

    name = name.strip()
    if not name:
        raise ValidationError("Model name cannot be empty")

    if len(name) > 255:
        raise ValidationError("Model name too long (max 255 characters)")

    return name


def validate_provider(provider: Any) -> str:
    """验证提供商名称"""
    if not provider:
        raise ValidationError("Provider is required")

    if not isinstance(provider, str):
        raise ValidationError("Provider must be a string")

    provider = provider.strip()
    if not provider:
        raise ValidationError("Provider cannot be empty")

    if len(provider) > 255:
        raise ValidationError("Provider name too long (max 255 characters)")

    return provider


def validate_token_count(value: Any, field_name: str) -> Optional[int]:
    """验证 token 数量"""
    if value is None:
        return None

    if not isinstance(value, int):
        raise ValidationError(f"{field_name} must be an integer")

    if value <= 0:
        raise ValidationError(f"{field_name} must be positive")

    if value > 10_000_000:
        raise ValidationError(f"{field_name} too large (max 10M)")

    return value


def validate_score(value: Any, field_name: str) -> Optional[float]:
    """验证评分"""
    if value is None:
        return None

    if not isinstance(value, (int, float)):
        raise ValidationError(f"{field_name} must be a number")

    value = float(value)

    if not (MIN_SCORE <= value <= MAX_SCORE):
        raise ValidationError(
            f"{field_name} must be between {MIN_SCORE} and {MAX_SCORE}"
        )

    return value


def validate_cost(value: Any, field_name: str) -> Optional[float]:
    """验证成本"""
    if value is None:
        return None

    if not isinstance(value, (int, float)):
        raise ValidationError(f"{field_name} must be a number")

    value = float(value)

    if value < 0:
        raise ValidationError(f"{field_name} cannot be negative")

    if value > 1000:
        raise ValidationError(f"{field_name} too large (max 1000)")

    return value


def validate_specialties(value: Any) -> Optional[List[str]]:
    """验证专长列表"""
    if value is None:
        return None

    if isinstance(value, str):
        # 如果是字符串，尝试分割
        value = [s.strip() for s in value.split(",") if s.strip()]

    if not isinstance(value, list):
        raise ValidationError("Specialties must be a list or comma-separated string")

    if not value:
        return None

    validated = []
    for item in value:
        if not isinstance(item, str):
            raise ValidationError("Each specialty must be a string")

        item = item.strip().lower()
        if not item:
            continue

        if item not in SPECIALTIES:
            raise ValidationError(
                f"Invalid specialty '{item}'. Must be one of: {', '.join(SPECIALTIES)}"
            )

        if item not in validated:
            validated.append(item)

    return validated if validated else None


def validate_url(value: Any, field_name: str) -> Optional[str]:
    """验证URL"""
    if value is None:
        return None

    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string")

    value = value.strip()
    if not value:
        return None

    if not value.startswith(("http://", "https://")):
        raise ValidationError(f"{field_name} must start with http:// or https://")

    if len(value) > 2048:
        raise ValidationError(f"{field_name} too long (max 2048 characters)")

    return value


def validate_string(
    value: Any, field_name: str, max_length: int = 1000
) -> Optional[str]:
    """验证字符串字段"""
    if value is None:
        return None

    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string")

    value = value.strip()
    if not value:
        return None

    if len(value) > max_length:
        raise ValidationError(f"{field_name} too long (max {max_length} characters)")

    return value


def validate_model_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    验证完整的模型数据
    返回验证后的数据字典
    """
    validated = {}

    # 必需字段
    validated["name"] = validate_model_name(data.get("name"))
    validated["provider"] = validate_provider(data.get("provider"))

    # 可选字段
    validated["api_key"] = validate_string(data.get("api_key"), "api_key", 500)
    validated["api_url"] = validate_url(data.get("api_url"), "api_url")

    # Token字段
    validated["max_input_tokens"] = validate_token_count(
        data.get("max_input_tokens"), "max_input_tokens"
    )
    validated["max_output_tokens"] = validate_token_count(
        data.get("max_output_tokens"), "max_output_tokens"
    )
    validated["context_window"] = validate_token_count(
        data.get("context_window"), "context_window"
    )

    # 评分字段
    validated["code_score"] = validate_score(data.get("code_score"), "code_score")
    validated["reasoning_score"] = validate_score(
        data.get("reasoning_score"), "reasoning_score"
    )
    validated["speed_score"] = validate_score(data.get("speed_score"), "speed_score")

    # 成本字段
    validated["cost_per_1k_input"] = validate_cost(
        data.get("cost_per_1k_input"), "cost_per_1k_input"
    )
    validated["cost_per_1k_output"] = validate_cost(
        data.get("cost_per_1k_output"), "cost_per_1k_output"
    )

    # 专长和备注
    validated["specialties"] = validate_specialties(data.get("specialties"))
    validated["notes"] = validate_string(data.get("notes"), "notes", 2000)

    return validated
