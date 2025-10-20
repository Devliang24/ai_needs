"""Generate XMind files from session results."""

from __future__ import annotations

import json
import time
import uuid
from io import BytesIO
from typing import Any, Dict, List
from zipfile import ZipFile, ZIP_DEFLATED


def _coerce_step_text(item: Any) -> str:
    if item is None:
        return ""
    if isinstance(item, str):
        return item.strip()
    if isinstance(item, dict):
        for key in ("text", "desc", "description", "action", "step", "content", "title"):
            val = item.get(key)
            if isinstance(val, str):
                return val.strip()
        try:
            return " ".join(str(v).strip() for v in item.values() if v is not None)
        except Exception:
            return str(item)
    return str(item).strip()


def _format_steps(steps: Any) -> str:
    """Format steps with numbering if it's a list with multiple items."""
    if steps is None:
        return ""
    if isinstance(steps, (list, tuple, set)):
        steps_list = list(steps)
        if len(steps_list) == 0:
            return ""
        if len(steps_list) == 1:
            return _coerce_step_text(steps_list[0])
        return "; ".join(f"{i+1}. {_coerce_step_text(x)}" for i, x in enumerate(steps_list))
    return _coerce_step_text(steps)


def _format_field_with_numbering(field: Any) -> str:
    """Format field (preconditions) with numbering if it's a list."""
    if field is None:
        return ""
    if isinstance(field, (list, tuple)):
        field_list = list(field)
        if len(field_list) == 0:
            return ""
        if len(field_list) == 1:
            return _coerce_step_text(field_list[0])
        return "; ".join(f"{i+1}. {_coerce_step_text(x)}" for i, x in enumerate(field_list))
    return _coerce_step_text(field)


def _get_priority_icon(priority: str) -> str:
    """Map priority level to icon."""
    priority_map = {
        "P0": "①",
        "P1": "②",
        "P2": "③",
        "P3": "④",
    }
    return priority_map.get(priority, "")


def _build_content_tree(session_title: str, result: Dict[str, Any]) -> Dict[str, Any]:
    modules: List[Dict[str, Any]] = result.get("modules", [])

    def _topic(topic_id: str, title: str, children: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
        data = {
            "id": topic_id,
            "class": "topic",
            "title": title,
        }
        if children:
            data["children"] = {"attached": children}
        return data

    attached_modules = []
    for module in modules:
        module_id = str(uuid.uuid4())
        case_children = []
        for case in module.get("cases", []):
            case_id = str(uuid.uuid4())

            # 构建用例标题，包含优先级图标
            priority = case.get("priority", "")
            priority_icon = _get_priority_icon(priority)
            case_title = f"{case.get('id', 'TC')}: {case.get('title', '')}"
            if priority_icon:
                case_title = f"{case_title} {priority_icon}"

            # 前置条件放在备注中
            preconditions_text = _format_field_with_numbering(case.get('preconditions', ''))
            notes = f"前置条件: {preconditions_text}" if preconditions_text else ""

            # 构建操作步骤子节点
            steps_children = []
            steps = case.get("steps", [])
            if steps:
                if isinstance(steps, (list, tuple)):
                    for i, step in enumerate(steps):
                        steps_children.append({
                            "id": str(uuid.uuid4()),
                            "class": "topic",
                            "title": f"{i+1}. {_coerce_step_text(step)}"
                        })
                else:
                    steps_children.append({
                        "id": str(uuid.uuid4()),
                        "class": "topic",
                        "title": f"1. {_coerce_step_text(steps)}"
                    })

            # 构建预期结果子节点
            expected_children = []
            expected = case.get("expected", [])
            if expected:
                if isinstance(expected, (list, tuple)):
                    for i, exp in enumerate(expected):
                        expected_children.append({
                            "id": str(uuid.uuid4()),
                            "class": "topic",
                            "title": f"{i+1}. {_coerce_step_text(exp)}"
                        })
                else:
                    expected_children.append({
                        "id": str(uuid.uuid4()),
                        "class": "topic",
                        "title": f"1. {_coerce_step_text(expected)}"
                    })

            # 构建用例的子节点列表
            case_sub_children = []
            if steps_children:
                case_sub_children.append(_topic(str(uuid.uuid4()), "操作步骤", steps_children))
            if expected_children:
                case_sub_children.append(_topic(str(uuid.uuid4()), "预期结果", expected_children))

            # 创建用例节点
            case_node = {
                "id": case_id,
                "class": "topic",
                "title": case_title,
            }
            if notes:
                case_node["notes"] = {"plain": {"content": notes}}
            if case_sub_children:
                case_node["children"] = {"attached": case_sub_children}

            case_children.append(case_node)

        attached_modules.append(_topic(module_id, module.get("name", "模块"), case_children))

    root_topic = _topic(str(uuid.uuid4()), session_title, attached_modules)
    # Add structureClass to root topic
    root_topic["structureClass"] = "org.xmind.ui.map.unbalanced"

    return {
        "id": str(uuid.uuid4()),
        "class": "sheet",
        "title": session_title,
        "rootTopic": root_topic,
        "topicPositioning": "fixed",
    }


def generate_xmind_bytes(session_id: str, test_cases: Dict[str, Any]) -> bytes:
    """Create an XMind file content as bytes."""

    timestamp = int(time.time() * 1000)
    workbook = [_build_content_tree(f"Session {session_id}", test_cases)]

    metadata = {
        "creator": "智能分析平台",
        "created": timestamp,
        "modified": timestamp,
    }

    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as xmind_zip:
        xmind_zip.writestr("content.json", json.dumps(workbook, ensure_ascii=False))
        xmind_zip.writestr("metadata.json", json.dumps(metadata))
        manifest = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>"
            "<manifest xmlns=\"urn:xmind:xmap:xmlns:manifest:1.0\">"
            "<file-entry full-path=\"content.json\" media-type=\"application/vnd.xmind.content+xml\"/>"
            "<file-entry full-path=\"metadata.json\" media-type=\"application/vnd.xmind.metadata+xml\"/>"
            "</manifest>"
        )
        xmind_zip.writestr("META-INF/manifest.xml", manifest)

    return buffer.getvalue()
