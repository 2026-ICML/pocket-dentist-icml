"""
Core JSON answer-extraction shared by all MetaDent tasks.

Verbatim logic from the research harness (``src/models/base_model.py``).
Evaluated VLMs are prompted to emit JSON; their raw text is coerced to JSON
with ``json_repair`` (tolerating ```json fences and minor malformations).
A response that cannot be coerced to the expected type is treated as a
*format-collapse* failure and scored as wrong — this is exactly how the
"output reliability" results in the paper are produced.
"""

import json
from typing import TypeVar

JSON_T = dict | list
JSON_T_VAR = TypeVar("JSON_T_VAR", bound=JSON_T)


def parse_json(json_str: str, ret_t: type[JSON_T_VAR] = dict) -> JSON_T_VAR:
    """Coerce a model's raw text response into ``ret_t`` (``dict`` or ``list``).

    Raises ``ValueError`` if the text cannot be repaired into valid JSON, and
    ``AssertionError`` if the parsed value is not of the expected type.
    """
    from json_repair import repair_json

    if json_str.startswith("```json") and json_str.endswith("```"):
        json_str = json_str[7:-3].strip()

    try:
        json_str = repair_json(json_str, ensure_ascii=False)
        res_json = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON response: {json_str}") from e

    assert isinstance(res_json, ret_t), f"Expected type {ret_t}, but got {type(res_json)}"
    return res_json
