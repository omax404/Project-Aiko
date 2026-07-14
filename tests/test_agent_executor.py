import pytest
from core.infrastructure.tools.executor import AgentExecutor, AgentAction

def test_parse_actions():
    executor = AgentExecutor()

    # Test empty text
    assert executor.parse_actions("") == []

    # Test BIO_REGISTER
    actions = executor.parse_actions("[BIO_REGISTER]")
    assert len(actions) == 1
    assert actions[0].tool_name == "BIO_REGISTER"

    # Test RUN_PYTHON
    actions = executor.parse_actions("[RUN_PYTHON: print('test')]")
    assert len(actions) == 1
    assert actions[0].tool_name == "RUN_PYTHON"
    assert actions[0].args["code"] == "print('test')"

    # Test SCAN and CAMERA
    actions = executor.parse_actions("[SCAN] [CAMERA]")
    assert len(actions) == 2
    assert actions[0].tool_name == "SCAN"
    assert actions[1].tool_name == "CAMERA"

    # Test IMAGE and LATEX
    actions = executor.parse_actions("[IMAGE: a beautiful sunset] [LATEX: e=mc^2]")
    assert len(actions) == 2
    assert actions[0].tool_name == "IMAGE"
    assert actions[0].args["prompt"] == "a beautiful sunset"
    assert actions[1].tool_name == "LATEX"
    assert actions[1].args["code"] == "e=mc^2"

    # Test CLICK, TYPE, PRESS, OPEN
    text = "[CLICK: 500,600] [TYPE: Aiko] [PRESS: enter] [OPEN: calc.exe]"
    actions = executor.parse_actions(text)
    assert len(actions) == 4
    assert actions[0].tool_name == "CLICK"
    assert actions[0].args["target"] == "500,600"
    assert actions[1].tool_name == "TYPE"
    assert actions[1].args["content"] == "Aiko"
    assert actions[2].tool_name == "PRESS"
    assert actions[2].args["key"] == "enter"
    assert actions[3].tool_name == "OPEN"
    assert actions[3].args["target"] == "calc.exe"

    # Test MCP
    actions = executor.parse_actions("[MCP: read_file | C:\\path\\to\\file.txt]")
    assert len(actions) == 1
    assert actions[0].tool_name == "MCP"
    assert actions[0].args["tool"] == "read_file"
    assert actions[0].args["arg_str"] == "C:\\path\\to\\file.txt"

    # Test RECALL
    actions = executor.parse_actions("[RECALL: yesterday's task | general]")
    assert len(actions) == 1
    assert actions[0].tool_name == "RECALL"
    assert actions[0].args["query"] == "yesterday's task"
    assert actions[0].args["room"] == "general"
