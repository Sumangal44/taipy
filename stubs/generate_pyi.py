# Copyright 2023 Avaiga Private Limited
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
# an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.

import ast
import re
from pathlib import Path
from typing import List

__FCT_WHITELIST = ["data_nodes", "tasks", "pipelines", "scenarios", "job_config"]


def _get_function_delimiters(initial_line, lines):
    begin = end = initial_line
    while True:
        if lines[begin - 1] == "\n":
            break
        begin -= 1

    if lines[end].endswith("(\n"):
        while ":\n" not in lines[end]:
            end += 1

    if '"""' in lines[end + 1]:
        while True:
            if '"""\n' in lines[end]:
                break
            end += 1
    return begin, end + 1


def _get_file_lines(filename: str) -> List[str]:
    # Get file lines for later
    with open(filename) as f:
        return f.readlines()


def _get_file_ast(filename: str):
    # Get raw text and build ast
    _config = Path(filename)
    _tree = _config.read_text()
    return ast.parse(_tree)


def _build_base_config_pyi(filename, base_pyi):
    lines = _get_file_lines(filename)
    tree = _get_file_ast(filename)

    class_lineno = [f.lineno for f in ast.walk(tree) if isinstance(f, ast.ClassDef) and f.name == "Config"]
    begin_class, end_class = _get_function_delimiters(class_lineno[0] - 1, lines)

    base_pyi += "".join(lines[begin_class:end_class])
    functions = [f.lineno for f in ast.walk(tree) if isinstance(f, ast.FunctionDef) and not f.name.startswith("__")]

    for ln in functions:
        begin_line, end_line = _get_function_delimiters(ln - 1, lines)
        base_pyi += "".join(lines[begin_line:end_line])

        base_pyi = __add_docstring(base_pyi, lines, end_line)
        base_pyi += "\n"

    return base_pyi


def __add_docstring(base_pyi, lines, end_line):
    if '"""' not in lines[end_line - 1]:
        base_pyi += '\t\t""""""\n'.replace("\t", "    ")
    return base_pyi


def _build_entity_config_pyi(base_pyi, filename, entity_map):
    lines = _get_file_lines(filename)
    tree = _get_file_ast(filename)
    functions = {}

    for f in ast.walk(tree):
        if isinstance(f, ast.FunctionDef):
            if "_configure" in f.name and not f.name.startswith("__") or f.name in __FCT_WHITELIST:
                functions[f.name] = f.lineno

    for k, v in functions.items():
        begin_line, end_line = _get_function_delimiters(v - 1, lines)
        try:
            func = "".join(lines[begin_line:end_line])
            func = func if not k.startswith("_") else func.replace(k, entity_map.get(k))
            func = __add_docstring(func, lines, end_line) + "\n"
            base_pyi += func
        except Exception:
            print(f"key={k}")
            raise

    return base_pyi


def _generate_entity_map(filename):
    entities_map = {}
    entity_tree = _get_file_ast(filename)
    functions = [
        f for f in ast.walk(entity_tree) if isinstance(f, ast.Call) and getattr(f.func, "id", "") == "_inject_section"
    ]

    for f in functions:
        entity = ast.unparse(f.args[0])
        entities_map[entity] = {}
        # Remove class name from function map
        text = ast.unparse(f.args[-1]).replace(f"{entity}.", "")
        matches = re.findall(r"\((.*?)\)", text)

        for m in matches:
            v, k = m.replace("'", "").split(",")
            entities_map[entity][k.strip()] = v
    return entities_map


def _build_header(filename):
    _file = Path(filename)
    return _file.read_text() + "\n\n"


if __name__ == "__main__":
    header_file = "stubs/pyi_header.py"
    config_init = Path("taipy-core/src/taipy/core/config/__init__.py")
    base_config = "src/taipy/config/config.py"

    pipeline_filename = "taipy-core/src/taipy/core/config/pipeline_config.py"
    dn_filename = "taipy-core/src/taipy/core/config/data_node_config.py"
    job_filename = "taipy-core/src/taipy/core/config/job_config.py"
    scenario_filename = "taipy-core/src/taipy/core/config/scenario_config.py"
    task_filename = "taipy-core/src/taipy/core/config/task_config.py"

    entities_map = _generate_entity_map(config_init)
    pyi = _build_header(header_file)
    pyi = _build_base_config_pyi(base_config, pyi)
    pyi = _build_entity_config_pyi(pyi, scenario_filename, entities_map["ScenarioConfig"])
    pyi = _build_entity_config_pyi(pyi, pipeline_filename, entities_map["PipelineConfig"])
    pyi = _build_entity_config_pyi(pyi, dn_filename, entities_map["DataNodeConfig"])
    pyi = _build_entity_config_pyi(pyi, task_filename, entities_map["TaskConfig"])
    pyi = _build_entity_config_pyi(pyi, job_filename, entities_map["JobConfig"])

    with open("src/taipy/config/config.pyi", "w") as f:
        f.writelines(pyi)
