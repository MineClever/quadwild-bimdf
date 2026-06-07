#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import datetime
import contextlib
import json
import os
import re
import shutil
import shlex
import subprocess
import sys
import traceback

QT_BINDING = None
try:
    with open(os.devnull, "w") as _null_stream:
        with contextlib.redirect_stderr(_null_stream):
            from PySide2 import QtCore, QtGui, QtWidgets
            QT_BINDING = "PySide2"
except Exception:
    try:
        from PySide6 import QtCore, QtGui, QtWidgets
        QT_BINDING = "PySide6"
    except Exception:
        print("PySide2 or PySide6 is required to run this UI.")
        raise


PY2 = sys.version_info[0] == 2
if PY2:
    text_type = unicode  # noqa: F821
else:
    text_type = str


def ensure_text(value):
    if value is None:
        return text_type("")
    if isinstance(value, text_type):
        return value
    try:
        return value.decode("utf-8")
    except Exception:
        return text_type(value)


def repo_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def settings_path():
    return os.path.join(repo_root(), "scripts", "quadwild_ui_settings.json")


def read_text_file(path):
    if not path or not os.path.isfile(path):
        return text_type("")
    handle = open(path, "rb")
    try:
        return ensure_text(handle.read())
    finally:
        handle.close()


def write_text_file(path, content):
    handle = open(path, "wb")
    try:
        handle.write(ensure_text(content).encode("utf-8"))
    finally:
        handle.close()


def read_json_file(path, fallback=None):
    if fallback is None:
        fallback = {}
    content = read_text_file(path)
    if not content.strip():
        return dict(fallback)
    try:
        data = json.loads(content)
    except Exception:
        return dict(fallback)
    if isinstance(data, dict):
        result = dict(fallback)
        result.update(data)
        return result
    return dict(fallback)


def write_json_file(path, data):
    write_text_file(path, json.dumps(data, indent=2, ensure_ascii=False, sort_keys=False))


def binary_candidates(filename):
    root = repo_root()
    return [
        os.path.join(root, "build", "windows-clangcl", "Build", "bin", "Release", filename),
        os.path.join(root, "build", "windows-clangcl", "Build", "bin", filename),
        os.path.join(root, "build", "windows-default", "Build", "bin", "Release", filename),
        os.path.join(root, "build", "windows-default", "Build", "bin", filename),
        os.path.join(root, "release", "windows", filename),
    ]


def preferred_repo_binary(filename):
    existing = [path for path in binary_candidates(filename) if os.path.isfile(path)]
    if not existing:
        return text_type("")
    existing.sort(key=lambda path: os.path.getmtime(path), reverse=True)
    return existing[0]


def normalize_binary_path(configured_path, filename):
    configured_path = ensure_text(configured_path).strip()
    root = repo_root()
    preferred = preferred_repo_binary(filename)

    if configured_path:
        normalized = os.path.abspath(configured_path)
        managed_candidates = [os.path.abspath(path) for path in binary_candidates(filename)]
        managed_prefixes = [
            os.path.abspath(os.path.join(root, "release", "windows")),
            os.path.abspath(os.path.join(root, "build", "windows-clangcl")),
            os.path.abspath(os.path.join(root, "build", "windows-default")),
        ]
        under_managed_tree = any(normalized.startswith(prefix + os.sep) or normalized == prefix for prefix in managed_prefixes)
        if os.path.isfile(normalized) and not under_managed_tree:
            return normalized
        if normalized in managed_candidates and preferred:
            return preferred
        if os.path.isfile(normalized):
            return normalized

    return preferred


def default_prep_config():
    return os.path.join(repo_root(), "quadwild", "basic_setup.json")


def default_main_config():
    return os.path.join(repo_root(), "config", "main_config", "flow_noalign_lemon.json")


def default_flow_solver_config():
    return os.path.join(repo_root(), "config", "main_config", "flow_virtual_simple.json")


def default_satsuma_config():
    return os.path.join(repo_root(), "config", "satsuma", "lemon.json")


def default_output_root():
    return os.path.join(repo_root(), "ui_runs")


def safe_makedirs(path):
    if path and not os.path.isdir(path):
        os.makedirs(path)


def split_extra_args(raw_text):
    raw_text = ensure_text(raw_text).strip()
    if not raw_text:
        return []
    try:
        return shlex.split(raw_text)
    except Exception:
        return raw_text.split()


def quote_argument(value):
    value = ensure_text(value)
    if not value:
        return u'""'
    if u" " in value or u"\t" in value or u"\"" in value:
        return u"\"" + value.replace(u"\"", u"\\\"") + u"\""
    return value


def command_to_text(parts):
    return u" ".join([quote_argument(part) for part in parts])


def copy_file_to_directory(source_path, target_directory):
    target_path = os.path.join(target_directory, os.path.basename(source_path))
    shutil.copy2(source_path, target_path)
    return target_path


def copy_sidecars(source_mesh_path, target_directory, extensions, logger):
    source_base = os.path.splitext(source_mesh_path)[0]
    copied = []
    for extension in extensions:
        sidecar_path = source_base + extension
        if os.path.exists(sidecar_path):
            copied.append(copy_file_to_directory(sidecar_path, target_directory))
        else:
            logger(u"[WARN] 缺少辅助文件: {0}".format(sidecar_path))
    return copied


def sanitize_name(value):
    value = ensure_text(value).strip()
    if not value:
        return u"quadwild_job"
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value)
    value = re.sub(r"_+", "_", value)
    value = value.strip("._-")
    return value or u"quadwild_job"


def workflow_label(workflow):
    if workflow == "full_pipeline":
        return "full"
    if workflow == "quadwild_only":
        return "quadwild"
    return "qfp"


def generate_job_name(workflow, input_path):
    input_path = ensure_text(input_path).strip()
    if input_path:
        basename = os.path.basename(input_path)
        stem, ext = os.path.splitext(basename)
        stem = sanitize_name(stem)
        ext = sanitize_name(ext.lstrip("."))
    else:
        stem = "mesh"
        ext = "input"
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return "{0}_{1}_{2}_{3}".format(workflow_label(workflow), stem, ext, stamp)


def parse_number_list_text(raw_text):
    raw_text = ensure_text(raw_text).strip()
    if not raw_text:
        return []
    separators_normalized = raw_text.replace("\n", ",").replace(";", ",")
    parts = [part.strip() for part in separators_normalized.split(",")]
    result = []
    for part in parts:
        if not part:
            continue
        result.append(float(part))
    return result


def number_list_to_text(values):
    if not values:
        return text_type("")
    return u", ".join([ensure_text(value) for value in values])


def deep_copy_json_dict(data):
    return json.loads(json.dumps(data))


def nested_get(data, dotted_key, default=None):
    current = data
    for part in dotted_key.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def nested_set(data, dotted_key, value):
    current = data
    parts = dotted_key.split(".")
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value


def resolve_config_reference(path_value, base_dir=None):
    path_value = ensure_text(path_value).strip()
    if not path_value:
        return text_type("")
    if os.path.isabs(path_value):
        return path_value
    candidates = []
    if base_dir:
        candidates.append(os.path.abspath(os.path.join(base_dir, path_value)))
    candidates.append(os.path.abspath(os.path.join(repo_root(), path_value)))
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    if base_dir:
        return os.path.abspath(os.path.join(base_dir, path_value))
    return os.path.abspath(os.path.join(repo_root(), path_value))


QUADWILD_DEFAULTS = read_json_file(default_prep_config(), {})
QFP_DEFAULTS = read_json_file(default_main_config(), {})
FLOW_SOLVER_DEFAULTS = read_json_file(default_flow_solver_config(), {})
SATSUMA_DEFAULTS = read_json_file(default_satsuma_config(), {})


QUADWILD_FORM_FIELDS = [
    {"key": "do_remesh", "label": u"执行重网格", "type": "bool", "section": u"预处理与场", "help": u"仅对 quadwild 生效。开启后先做重网格、场计算和 tracing；关闭时用于直接复用已有中间结果。"},
    {"key": "sharp_feature_thr", "label": u"锐边阈值", "type": "double", "decimals": 4, "minimum": -99999.0, "maximum": 99999.0, "section": u"预处理与场", "help": u"仅对 quadwild 生效。控制识别 sharp feature 的角度阈值，值越小越容易把边当作特征边。"},
    {"key": "alpha", "label": u"Alpha", "type": "double", "decimals": 6, "minimum": 0.0, "maximum": 99999.0, "section": u"共享量化目标", "help": u"共享参数。平衡几何等距与拓扑规则性；越小越偏规则网格，越大越偏保形。"},
    {"key": "scaleFact", "label": u"Scale Factor", "type": "double", "decimals": 6, "minimum": 0.0, "maximum": 99999.0, "section": u"共享量化目标", "help": u"共享参数。控制目标边长尺度，直接影响量化后的边数分配与最终网格密度。"},
    {"key": "fixedChartClusters", "label": u"Fixed Chart Clusters", "type": "int", "minimum": 0, "maximum": 1000000, "section": u"共享量化目标", "help": u"共享参数。固定 chart 聚类数量；0 表示不强制固定。"},
    {"key": "ilpMethod", "label": u"ILP 方法", "type": "combo", "choices": [(0, u"ABS"), (1, u"Least Squares")], "section": u"求解器", "help": u"共享参数。选择量化优化目标形式；ABS 更稳，Least Squares 往往更平滑。"},
    {"key": "timeLimit", "label": u"Time Limit", "type": "double", "decimals": 3, "minimum": 0.0, "maximum": 999999.0, "section": u"求解器", "help": u"共享参数。主求解器时间上限，单位秒。"},
    {"key": "gapLimit", "label": u"Gap Limit", "type": "double", "decimals": 9, "minimum": 0.0, "maximum": 999999.0, "section": u"求解器", "help": u"共享参数。达到该 gap 后提早停止优化；越小通常质量越好但更慢。"},
    {"key": "minimumGap", "label": u"Minimum Gap", "type": "double", "decimals": 6, "minimum": 0.0, "maximum": 999999.0, "section": u"求解器", "help": u"共享参数。若主优化未达到该最低 gap，后续会尝试更激进的求解步骤。"},
    {"key": "callbackTimeLimit", "label": u"Callback Time Limit", "type": "float_list", "section": u"求解器", "help": u"共享参数。阶段性回调时间阈值列表，使用逗号分隔秒数，例如 3, 10, 30。"},
    {"key": "callbackGapLimit", "label": u"Callback Gap Limit", "type": "float_list", "section": u"求解器", "help": u"共享参数。阶段性回调 gap 阈值列表，和 Callback Time Limit 配合使用。"},
    {"key": "isometry", "label": u"Isometry", "type": "bool", "section": u"共享量化目标", "help": u"共享参数。是否启用等距项；通常建议开启。"},
    {"key": "regularityQuadrilaterals", "label": u"Quadrilateral Regularity", "type": "bool", "section": u"共享量化目标", "help": u"共享参数。是否对四边形规则性加入约束。"},
    {"key": "regularityNonQuadrilaterals", "label": u"Non-Quad Regularity", "type": "bool", "section": u"共享量化目标", "help": u"共享参数。是否惩罚非四边形的不规则结构。"},
    {"key": "regularityNonQuadrilateralsWeight", "label": u"Non-Quad Regularity Weight", "type": "double", "decimals": 6, "minimum": 0.0, "maximum": 999999.0, "section": u"共享量化目标", "help": u"共享参数。非四边形规则性权重，越大越强烈地压制异常 valence。"},
    {"key": "alignSingularities", "label": u"Align Singularities", "type": "bool", "section": u"共享量化目标", "help": u"共享参数。是否对奇异点方向对齐施加目标。"},
    {"key": "alignSingularitiesWeight", "label": u"Align Singularities Weight", "type": "double", "decimals": 6, "minimum": 0.0, "maximum": 999999.0, "section": u"共享量化目标", "help": u"共享参数。奇异点对齐项的权重。"},
    {"key": "repeatLosingConstraintsIterations", "label": u"Repeat Losing Iterations", "type": "bool", "section": u"约束策略", "help": u"共享参数。允许在多轮优化中重复放宽失败约束。"},
    {"key": "repeatLosingConstraintsQuads", "label": u"Repeat Losing Quads", "type": "bool", "section": u"约束策略", "help": u"共享参数。是否对四边形相关失败约束重复尝试。"},
    {"key": "repeatLosingConstraintsNonQuads", "label": u"Repeat Losing Non-Quads", "type": "bool", "section": u"约束策略", "help": u"共享参数。是否对非四边形相关失败约束重复尝试。"},
    {"key": "repeatLosingConstraintsAlign", "label": u"Repeat Losing Align", "type": "bool", "section": u"约束策略", "help": u"共享参数。是否对对齐类失败约束重复尝试。"},
    {"key": "hardParityConstraint", "label": u"Hard Parity Constraint", "type": "bool", "section": u"约束策略", "help": u"共享参数。启用更严格的 parity 约束；可能提高一致性，但也可能增大求解难度。"},
    {"key": "chartSmoothingIterations", "label": u"Chart Smoothing Iterations", "type": "int", "minimum": 0, "maximum": 1000000, "section": u"仅 QuadWild 后处理", "help": u"仅对 quadwild 生效。chart 层面的平滑次数。"},
    {"key": "quadrangulationFixedSmoothingIterations", "label": u"Fixed Smoothing Iterations", "type": "int", "minimum": 0, "maximum": 1000000, "section": u"仅 QuadWild 后处理", "help": u"仅对 quadwild 生效。边界固定时的 quadrangulation 平滑次数。"},
    {"key": "quadrangulationNonFixedSmoothingIterations", "label": u"Non-Fixed Smoothing Iterations", "type": "int", "minimum": 0, "maximum": 1000000, "section": u"仅 QuadWild 后处理", "help": u"仅对 quadwild 生效。边界可动时的 quadrangulation 平滑次数。"},
    {"key": "feasibilityFix", "label": u"Feasibility Fix", "type": "bool", "section": u"仅 QuadWild 后处理", "help": u"仅对 quadwild 生效。尝试修复量化可行性问题。"},
    {"key": "useFlowSolver", "label": u"Use Flow Solver", "type": "bool", "section": u"外部求解器", "help": u"共享参数。启用 Bi-MDF / flow 路线；具体 flow 与 satsuma 细节请在“外部求解器”页配置。"},
]


QFP_FORM_FIELDS = [
    {"key": "alpha", "label": u"Alpha", "type": "double", "decimals": 6, "minimum": 0.0, "maximum": 99999.0, "section": u"共享量化目标", "help": u"仅供 quad_from_patches 阶段使用。平衡几何等距与拓扑规则性。"},
    {"key": "scaleFact", "label": u"Scale Factor", "type": "double", "decimals": 6, "minimum": 0.0, "maximum": 99999.0, "section": u"共享量化目标", "help": u"控制目标边长和最终网格密度。"},
    {"key": "fixedChartClusters", "label": u"Fixed Chart Clusters", "type": "int", "minimum": 0, "maximum": 1000000, "section": u"共享量化目标", "help": u"固定 chart 聚类数量；0 表示不固定。"},
    {"key": "ilpMethod", "label": u"ILP 方法", "type": "combo", "choices": [(0, u"ABS"), (1, u"Least Squares")], "section": u"求解器", "help": u"选择量化求解目标形式。"},
    {"key": "timeLimit", "label": u"Time Limit", "type": "double", "decimals": 3, "minimum": 0.0, "maximum": 999999.0, "section": u"求解器", "help": u"主求解器时间上限，单位秒。"},
    {"key": "gapLimit", "label": u"Gap Limit", "type": "double", "decimals": 9, "minimum": 0.0, "maximum": 999999.0, "section": u"求解器", "help": u"达到该 gap 后提前结束优化。"},
    {"key": "minimumGap", "label": u"Minimum Gap", "type": "double", "decimals": 6, "minimum": 0.0, "maximum": 999999.0, "section": u"求解器", "help": u"未达到该最低 gap 时，会继续尝试额外优化步骤。"},
    {"key": "callbackTimeLimit", "label": u"Callback Time Limit", "type": "float_list", "section": u"求解器", "help": u"阶段性时间阈值列表，逗号分隔。"},
    {"key": "callbackGapLimit", "label": u"Callback Gap Limit", "type": "float_list", "section": u"求解器", "help": u"阶段性 gap 阈值列表，逗号分隔。"},
    {"key": "isometry", "label": u"Isometry", "type": "bool", "section": u"共享量化目标", "help": u"是否启用等距项。"},
    {"key": "regularityQuadrilaterals", "label": u"Quadrilateral Regularity", "type": "bool", "section": u"共享量化目标", "help": u"是否约束四边形规则性。"},
    {"key": "regularityNonQuadrilaterals", "label": u"Non-Quad Regularity", "type": "bool", "section": u"共享量化目标", "help": u"是否惩罚非四边形异常结构。"},
    {"key": "regularityNonQuadrilateralsWeight", "label": u"Non-Quad Regularity Weight", "type": "double", "decimals": 6, "minimum": 0.0, "maximum": 999999.0, "section": u"共享量化目标", "help": u"非四边形异常惩罚权重。"},
    {"key": "alignSingularities", "label": u"Align Singularities", "type": "bool", "section": u"共享量化目标", "help": u"是否优化奇异点方向对齐。"},
    {"key": "alignSingularitiesWeight", "label": u"Align Singularities Weight", "type": "double", "decimals": 6, "minimum": 0.0, "maximum": 999999.0, "section": u"共享量化目标", "help": u"奇异点对齐项的权重。"},
    {"key": "repeatLosingConstraintsIterations", "label": u"Repeat Losing Iterations", "type": "bool", "section": u"约束策略", "help": u"允许重复放宽失败约束。"},
    {"key": "repeatLosingConstraintsQuads", "label": u"Repeat Losing Quads", "type": "bool", "section": u"约束策略", "help": u"是否重复尝试四边形类失败约束。"},
    {"key": "repeatLosingConstraintsNonQuads", "label": u"Repeat Losing Non-Quads", "type": "bool", "section": u"约束策略", "help": u"是否重复尝试非四边形类失败约束。"},
    {"key": "repeatLosingConstraintsAlign", "label": u"Repeat Losing Align", "type": "bool", "section": u"约束策略", "help": u"是否重复尝试对齐类失败约束。"},
    {"key": "hardParityConstraint", "label": u"Hard Parity Constraint", "type": "bool", "section": u"约束策略", "help": u"启用更严格的 parity 约束。"},
    {"key": "useFlowSolver", "label": u"Use Flow Solver", "type": "bool", "section": u"外部求解器", "help": u"启用 Bi-MDF / flow 路径；具体 flow 与 satsuma 细节请在“外部求解器”页配置。"},
]


FLOW_SOLVER_FORM_FIELDS = [
    {"key": "paired_half_target", "label": u"Half Target", "type": "combo", "choices": [("half", u"half"), ("simple", u"simple")], "section": u"总体策略", "help": u"控制 paired 边在 Bi-MDF 建模时如何拆成两个子目标。`simple` 会调用 virtual_subside_target，通常更稳，也是当前默认配置；`half` 会直接按 1/2-1/2 平分目标，只有在你明确想要更对称、但能接受更强人为假设时再试。推荐：先保持 `simple`。"},
    {"key": "paired_resolve_new_targets", "label": u"Resolve New Targets", "type": "bool", "section": u"总体策略", "help": u"第二轮 resolve 时，是否根据上一轮解出的两条 paired 子边流量重新分配目标。开启后，第二轮会更贴近第一轮真实解，通常更容易消化 paired 边不平衡；关闭则继续沿用初始目标。推荐：默认开启，仅在你希望两轮目标严格一致时关闭。"},
    {"key": "paired_initial.iso_weight", "label": u"Initial Iso Weight", "type": "double", "decimals": 6, "minimum": 0.0, "maximum": 999999.0, "section": u"Paired Initial", "help": u"paired 初始求解阶段的等距项权重，对应源码中的 aligned_iso_scale。值越大，paired 子边长度越强地贴近目标；值越小，求解器会更愿意为了整体可行性放松长度一致。推荐：从默认 `1.0` 开始；如果 paired 边分配明显失真可上调到 `1.5-3`，若可行性差或过度僵硬可降到 `0.5`。"},
    {"key": "paired_initial.iso_objective", "label": u"Initial Iso Objective", "type": "combo", "choices": [("abs", u"abs"), ("quad", u"quad")], "section": u"Paired Initial", "help": u"paired 初始阶段的等距代价形式。`quad` 更强地惩罚大偏差，适合默认求稳；`abs` 对离群偏差更宽容，通常在后续收敛或困难模型上更稳。推荐：初始阶段保留默认 `quad`。"},
    {"key": "paired_initial.unalign_weight", "label": u"Initial Unalign Weight", "type": "double", "decimals": 6, "minimum": 0.0, "maximum": 999999.0, "section": u"Paired Initial", "help": u"paired 初始阶段的未对齐惩罚权重。值越大，左右 paired 侧越不允许出现不一致拆分，但过大可能让问题更硬。推荐：默认 `2.0`；若 paired 边经常拆得很偏，可提高到 `3-6`，若求解困难则先降回 `1-2`。"},
    {"key": "paired_resolve.iso_weight", "label": u"Resolve Iso Weight", "type": "double", "decimals": 6, "minimum": 0.0, "maximum": 999999.0, "section": u"Paired Resolve", "help": u"paired resolve 阶段的等距项权重。这个阶段是在已有前一轮解的基础上做修正，通常保持与初始相同或略强即可。推荐：默认 `1.0`；只有在第二轮仍然出现明显长度漂移时再提高。"},
    {"key": "paired_resolve.iso_objective", "label": u"Resolve Iso Objective", "type": "combo", "choices": [("abs", u"abs"), ("quad", u"quad")], "section": u"Paired Resolve", "help": u"paired resolve 阶段的等距代价形式。当前默认 `abs`，因为第二轮更偏向稳健修正而不是继续放大大偏差惩罚。推荐：保留 `abs`；如果你想让第二轮也更激进地压大偏差，可试 `quad`。"},
    {"key": "paired_resolve.unalign_weight", "label": u"Resolve Unalign Weight", "type": "double", "decimals": 6, "minimum": 0.0, "maximum": 999999.0, "section": u"Paired Resolve", "help": u"paired resolve 阶段的未对齐惩罚权重。默认 `4.0` 高于初始阶段，表示第二轮会更强地拉齐 paired 侧拆分。推荐：先保持默认；若最终 paired 边仍不齐可继续上调到 `6-8`，若第二轮经常把问题推向不可行或质量下降则回落到 `2-4`。"},
]


SATSUMA_FORM_FIELDS = [
    {"key": "double_cover.max_deviation", "label": u"DC Max Deviation", "type": "int", "minimum": 0, "maximum": 1000000, "section": u"Double Cover", "help": u"double-cover 近似阶段的最大允许偏差。源码会把它传入 `BiMDF_to_BiMCF` 作为 `max_deviation`，值越大，近似空间越宽、通常更稳但更慢；值太小可能让近似表达能力不足。推荐：默认 `5`；小模型或追求更严近似可试 `3-4`，大模型或经常卡在近似不足时可升到 `6-8`。"},
    {"key": "double_cover.matching_solver", "label": u"DC Matching Solver", "type": "combo", "choices": [("Lemon", u"Lemon"), ("lemon", u"lemon")], "section": u"Double Cover", "help": u"double-cover 阶段使用的 matching / MCF 后端。当前仓库默认与主配置都使用 `Lemon`，兼容性最好。推荐：保持 `Lemon`，除非你明确接入了其他后端并验证可用。"},
    {"key": "double_cover.evening_mode", "label": u"DC Evening Mode", "type": "combo", "choices": [("MST", u"MST"), ("RoundToEven", u"RoundToEven")], "section": u"Double Cover", "help": u"决定 even RHS 的猜测方式，即 double-cover 之前如何把问题调整到偶数约束。`MST` 更稳，是默认方案；`RoundToEven` 更直接但可能更粗糙。推荐：优先 `MST`，只有在调试近似策略或想比较更简单的 even 化方式时再试 `RoundToEven`。"},
    {"key": "double_cover.method", "label": u"DC Method", "type": "combo", "choices": [("HalfAsymmetric", u"HalfAsymmetric"), ("HalfSymmetric", u"HalfSymmetric")], "section": u"Double Cover", "help": u"控制 BiMCF 向 MCF 的 half reduction 方式。`HalfAsymmetric` 是库里的默认方法，也是当前配置默认；`HalfSymmetric` 更对称，但常配合关闭 refinement 用于近似变体测试。推荐：保持 `HalfAsymmetric`，只有在比较不同近似风格时再试 `HalfSymmetric`。"},
    {"key": "double_cover.verbosity", "label": u"DC Verbosity", "type": "int", "minimum": 0, "maximum": 1000000, "section": u"Double Cover", "help": u"仅控制 double-cover 阶段的日志细节。`0-1` 适合日常运行，`2+` 适合排查 evening / max deviation 行为。推荐：默认 `1`；定位问题时临时调到 `2` 或 `3`。"},
    {"key": "refine_with_matching", "label": u"Refine With Matching", "type": "bool", "section": u"Refinement", "help": u"是否在 double-cover 得到初始解后继续做 matching refinement。源码里关闭后会直接返回近似解，开启后会按 `refinement_maxdev_min..max` 循环改进成本。推荐：默认开启；只有在你只想要快速近似结果、或专门比较 DC 结果时关闭。"},
    {"key": "matching_solver", "label": u"Matching Solver", "type": "combo", "choices": [("Lemon", u"Lemon"), ("lemon", u"lemon")], "section": u"Refinement", "help": u"refinement 阶段的 matching 求解后端。当前项目默认全用 `Lemon`，最稳。推荐：保持 `Lemon`。"},
    {"key": "refinement_maxdev_min", "label": u"Refine MaxDev Min", "type": "int", "minimum": 0, "maximum": 1000000, "section": u"Refinement", "help": u"refinement 扫描的起始 `max deviation`。源码会从这个值开始逐级尝试 matching refinement。值越小，每轮修改更保守；值越大，更可能带来更明显改进但搜索成本更高。推荐：默认 `2`。"},
    {"key": "refinement_maxdev_max", "label": u"Refine MaxDev Max", "type": "int", "minimum": 0, "maximum": 1000000, "section": u"Refinement", "help": u"refinement 扫描的结束 `max deviation`。若与最小值相同，就只跑一个固定强度；若更大，源码会从最小值逐个递增尝试，直到该上限。推荐：默认与最小值同为 `2`；只有当你确认 refinement 改进不足时，再尝试扩到 `3-5`。"},
    {"key": "deviation_limit", "label": u"Deviation Limit", "type": "combo", "choices": [("NodeThroughflow", u"NodeThroughflow"), ("EdgeFlow", u"EdgeFlow")], "section": u"Refinement", "help": u"决定 refinement 时偏差约束按节点 throughflow 还是按边流量来限制。`NodeThroughflow` 是默认且更常见的模式；`EdgeFlow` 会更直接限制单边变化，通常更保守。推荐：先保持 `NodeThroughflow`，只有在你想更强约束单边变化时再试 `EdgeFlow`。"},
    {"key": "verbosity", "label": u"Verbosity", "type": "int", "minimum": 0, "maximum": 1000000, "section": u"Refinement", "help": u"整体 satsuma 高层流程的日志级别。`1` 会打印 refinement 过程，`2+` 会看到更多 double-cover 与改进细节。推荐：默认 `2` 便于观察优化过程；批量跑任务时可降到 `1`。"},
]


SHARED_MAIN_CONFIG_KEYS = sorted(set([spec["key"] for spec in QUADWILD_FORM_FIELDS]).intersection(set([spec["key"] for spec in QFP_FORM_FIELDS])))


class ProcessWorker(QtCore.QObject):
    log_message = QtCore.Signal(str)
    status_changed = QtCore.Signal(str, str)
    finished = QtCore.Signal(bool, str, str)

    def __init__(self, settings):
        QtCore.QObject.__init__(self)
        self._settings = settings
        self._cancel_requested = False
        self._current_process = None

    @QtCore.Slot()
    def cancel(self):
        self._cancel_requested = True
        if self._current_process is not None:
            try:
                self._current_process.terminate()
            except Exception:
                pass
        self.log_message.emit(u"[WARN] 已请求中断当前任务。")

    def emit_status(self, state, detail):
        self.status_changed.emit(ensure_text(state), ensure_text(detail))

    def ensure_not_cancelled(self):
        if self._cancel_requested:
            raise RuntimeError(u"用户已中断任务。")

    def run(self):
        workspace = text_type("")
        state = "failed"
        try:
            self.emit_status(u"准备中", u"创建工作目录与配置文件")
            workspace, command_specs = self.prepare_workspace_and_commands()
            commands_file = os.path.join(workspace, "commands.txt")
            write_text_file(
                commands_file,
                u"\n".join([u"{0}: {1}".format(label, command_to_text(cmd)) for label, cmd in command_specs])
            )

            for label, command in command_specs:
                self.ensure_not_cancelled()
                self.emit_status(u"运行中", label)
                self.log_message.emit(u"[INFO] 开始执行: {0}".format(label))
                self.log_message.emit(command_to_text(command))
                exit_code = self.run_process(command)
                if self._cancel_requested:
                    raise RuntimeError(u"用户已中断任务。")
                if exit_code != 0:
                    raise RuntimeError(u"{0} 执行失败，退出码 {1}".format(label, exit_code))

            state = "success"
            self.emit_status(u"已完成", u"全部流程执行完成")
            self.log_message.emit(u"[INFO] 全部流程执行完成。")
            self.finished.emit(True, workspace, state)
        except Exception as exc:
            if self._cancel_requested:
                state = "canceled"
                self.emit_status(u"已中断", u"用户取消")
                self.log_message.emit(u"[WARN] 任务已被用户中断。")
                self.finished.emit(False, workspace, state)
            else:
                self.emit_status(u"失败", ensure_text(exc))
                self.log_message.emit(u"[ERROR] {0}".format(ensure_text(exc)))
                self.log_message.emit(ensure_text(traceback.format_exc()))
                self.finished.emit(False, workspace, state)

    def run_process(self, command):
        self._current_process = subprocess.Popen(
            command,
            cwd=self._settings["process_cwd"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        try:
            while True:
                line = self._current_process.stdout.readline()
                if not line:
                    break
                self.log_message.emit(ensure_text(line.rstrip()))
        finally:
            try:
                self._current_process.stdout.close()
            except Exception:
                pass
        exit_code = self._current_process.wait()
        self._current_process = None
        return exit_code

    def prepare_workspace_and_commands(self):
        workflow = self._settings["workflow"]
        output_root = self._settings["output_root"]
        job_name = sanitize_name(self._settings["job_name"])
        workspace = os.path.join(output_root, job_name)
        safe_makedirs(workspace)

        self.log_message.emit(u"[INFO] 输出工作目录: {0}".format(workspace))

        staged_flow_config = os.path.join(workspace, "flow_solver_config.json")
        staged_satsuma_config = os.path.join(workspace, "satsuma_solver_config.json")
        write_text_file(staged_flow_config, self._settings["flow_solver_config_text"])
        write_text_file(staged_satsuma_config, self._settings["satsuma_solver_config_text"])

        staged_quadwild_config = os.path.join(workspace, "quadwild_config.json")
        staged_qfp_config = os.path.join(workspace, "quad_from_patches_config.json")
        quadwild_config_data = deep_copy_json_dict(self._settings["quadwild_config_data"])
        qfp_config_data = deep_copy_json_dict(self._settings["quad_from_patches_config_data"])
        quadwild_config_data["flow_config_filename"] = staged_flow_config
        quadwild_config_data["satsuma_config_filename"] = staged_satsuma_config
        qfp_config_data["flow_config_filename"] = staged_flow_config
        qfp_config_data["satsuma_config_filename"] = staged_satsuma_config
        write_text_file(staged_quadwild_config, json.dumps(quadwild_config_data, indent=2, ensure_ascii=False, sort_keys=False))
        write_text_file(staged_qfp_config, json.dumps(qfp_config_data, indent=2, ensure_ascii=False, sort_keys=False))

        command_specs = []

        if workflow in ("full_pipeline", "quadwild_only"):
            staged_quadwild_mesh = copy_file_to_directory(self._settings["quadwild_input_mesh"], workspace)
            staged_sharp = text_type("")
            staged_rosy = text_type("")
            if self._settings["sharp_file"]:
                staged_sharp = copy_file_to_directory(self._settings["sharp_file"], workspace)
            if self._settings["rosy_file"]:
                staged_rosy = copy_file_to_directory(self._settings["rosy_file"], workspace)

            stop_step = self._settings["quadwild_stop_step"]
            if workflow == "full_pipeline":
                stop_step = "2"

            quadwild_command = [
                self._settings["quadwild_binary"],
                staged_quadwild_mesh,
                stop_step,
                staged_quadwild_config
            ]
            if staged_sharp:
                quadwild_command.append(staged_sharp)
            if staged_rosy:
                quadwild_command.append(staged_rosy)
            quadwild_command.extend(split_extra_args(self._settings["quadwild_extra_args"]))
            command_specs.append((u"quadwild", quadwild_command))

            should_run_viz = self._settings.get("enable_viz_export", False)
            can_run_viz_after_quadwild = (workflow == "full_pipeline") or (workflow == "quadwild_only" and stop_step in ("2", "3"))
            if should_run_viz and can_run_viz_after_quadwild:
                rem_mesh = os.path.splitext(staged_quadwild_mesh)[0] + "_rem.obj"
                viz_command = [
                    self._settings["viz_mesh_results_binary"],
                    rem_mesh
                ]
                command_specs.append((u"viz_mesh_results", viz_command))
            elif should_run_viz and workflow == "quadwild_only":
                self.log_message.emit(u"[WARN] 当前 quadwild 停止步骤早于 tracing，可视化导出已跳过。")

            if workflow == "full_pipeline":
                rem_p0_mesh = os.path.splitext(staged_quadwild_mesh)[0] + "_rem_p0.obj"
                quad_from_patches_command = self.build_quad_from_patches_command(rem_p0_mesh, staged_qfp_config, workspace)
                command_specs.append((u"quad_from_patches", quad_from_patches_command))

        if workflow == "quad_from_patches_only":
            staged_qfp_mesh = copy_file_to_directory(self._settings["quad_from_patches_input_mesh"], workspace)
            copy_sidecars(
                self._settings["quad_from_patches_input_mesh"],
                workspace,
                [".patch", ".corners", ".feature", ".c_feature"],
                self.log_message.emit
            )
            quad_from_patches_command = self.build_quad_from_patches_command(staged_qfp_mesh, staged_qfp_config, workspace)
            command_specs.append((u"quad_from_patches", quad_from_patches_command))

        return workspace, command_specs

    def build_quad_from_patches_command(self, mesh_path, config_path, workspace):
        command = [
            self._settings["quad_from_patches_binary"],
            mesh_path,
            self._settings["quad_from_patches_num"],
            config_path
        ]
        stats_name = ensure_text(self._settings["stats_json"]).strip()
        if stats_name:
            if not os.path.isabs(stats_name):
                stats_name = os.path.join(workspace, stats_name)
            command.append(stats_name)
        command.extend(split_extra_args(self._settings["quad_from_patches_extra_args"]))
        return command


class QuadWildWindow(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.worker_thread = None
        self.worker = None
        self.last_workspace = text_type("")
        self.job_name_manually_edited = False
        self._syncing_quadwild_input = False
        self._syncing_shared_config = False
        self._config_sender_map = {}
        self.quadwild_form_widgets = {}
        self.qfp_form_widgets = {}
        self.flow_solver_form_widgets = {}
        self.satsuma_form_widgets = {}
        self.quadwild_json_preview = None
        self.qfp_json_preview = None
        self.flow_solver_json_preview = None
        self.satsuma_solver_json_preview = None
        self.setWindowTitle(u"QuadWild Binary UI")
        self.resize(1380, 960)
        self.build_ui()
        self.load_settings()
        self.apply_defaults_if_needed()
        self.update_mode()
        self.refresh_json_previews()
        self.update_command_preview()
        self.update_runtime_status(u"空闲", u"未开始")

    def build_ui(self):
        central = QtWidgets.QWidget(self)
        self.setCentralWidget(central)
        root_layout = QtWidgets.QVBoxLayout(central)

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.addTab(self.build_general_tab(), u"总览")
        self.tabs.addTab(self.build_quadwild_tab(), u"QuadWild")
        self.tabs.addTab(self.build_qfp_tab(), u"Quad From Patches")
        self.tabs.addTab(self.build_external_solver_tab(), u"外部求解器")
        self.tabs.addTab(self.build_execution_tab(), u"执行")
        root_layout.addWidget(self.tabs, 1)

        button_layout = QtWidgets.QHBoxLayout()
        self.start_button = QtWidgets.QPushButton(u"开始执行")
        self.cancel_button = QtWidgets.QPushButton(u"中断执行")
        self.cancel_button.setEnabled(False)
        self.reset_button = QtWidgets.QPushButton(u"重置默认")
        self.open_output_button = QtWidgets.QPushButton(u"打开输出目录")
        self.open_output_button.setEnabled(False)
        self.save_settings_button = QtWidgets.QPushButton(u"保存界面设置")

        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.open_output_button)
        button_layout.addStretch(1)
        button_layout.addWidget(self.save_settings_button)
        root_layout.addLayout(button_layout)

        self.start_button.clicked.connect(self.start_workflow)
        self.cancel_button.clicked.connect(self.cancel_workflow)
        self.reset_button.clicked.connect(self.reset_defaults)
        self.open_output_button.clicked.connect(self.open_output_directory)
        self.save_settings_button.clicked.connect(self.save_settings)

    def build_general_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)

        status_group = QtWidgets.QGroupBox(u"运行状态")
        status_layout = QtWidgets.QGridLayout(status_group)
        self.binding_value = QtWidgets.QLabel(ensure_text(QT_BINDING))
        self.status_value = QtWidgets.QLabel()
        self.stage_value = QtWidgets.QLabel()
        self.workspace_value = QtWidgets.QLabel(u"-")
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)

        status_layout.addWidget(QtWidgets.QLabel(u"Qt 绑定"), 0, 0)
        status_layout.addWidget(self.binding_value, 0, 1)
        status_layout.addWidget(QtWidgets.QLabel(u"状态"), 1, 0)
        status_layout.addWidget(self.status_value, 1, 1)
        status_layout.addWidget(QtWidgets.QLabel(u"当前阶段"), 2, 0)
        status_layout.addWidget(self.stage_value, 2, 1)
        status_layout.addWidget(QtWidgets.QLabel(u"最近输出目录"), 3, 0)
        status_layout.addWidget(self.workspace_value, 3, 1)
        status_layout.addWidget(self.progress_bar, 4, 0, 1, 2)
        layout.addWidget(status_group)

        general_group = QtWidgets.QGroupBox(u"任务与路径")
        form = QtWidgets.QFormLayout(general_group)
        self.workflow_combo = QtWidgets.QComboBox()
        self.workflow_combo.addItem(u"完整流程：quadwild -> quad_from_patches", "full_pipeline")
        self.workflow_combo.addItem(u"仅运行 quadwild", "quadwild_only")
        self.workflow_combo.addItem(u"仅运行 quad_from_patches", "quad_from_patches_only")
        self.workflow_combo.setToolTip(u"选择本次运行执行到哪个阶段。完整流程会先运行 quadwild，再自动调用 quad_from_patches。")

        self.output_root_edit = QtWidgets.QLineEdit()
        self.output_root_button = QtWidgets.QPushButton(u"浏览...")
        self.job_name_edit = QtWidgets.QLineEdit()
        self.job_name_generate_button = QtWidgets.QPushButton(u"自动生成")
        self.job_name_edit.textEdited.connect(self.on_job_name_edited)

        form.addRow(u"工作流", self.workflow_combo)
        form.addRow(u"输出根目录", self.browse_row(self.output_root_edit, self.output_root_button))
        form.addRow(u"任务文件夹名", self.browse_row(self.job_name_edit, self.job_name_generate_button))
        layout.addWidget(general_group)

        binary_group = QtWidgets.QGroupBox(u"二进制路径")
        binary_form = QtWidgets.QFormLayout(binary_group)
        self.quadwild_binary_edit = QtWidgets.QLineEdit()
        self.quadwild_binary_button = QtWidgets.QPushButton(u"浏览...")
        self.qfp_binary_edit = QtWidgets.QLineEdit()
        self.qfp_binary_button = QtWidgets.QPushButton(u"浏览...")
        self.viz_binary_edit = QtWidgets.QLineEdit()
        self.viz_binary_button = QtWidgets.QPushButton(u"浏览...")
        self.quadwild_binary_edit.setToolTip(u"quadwild 可执行文件路径。若填写仓库内旧路径，UI 会自动解析到最新构建产物。")
        self.qfp_binary_edit.setToolTip(u"quad_from_patches 可执行文件路径。若填写仓库内旧路径，UI 会自动解析到最新构建产物。")
        self.viz_binary_edit.setToolTip(u"viz_mesh_results 可执行文件路径。若启用可视化导出，UI 会在 quadwild 生成 tracing 中间结果后调用它，导出 field / sharp / patch 检查文件。")
        binary_form.addRow(u"quadwild.exe", self.browse_row(self.quadwild_binary_edit, self.quadwild_binary_button))
        binary_form.addRow(u"quad_from_patches.exe", self.browse_row(self.qfp_binary_edit, self.qfp_binary_button))
        binary_form.addRow(u"viz_mesh_results.exe", self.browse_row(self.viz_binary_edit, self.viz_binary_button))
        layout.addWidget(binary_group)

        viz_group = QtWidgets.QGroupBox(u"检查导出")
        viz_form = QtWidgets.QFormLayout(viz_group)
        self.enable_viz_checkbox = QtWidgets.QCheckBox(u"运行 viz_mesh_results 导出检查文件")
        self.enable_viz_checkbox.setToolTip(u"勾选后，在 quadwild 完成 tracing 并生成 *_rem / *_rem_p0 相关文件后，自动调用 viz_mesh_results.exe 生成 _field_mesh.ply、_sharp_mesh.ply、_borderpatch_mesh.ply、_colorpatch_mesh.ply 等可视化文件。")
        viz_hint = QtWidgets.QLabel(u"依赖 quadwild 的 step 2 或完整流程输出；若仅停在 step 1，将自动跳过。")
        viz_hint.setWordWrap(True)
        viz_form.addRow(self.enable_viz_checkbox)
        viz_form.addRow(viz_hint)
        layout.addWidget(viz_group)

        overview_input_group = QtWidgets.QGroupBox(u"QuadWild 快速输入")
        overview_form = QtWidgets.QFormLayout(overview_input_group)
        self.quadwild_input_general_edit = QtWidgets.QLineEdit()
        self.quadwild_input_general_button = QtWidgets.QPushButton(u"浏览...")
        self.quadwild_input_general_edit.setToolTip(u"QuadWild 输入网格。总览页与 QuadWild 页的该字段保持实时同步。")
        overview_form.addRow(u"输入网格", self.browse_row(self.quadwild_input_general_edit, self.quadwild_input_general_button))
        layout.addWidget(overview_input_group)
        layout.addStretch(1)

        self.workflow_combo.currentIndexChanged.connect(self.update_mode)
        self.output_root_button.clicked.connect(lambda: self.choose_directory(self.output_root_edit))
        self.job_name_generate_button.clicked.connect(self.regenerate_job_name)
        self.quadwild_binary_button.clicked.connect(lambda: self.choose_file(self.quadwild_binary_edit, u"选择 quadwild 可执行文件", u"Executable (*.exe);;All Files (*)"))
        self.qfp_binary_button.clicked.connect(lambda: self.choose_file(self.qfp_binary_edit, u"选择 quad_from_patches 可执行文件", u"Executable (*.exe);;All Files (*)"))
        self.viz_binary_button.clicked.connect(lambda: self.choose_file(self.viz_binary_edit, u"选择 viz_mesh_results 可执行文件", u"Executable (*.exe);;All Files (*)"))
        self.quadwild_input_general_button.clicked.connect(lambda: self.choose_file(self.quadwild_input_general_edit, u"选择 QuadWild 输入网格", u"Mesh Files (*.obj *.ply);;All Files (*)"))
        self.enable_viz_checkbox.stateChanged.connect(self.update_command_preview)
        self.connect_preview_updates([self.output_root_edit, self.job_name_edit, self.quadwild_binary_edit, self.qfp_binary_edit, self.viz_binary_edit])
        return tab

    def build_quadwild_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)

        summary = QtWidgets.QLabel(u"此页只展示 quadwild.exe 真正读取的参数。前两项用于 remesh / tracing，其余为 quadrangulation 配置。")
        summary.setWordWrap(True)
        layout.addWidget(summary)

        input_group = QtWidgets.QGroupBox(u"输入与执行参数")
        form = QtWidgets.QFormLayout(input_group)
        self.quadwild_input_edit = QtWidgets.QLineEdit()
        self.quadwild_input_button = QtWidgets.QPushButton(u"浏览...")
        self.stop_step_combo = QtWidgets.QComboBox()
        self.stop_step_combo.addItem(u"1 - 仅重网格与场", "1")
        self.stop_step_combo.addItem(u"2 - 处理到 Tracing", "2")
        self.stop_step_combo.addItem(u"3 - 处理到 Quadrangulation", "3")
        self.sharp_edit = QtWidgets.QLineEdit()
        self.sharp_button = QtWidgets.QPushButton(u"浏览...")
        self.rosy_edit = QtWidgets.QLineEdit()
        self.rosy_button = QtWidgets.QPushButton(u"浏览...")
        self.quadwild_extra_args_edit = QtWidgets.QLineEdit()
        self.quadwild_input_edit.setToolTip(u"quadwild 的输入网格路径。完整流程下会复制到任务目录后再执行。")
        self.stop_step_combo.setToolTip(u"控制 quadwild 停在哪个阶段。完整流程会自动强制使用 2，以便把结果交给 quad_from_patches。")
        self.sharp_edit.setToolTip(u"可选的现成 .sharp 文件。提供后会与输入网格一同复制到任务目录。")
        self.rosy_edit.setToolTip(u"可选的现成 .rosy 文件。提供后会与输入网格一同复制到任务目录。")
        self.quadwild_extra_args_edit.setToolTip(u"直接附加到 quadwild 命令行末尾的额外参数，按命令行方式填写。")

        form.addRow(u"输入网格", self.browse_row(self.quadwild_input_edit, self.quadwild_input_button))
        form.addRow(u"停止步骤", self.stop_step_combo)
        form.addRow(u"可选 .sharp", self.browse_row(self.sharp_edit, self.sharp_button))
        form.addRow(u"可选 .rosy", self.browse_row(self.rosy_edit, self.rosy_button))
        form.addRow(u"额外参数", self.quadwild_extra_args_edit)
        layout.addWidget(input_group)

        config_group = self.build_config_group(
            kind="quadwild",
            title=u"QuadWild JSON 配置",
            path_attr="quadwild_config_path_edit",
            load_title=u"选择 QuadWild JSON 配置文件",
            default_data=QUADWILD_DEFAULTS,
            field_specs=QUADWILD_FORM_FIELDS
        )
        layout.addWidget(config_group, 1)

        self.quadwild_input_button.clicked.connect(lambda: self.choose_file(self.quadwild_input_edit, u"选择 QuadWild 输入网格", u"Mesh Files (*.obj *.ply);;All Files (*)"))
        self.sharp_button.clicked.connect(lambda: self.choose_file(self.sharp_edit, u"选择 .sharp 文件", u"Sharp Files (*.sharp);;All Files (*)"))
        self.rosy_button.clicked.connect(lambda: self.choose_file(self.rosy_edit, u"选择 .rosy 文件", u"Rosy Files (*.rosy);;All Files (*)"))
        self.quadwild_extra_args_edit.textChanged.connect(self.update_command_preview)
        self.stop_step_combo.currentIndexChanged.connect(self.update_command_preview)
        return tab

    def build_qfp_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)

        summary = QtWidgets.QLabel(u"此页只展示 quad_from_patches.exe 真正读取的参数。它不读取 quadwild 的 remesh、sharp 阈值和 quadwild 专属 smoothing / feasibility 参数。")
        summary.setWordWrap(True)
        layout.addWidget(summary)

        input_group = QtWidgets.QGroupBox(u"输入与执行参数")
        form = QtWidgets.QFormLayout(input_group)
        self.qfp_input_edit = QtWidgets.QLineEdit()
        self.qfp_input_button = QtWidgets.QPushButton(u"浏览...")
        self.qfp_num_spin = QtWidgets.QSpinBox()
        self.qfp_num_spin.setRange(0, 1000000)
        self.qfp_auto_label = QtWidgets.QLabel(u"完整流程下会自动使用 quadwild 生成的 *_rem_p0.obj")
        self.qfp_auto_label.setWordWrap(True)
        self.stats_json_edit = QtWidgets.QLineEdit()
        self.stats_json_button = QtWidgets.QPushButton(u"浏览...")
        self.qfp_extra_args_edit = QtWidgets.QLineEdit()
        self.qfp_input_edit.setToolTip(u"仅在“仅运行 quad_from_patches”时需要手动指定。完整流程下会自动接收 quadwild 的 *_rem_p0.obj。")
        self.qfp_num_spin.setToolTip(u"传给 quad_from_patches 的 num 参数，用于区分输出文件名。")
        self.stats_json_edit.setToolTip(u"可选的统计 JSON 输出路径。若填写相对路径，会写到任务目录下。")
        self.qfp_extra_args_edit.setToolTip(u"直接附加到 quad_from_patches 命令行末尾的额外参数。")

        form.addRow(u"输入网格", self.browse_row(self.qfp_input_edit, self.qfp_input_button))
        form.addRow(u"自动说明", self.qfp_auto_label)
        form.addRow(u"序号参数 num", self.qfp_num_spin)
        form.addRow(u"统计 JSON 输出", self.browse_row(self.stats_json_edit, self.stats_json_button))
        form.addRow(u"额外参数", self.qfp_extra_args_edit)
        layout.addWidget(input_group)

        config_group = self.build_config_group(
            kind="qfp",
            title=u"Quad From Patches JSON 配置",
            path_attr="qfp_config_path_edit",
            load_title=u"选择 Quad From Patches JSON 配置文件",
            default_data=QFP_DEFAULTS,
            field_specs=QFP_FORM_FIELDS
        )
        layout.addWidget(config_group, 1)

        self.qfp_input_button.clicked.connect(lambda: self.choose_file(self.qfp_input_edit, u"选择 Quad From Patches 输入网格", u"OBJ Files (*.obj);;All Files (*)"))
        self.stats_json_button.clicked.connect(lambda: self.choose_save_file(self.stats_json_edit, u"选择统计 JSON 输出", u"JSON Files (*.json);;All Files (*)"))
        self.qfp_num_spin.valueChanged.connect(self.update_command_preview)
        self.qfp_extra_args_edit.textChanged.connect(self.update_command_preview)
        self.stats_json_edit.textChanged.connect(self.update_command_preview)
        return tab

    def build_external_solver_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)

        summary = QtWidgets.QLabel(u"这里配置 flow 与 satsuma 的外部求解器 JSON 内容。运行时 UI 会自动把这些配置写入任务目录，并回填到 quadwild / quad_from_patches 主配置中。")
        summary.setWordWrap(True)
        layout.addWidget(summary)

        flow_group = self.build_config_group(
            kind="flow_solver",
            title=u"Flow Solver JSON 配置",
            path_attr="flow_solver_config_path_edit",
            load_title=u"选择 Flow Solver JSON 配置文件",
            default_data=FLOW_SOLVER_DEFAULTS,
            field_specs=FLOW_SOLVER_FORM_FIELDS
        )
        layout.addWidget(flow_group, 1)

        satsuma_group = self.build_config_group(
            kind="satsuma_solver",
            title=u"Satsuma Solver JSON 配置",
            path_attr="satsuma_solver_config_path_edit",
            load_title=u"选择 Satsuma Solver JSON 配置文件",
            default_data=SATSUMA_DEFAULTS,
            field_specs=SATSUMA_FORM_FIELDS
        )
        layout.addWidget(satsuma_group, 1)
        return tab

    def build_execution_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)
        splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)

        preview_group = QtWidgets.QGroupBox(u"命令与配置预览")
        preview_layout = QtWidgets.QVBoxLayout(preview_group)
        self.preview_text = QtWidgets.QPlainTextEdit()
        self.preview_text.setReadOnly(True)
        preview_layout.addWidget(self.preview_text)

        log_group = QtWidgets.QGroupBox(u"执行日志")
        log_layout = QtWidgets.QVBoxLayout(log_group)
        self.log_text = QtWidgets.QPlainTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)

        splitter.addWidget(preview_group)
        splitter.addWidget(log_group)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter, 1)
        return tab

    def build_config_group(self, kind, title, path_attr, load_title, default_data, field_specs):
        group = QtWidgets.QGroupBox(title)
        group_layout = QtWidgets.QVBoxLayout(group)

        path_layout = QtWidgets.QHBoxLayout()
        path_edit = QtWidgets.QLineEdit()
        path_edit.textChanged.connect(self.on_config_changed)
        setattr(self, path_attr, path_edit)
        load_button = QtWidgets.QPushButton(u"从文件加载")
        save_button = QtWidgets.QPushButton(u"保存到文件")
        reset_button = QtWidgets.QPushButton(u"恢复默认")
        path_layout.addWidget(path_edit, 1)
        path_layout.addWidget(load_button)
        path_layout.addWidget(save_button)
        path_layout.addWidget(reset_button)
        group_layout.addLayout(path_layout)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        form_container = QtWidgets.QWidget()
        form_layout = QtWidgets.QVBoxLayout(form_container)

        widget_map = {}
        section_forms = {}
        for spec in field_specs:
            widget = self.create_config_field_widget(kind, spec)
            self.apply_field_help(widget, spec)
            widget_map[spec["key"]] = widget
            self.register_config_widget(kind, spec["key"], widget)
            section_name = spec.get("section", u"未分组")
            if section_name not in section_forms:
                section_group = QtWidgets.QGroupBox(section_name)
                section_form = QtWidgets.QFormLayout(section_group)
                section_form.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
                form_layout.addWidget(section_group)
                section_forms[section_name] = section_form
            label_widget = QtWidgets.QLabel(spec["label"])
            if spec.get("help"):
                label_widget.setToolTip(spec["help"])
            section_forms[section_name].addRow(label_widget, widget if spec["type"] != "bool" else self.wrap_checkbox(widget))

        form_layout.addStretch(1)

        if kind == "quadwild":
            self.quadwild_form_widgets = widget_map
        elif kind == "qfp":
            self.qfp_form_widgets = widget_map
        elif kind == "flow_solver":
            self.flow_solver_form_widgets = widget_map
        else:
            self.satsuma_form_widgets = widget_map

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(form_container)
        splitter.addWidget(scroll)

        preview = QtWidgets.QPlainTextEdit()
        preview.setReadOnly(True)
        splitter.addWidget(preview)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        if kind == "quadwild":
            self.quadwild_json_preview = preview
        elif kind == "qfp":
            self.qfp_json_preview = preview
        elif kind == "flow_solver":
            self.flow_solver_json_preview = preview
        else:
            self.satsuma_solver_json_preview = preview

        group_layout.addWidget(splitter, 1)

        load_button.clicked.connect(lambda: self.load_config_from_file(kind, load_title))
        save_button.clicked.connect(lambda: self.save_config_to_file(kind))
        reset_button.clicked.connect(lambda: self.reset_config_to_defaults(kind, default_data))
        return group

    def create_config_field_widget(self, kind, spec):
        field_type = spec["type"]
        if field_type == "bool":
            widget = QtWidgets.QCheckBox()
            widget.stateChanged.connect(self.on_config_changed)
            return widget

        if field_type == "int":
            widget = QtWidgets.QSpinBox()
            widget.setRange(spec.get("minimum", -1000000), spec.get("maximum", 1000000))
            widget.valueChanged.connect(self.on_config_changed)
            return widget

        if field_type == "double":
            widget = QtWidgets.QDoubleSpinBox()
            widget.setDecimals(spec.get("decimals", 6))
            widget.setRange(spec.get("minimum", -1000000.0), spec.get("maximum", 1000000.0))
            widget.setSingleStep(spec.get("step", 0.1))
            widget.valueChanged.connect(self.on_config_changed)
            return widget

        if field_type == "combo":
            widget = QtWidgets.QComboBox()
            for value, label in spec["choices"]:
                widget.addItem(label, value)
            widget.currentIndexChanged.connect(self.on_config_changed)
            return widget

        if field_type == "float_list":
            widget = QtWidgets.QLineEdit()
            widget.setPlaceholderText(spec.get("placeholder", u"例如: 3.0, 5.0, 10.0"))
            widget.textChanged.connect(self.on_config_changed)
            return widget

        if field_type == "path_file":
            edit = QtWidgets.QLineEdit()
            edit.setPlaceholderText(spec.get("placeholder", u"选择一个 JSON 文件"))
            button = QtWidgets.QPushButton(u"浏览...")
            button.clicked.connect(lambda: self.choose_file(edit, u"选择 JSON 文件", u"JSON Files (*.json);;All Files (*)"))
            edit.textChanged.connect(self.on_config_changed)
            container = self.browse_row(edit, button)
            container._line_edit = edit  # noqa
            container._browse_button = button  # noqa
            return container

        widget = QtWidgets.QLineEdit()
        if spec.get("placeholder"):
            widget.setPlaceholderText(spec["placeholder"])
        widget.textChanged.connect(self.on_config_changed)
        return widget

    def apply_field_help(self, widget, spec):
        help_text = ensure_text(spec.get("help", u"")).strip()
        if not help_text:
            return
        widget.setToolTip(help_text)
        if hasattr(widget, "_line_edit"):
            widget._line_edit.setToolTip(help_text)
        if hasattr(widget, "_browse_button"):
            widget._browse_button.setToolTip(help_text)

    def register_config_widget(self, kind, key, widget):
        self._config_sender_map[widget] = (kind, key)
        if hasattr(widget, "_line_edit"):
            self._config_sender_map[widget._line_edit] = (kind, key)

    def browse_row(self, edit_widget, button_widget):
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(edit_widget, 1)
        layout.addWidget(button_widget)
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        return widget

    def wrap_checkbox(self, checkbox):
        wrapper = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(checkbox)
        layout.addStretch(1)
        return wrapper

    def connect_preview_updates(self, widgets):
        for widget in widgets:
            widget.textChanged.connect(self.update_command_preview)

    def choose_file(self, target_edit, title, filter_text):
        path, _selected = QtWidgets.QFileDialog.getOpenFileName(self, title, target_edit.text(), filter_text)
        if path:
            target_edit.setText(path)

    def choose_save_file(self, target_edit, title, filter_text):
        path, _selected = QtWidgets.QFileDialog.getSaveFileName(self, title, target_edit.text(), filter_text)
        if path:
            target_edit.setText(path)

    def choose_directory(self, target_edit):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, u"选择目录", target_edit.text())
        if path:
            target_edit.setText(path)

    def config_widget_value(self, widget, field_type):
        if field_type == "bool":
            return bool(widget.isChecked())
        if field_type == "int":
            return int(widget.value())
        if field_type == "double":
            return float(widget.value())
        if field_type == "combo":
            return widget.currentData()
        if field_type == "float_list":
            return parse_number_list_text(widget.text())
        if field_type == "path_file":
            return ensure_text(widget._line_edit.text()).strip()
        return ensure_text(widget.text()).strip()

    def set_config_widget_value(self, widget, field_type, value):
        if field_type == "bool":
            widget.setChecked(bool(value))
            return
        if field_type == "int":
            try:
                widget.setValue(int(value))
            except Exception:
                widget.setValue(0)
            return
        if field_type == "double":
            try:
                widget.setValue(float(value))
            except Exception:
                widget.setValue(0.0)
            return
        if field_type == "combo":
            self.set_combo_by_data(widget, value)
            return
        if field_type == "float_list":
            widget.setText(number_list_to_text(value if isinstance(value, list) else []))
            return
        if field_type == "path_file":
            widget._line_edit.setText(ensure_text(value))
            return
        widget.setText(ensure_text(value))

    def config_field_specs(self, kind):
        if kind == "quadwild":
            return QUADWILD_FORM_FIELDS
        if kind == "qfp":
            return QFP_FORM_FIELDS
        if kind == "flow_solver":
            return FLOW_SOLVER_FORM_FIELDS
        return SATSUMA_FORM_FIELDS

    def config_widgets(self, kind):
        if kind == "quadwild":
            return self.quadwild_form_widgets
        if kind == "qfp":
            return self.qfp_form_widgets
        if kind == "flow_solver":
            return self.flow_solver_form_widgets
        return self.satsuma_form_widgets

    def config_defaults(self, kind):
        if kind == "quadwild":
            return dict(QUADWILD_DEFAULTS)
        if kind == "qfp":
            return dict(QFP_DEFAULTS)
        if kind == "flow_solver":
            return deep_copy_json_dict(FLOW_SOLVER_DEFAULTS)
        return deep_copy_json_dict(SATSUMA_DEFAULTS)

    def config_path_edit(self, kind):
        if kind == "quadwild":
            return self.quadwild_config_path_edit
        if kind == "qfp":
            return self.qfp_config_path_edit
        if kind == "flow_solver":
            return self.flow_solver_config_path_edit
        return self.satsuma_solver_config_path_edit

    def config_preview_widget(self, kind):
        if kind == "quadwild":
            return self.quadwild_json_preview
        if kind == "qfp":
            return self.qfp_json_preview
        if kind == "flow_solver":
            return self.flow_solver_json_preview
        return self.satsuma_solver_json_preview

    def load_config_data_into_form(self, kind, data):
        defaults = deep_copy_json_dict(self.config_defaults(kind))
        defaults.update(data or {})
        widgets = self.config_widgets(kind)
        for spec in self.config_field_specs(kind):
            self.set_config_widget_value(widgets[spec["key"]], spec["type"], nested_get(defaults, spec["key"]))
        if kind in ("quadwild", "qfp"):
            self.sync_all_shared_main_fields(kind)
        self.refresh_json_previews()
        self.update_command_preview()

    def collect_config_data(self, kind):
        data = {}
        widgets = self.config_widgets(kind)
        for spec in self.config_field_specs(kind):
            nested_set(data, spec["key"], self.config_widget_value(widgets[spec["key"]], spec["type"]))
        return data

    def collect_config_text(self, kind):
        return json.dumps(self.collect_config_data(kind), indent=2, ensure_ascii=False, sort_keys=False)

    def external_config_reference(self, kind):
        if kind == "flow_solver":
            return ensure_text(self.flow_solver_config_path_edit.text()).strip() or default_flow_solver_config()
        return ensure_text(self.satsuma_solver_config_path_edit.text()).strip() or default_satsuma_config()

    def collect_main_config_data(self, kind):
        data = self.collect_config_data(kind)
        data["flow_config_filename"] = self.external_config_reference("flow_solver")
        data["satsuma_config_filename"] = self.external_config_reference("satsuma_solver")
        return data

    def load_external_configs_from_main_data(self, data, base_dir):
        flow_ref = ensure_text(data.get("flow_config_filename", "")).strip()
        satsuma_ref = ensure_text(data.get("satsuma_config_filename", "")).strip()
        if flow_ref:
            self.flow_solver_config_path_edit.setText(flow_ref)
            flow_path = resolve_config_reference(flow_ref, base_dir)
            if os.path.isfile(flow_path):
                self.load_config_data_into_form("flow_solver", read_json_file(flow_path, FLOW_SOLVER_DEFAULTS))
        if satsuma_ref:
            self.satsuma_solver_config_path_edit.setText(satsuma_ref)
            satsuma_path = resolve_config_reference(satsuma_ref, base_dir)
            if os.path.isfile(satsuma_path):
                self.load_config_data_into_form("satsuma_solver", read_json_file(satsuma_path, SATSUMA_DEFAULTS))

    def refresh_json_previews(self):
        for kind in ("quadwild", "qfp", "flow_solver", "satsuma_solver"):
            preview = self.config_preview_widget(kind)
            if preview is None:
                continue
            try:
                if kind in ("quadwild", "qfp"):
                    preview.setPlainText(json.dumps(self.collect_main_config_data(kind), indent=2, ensure_ascii=False, sort_keys=False))
                else:
                    preview.setPlainText(self.collect_config_text(kind))
            except Exception as exc:
                preview.setPlainText(u"[配置错误]\n{0}".format(ensure_text(exc)))

    def on_config_changed(self, *_args):
        sender = self.sender()
        if (not self._syncing_shared_config) and sender in self._config_sender_map:
            kind, key = self._config_sender_map[sender]
            if kind in ("quadwild", "qfp") and key in SHARED_MAIN_CONFIG_KEYS:
                self.sync_shared_main_field(kind, key)
        self.refresh_json_previews()
        self.update_command_preview()

    def sync_shared_main_field(self, source_kind, key):
        target_kind = "qfp" if source_kind == "quadwild" else "quadwild"
        self._syncing_shared_config = True
        try:
            source_widget = self.config_widgets(source_kind)[key]
            target_widget = self.config_widgets(target_kind)[key]
            field_type = None
            for spec in self.config_field_specs(source_kind):
                if spec["key"] == key:
                    field_type = spec["type"]
                    break
            if field_type is None:
                return
            value = self.config_widget_value(source_widget, field_type)
            target_value = self.config_widget_value(target_widget, field_type)
            if value != target_value:
                self.set_config_widget_value(target_widget, field_type, value)
        finally:
            self._syncing_shared_config = False

    def sync_all_shared_main_fields(self, source_kind):
        for key in SHARED_MAIN_CONFIG_KEYS:
            self.sync_shared_main_field(source_kind, key)

    def load_config_from_file(self, kind, title):
        path_edit = self.config_path_edit(kind)
        path, _selected = QtWidgets.QFileDialog.getOpenFileName(self, title, path_edit.text(), u"JSON Files (*.json);;All Files (*)")
        if not path:
            return
        try:
            data = read_json_file(path, self.config_defaults(kind))
            path_edit.setText(path)
            if kind in ("quadwild", "qfp"):
                self.load_external_configs_from_main_data(data, os.path.dirname(path))
            self.load_config_data_into_form(kind, data)
            self.append_log(u"[INFO] 已加载配置文件: {0}".format(path))
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, u"加载失败", ensure_text(exc))

    def save_config_to_file(self, kind):
        path_edit = self.config_path_edit(kind)
        current_path = ensure_text(path_edit.text()).strip()
        default_target = current_path or default_prep_config()
        if kind == "qfp":
            default_target = current_path or default_main_config()
        elif kind == "flow_solver":
            default_target = current_path or default_flow_solver_config()
        elif kind == "satsuma_solver":
            default_target = current_path or default_satsuma_config()
        path, _selected = QtWidgets.QFileDialog.getSaveFileName(
            self,
            u"保存 JSON 配置",
            default_target,
            u"JSON Files (*.json);;All Files (*)"
        )
        if not path:
            return
        try:
            if kind in ("quadwild", "qfp"):
                write_json_file(path, self.collect_main_config_data(kind))
            else:
                write_json_file(path, self.collect_config_data(kind))
            path_edit.setText(path)
            self.append_log(u"[INFO] 已保存配置文件: {0}".format(path))
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, u"保存失败", ensure_text(exc))

    def reset_config_to_defaults(self, kind, default_data):
        self.load_config_data_into_form(kind, default_data)
        self.append_log(u"[INFO] 已恢复 {0} 默认配置。".format(kind))

    def update_runtime_status(self, state, detail):
        self.status_value.setText(ensure_text(state))
        self.stage_value.setText(ensure_text(detail))

    def on_job_name_edited(self, _text):
        self.job_name_manually_edited = True

    def sync_quadwild_input_widgets(self, source_text):
        if self._syncing_quadwild_input:
            return
        self._syncing_quadwild_input = True
        try:
            if ensure_text(self.quadwild_input_edit.text()) != ensure_text(source_text):
                self.quadwild_input_edit.setText(ensure_text(source_text))
            if ensure_text(self.quadwild_input_general_edit.text()) != ensure_text(source_text):
                self.quadwild_input_general_edit.setText(ensure_text(source_text))
        finally:
            self._syncing_quadwild_input = False
        self.auto_refresh_job_name_if_needed()
        self.update_command_preview()

    def current_primary_input_path(self):
        workflow = ensure_text(self.workflow_combo.currentData())
        if workflow == "quad_from_patches_only":
            return ensure_text(self.qfp_input_edit.text()).strip()
        return ensure_text(self.quadwild_input_edit.text()).strip()

    def regenerate_job_name(self):
        workflow = ensure_text(self.workflow_combo.currentData())
        self.job_name_manually_edited = False
        self.job_name_edit.setText(generate_job_name(workflow, self.current_primary_input_path()))

    def auto_refresh_job_name_if_needed(self):
        if self.job_name_manually_edited and ensure_text(self.job_name_edit.text()).strip():
            return
        self.regenerate_job_name()

    def apply_defaults_if_needed(self):
        if not self.output_root_edit.text().strip():
            self.output_root_edit.setText(default_output_root())
        if not self.quadwild_binary_edit.text().strip():
            self.quadwild_binary_edit.setText(preferred_repo_binary("quadwild.exe"))
        if not self.qfp_binary_edit.text().strip():
            self.qfp_binary_edit.setText(preferred_repo_binary("quad_from_patches.exe"))
        if not self.viz_binary_edit.text().strip():
            self.viz_binary_edit.setText(preferred_repo_binary("viz_mesh_results.exe"))
        if not self.quadwild_config_path_edit.text().strip():
            self.quadwild_config_path_edit.setText(default_prep_config())
        if not self.qfp_config_path_edit.text().strip():
            self.qfp_config_path_edit.setText(default_main_config())
        if not self.flow_solver_config_path_edit.text().strip():
            self.flow_solver_config_path_edit.setText(default_flow_solver_config())
        if not self.satsuma_solver_config_path_edit.text().strip():
            self.satsuma_solver_config_path_edit.setText(default_satsuma_config())
        if not self.job_name_edit.text().strip():
            self.regenerate_job_name()

    def default_settings_dict(self):
        return {
            "workflow": "full_pipeline",
            "output_root": default_output_root(),
            "job_name": text_type(""),
            "quadwild_binary": preferred_repo_binary("quadwild.exe"),
            "quad_from_patches_binary": preferred_repo_binary("quad_from_patches.exe"),
            "viz_mesh_results_binary": preferred_repo_binary("viz_mesh_results.exe"),
            "quadwild_input_mesh": text_type(""),
            "quad_from_patches_input_mesh": text_type(""),
            "enable_viz_export": False,
            "quadwild_stop_step": "3",
            "sharp_file": text_type(""),
            "rosy_file": text_type(""),
            "quadwild_extra_args": text_type(""),
            "quad_from_patches_num": "0",
            "stats_json": "run_stats.json",
            "quad_from_patches_extra_args": text_type(""),
            "quadwild_config_path": default_prep_config(),
            "quad_from_patches_config_path": default_main_config(),
            "flow_solver_config_path": default_flow_solver_config(),
            "satsuma_solver_config_path": default_satsuma_config(),
            "quadwild_config_data": dict(QUADWILD_DEFAULTS),
            "quad_from_patches_config_data": dict(QFP_DEFAULTS),
            "flow_solver_config_data": deep_copy_json_dict(FLOW_SOLVER_DEFAULTS),
            "satsuma_solver_config_data": deep_copy_json_dict(SATSUMA_DEFAULTS)
        }

    def migrate_legacy_config_data(self, data, text_key, default_values):
        if text_key not in data:
            return dict(default_values)
        try:
            parsed = json.loads(ensure_text(data.get(text_key, "")))
            if isinstance(parsed, dict):
                result = dict(default_values)
                result.update(parsed)
                return result
        except Exception:
            pass
        return dict(default_values)

    def load_settings(self):
        path = settings_path()
        data = {}
        if os.path.exists(path):
            try:
                data = json.loads(read_text_file(path))
            except Exception:
                data = {}
        defaults = self.default_settings_dict()
        defaults.update(data)
        data = defaults

        self.set_combo_by_data(self.workflow_combo, data.get("workflow", "full_pipeline"))
        self.output_root_edit.setText(ensure_text(data.get("output_root", "")))
        self.job_name_edit.setText(ensure_text(data.get("job_name", "")))
        self.job_name_manually_edited = bool(ensure_text(data.get("job_name", "")).strip())
        self.quadwild_binary_edit.setText(ensure_text(data.get("quadwild_binary", "")))
        self.qfp_binary_edit.setText(ensure_text(data.get("quad_from_patches_binary", "")))
        self.viz_binary_edit.setText(ensure_text(data.get("viz_mesh_results_binary", "")))
        self.enable_viz_checkbox.setChecked(bool(data.get("enable_viz_export", False)))
        self.quadwild_input_edit.setText(ensure_text(data.get("quadwild_input_mesh", "")))
        self.quadwild_input_general_edit.setText(ensure_text(data.get("quadwild_input_mesh", "")))
        self.qfp_input_edit.setText(ensure_text(data.get("quad_from_patches_input_mesh", "")))
        self.set_combo_by_data(self.stop_step_combo, data.get("quadwild_stop_step", "3"))
        self.sharp_edit.setText(ensure_text(data.get("sharp_file", "")))
        self.rosy_edit.setText(ensure_text(data.get("rosy_file", "")))
        self.quadwild_extra_args_edit.setText(ensure_text(data.get("quadwild_extra_args", "")))
        self.qfp_extra_args_edit.setText(ensure_text(data.get("quad_from_patches_extra_args", "")))
        self.stats_json_edit.setText(ensure_text(data.get("stats_json", "")))
        self.quadwild_config_path_edit.setText(ensure_text(data.get("quadwild_config_path", "")))
        self.qfp_config_path_edit.setText(ensure_text(data.get("quad_from_patches_config_path", "")))
        self.flow_solver_config_path_edit.setText(ensure_text(data.get("flow_solver_config_path", "")))
        self.satsuma_solver_config_path_edit.setText(ensure_text(data.get("satsuma_solver_config_path", "")))

        quadwild_config_data = data.get("quadwild_config_data")
        if not isinstance(quadwild_config_data, dict):
            quadwild_config_data = self.migrate_legacy_config_data(data, "quadwild_config_text", QUADWILD_DEFAULTS)
        qfp_config_data = data.get("quad_from_patches_config_data")
        if not isinstance(qfp_config_data, dict):
            qfp_config_data = self.migrate_legacy_config_data(data, "quad_from_patches_config_text", QFP_DEFAULTS)
        flow_solver_config_data = data.get("flow_solver_config_data")
        if not isinstance(flow_solver_config_data, dict):
            flow_solver_config_data = deep_copy_json_dict(FLOW_SOLVER_DEFAULTS)
        satsuma_solver_config_data = data.get("satsuma_solver_config_data")
        if not isinstance(satsuma_solver_config_data, dict):
            satsuma_solver_config_data = deep_copy_json_dict(SATSUMA_DEFAULTS)

        self.load_config_data_into_form("quadwild", quadwild_config_data)
        self.load_config_data_into_form("qfp", qfp_config_data)
        self.load_config_data_into_form("flow_solver", flow_solver_config_data)
        self.load_config_data_into_form("satsuma_solver", satsuma_solver_config_data)

        try:
            self.qfp_num_spin.setValue(int(data.get("quad_from_patches_num", 0)))
        except Exception:
            self.qfp_num_spin.setValue(0)

        self.quadwild_input_edit.textChanged.connect(self.sync_quadwild_input_widgets)
        self.quadwild_input_general_edit.textChanged.connect(self.sync_quadwild_input_widgets)
        self.quadwild_input_edit.textChanged.connect(self.update_command_preview)
        self.quadwild_input_general_edit.textChanged.connect(self.update_command_preview)
        self.qfp_input_edit.textChanged.connect(self.update_command_preview)
        self.sharp_edit.textChanged.connect(self.update_command_preview)
        self.rosy_edit.textChanged.connect(self.update_command_preview)

    def save_settings(self):
        data = self.collect_settings()
        data["process_cwd"] = repo_root()
        write_text_file(settings_path(), json.dumps(data, indent=2, ensure_ascii=False))
        self.append_log(u"[INFO] 已保存界面设置: {0}".format(settings_path()))

    def reset_defaults(self):
        defaults = self.default_settings_dict()
        self.set_combo_by_data(self.workflow_combo, defaults["workflow"])
        self.output_root_edit.setText(defaults["output_root"])
        self.quadwild_binary_edit.setText(defaults["quadwild_binary"])
        self.qfp_binary_edit.setText(defaults["quad_from_patches_binary"])
        self.viz_binary_edit.setText(defaults["viz_mesh_results_binary"])
        self.enable_viz_checkbox.setChecked(bool(defaults["enable_viz_export"]))
        self.sync_quadwild_input_widgets(defaults["quadwild_input_mesh"])
        self.qfp_input_edit.setText(defaults["quad_from_patches_input_mesh"])
        self.set_combo_by_data(self.stop_step_combo, defaults["quadwild_stop_step"])
        self.sharp_edit.setText(defaults["sharp_file"])
        self.rosy_edit.setText(defaults["rosy_file"])
        self.quadwild_extra_args_edit.setText(defaults["quadwild_extra_args"])
        self.qfp_extra_args_edit.setText(defaults["quad_from_patches_extra_args"])
        self.stats_json_edit.setText(defaults["stats_json"])
        self.quadwild_config_path_edit.setText(defaults["quadwild_config_path"])
        self.qfp_config_path_edit.setText(defaults["quad_from_patches_config_path"])
        self.flow_solver_config_path_edit.setText(defaults["flow_solver_config_path"])
        self.satsuma_solver_config_path_edit.setText(defaults["satsuma_solver_config_path"])
        self.load_config_data_into_form("quadwild", defaults["quadwild_config_data"])
        self.load_config_data_into_form("qfp", defaults["quad_from_patches_config_data"])
        self.load_config_data_into_form("flow_solver", defaults["flow_solver_config_data"])
        self.load_config_data_into_form("satsuma_solver", defaults["satsuma_solver_config_data"])
        self.qfp_num_spin.setValue(int(defaults["quad_from_patches_num"]))
        self.job_name_manually_edited = False
        self.regenerate_job_name()
        self.update_mode()
        self.refresh_json_previews()
        self.update_command_preview()
        self.append_log(u"[INFO] 已恢复默认配置。")

    def set_combo_by_data(self, combo, value):
        value = ensure_text(value)
        for index in range(combo.count()):
            if ensure_text(combo.itemData(index)) == value:
                combo.setCurrentIndex(index)
                return

    def update_mode(self):
        workflow = ensure_text(self.workflow_combo.currentData())
        quadwild_enabled = workflow in ("full_pipeline", "quadwild_only")
        qfp_enabled = workflow in ("full_pipeline", "quad_from_patches_only")
        qfp_input_enabled = workflow == "quad_from_patches_only"

        self.stop_step_combo.setEnabled(workflow == "quadwild_only")
        self.qfp_input_edit.setEnabled(qfp_input_enabled)
        self.qfp_input_button.setEnabled(qfp_input_enabled)
        self.qfp_auto_label.setVisible(workflow == "full_pipeline")
        self.tabs.setTabEnabled(1, quadwild_enabled)
        self.tabs.setTabEnabled(2, qfp_enabled)
        self.auto_refresh_job_name_if_needed()
        self.update_command_preview()

    def validate_settings(self, settings):
        workflow = settings["workflow"]
        errors = []

        if not settings["output_root"]:
            errors.append(u"请选择输出根目录。")

        try:
            parse_number_list_text(self.quadwild_form_widgets["callbackTimeLimit"].text())
            parse_number_list_text(self.quadwild_form_widgets["callbackGapLimit"].text())
            parse_number_list_text(self.qfp_form_widgets["callbackTimeLimit"].text())
            parse_number_list_text(self.qfp_form_widgets["callbackGapLimit"].text())
        except Exception:
            errors.append(u"Callback 列表参数格式错误，请使用逗号分隔数字。")

        if workflow in ("full_pipeline", "quadwild_only"):
            if not os.path.isfile(settings["quadwild_binary"]):
                errors.append(u"quadwild 二进制不存在。")
            if not os.path.isfile(settings["quadwild_input_mesh"]):
                errors.append(u"quadwild 输入网格不存在。")
            if settings["sharp_file"] and not os.path.isfile(settings["sharp_file"]):
                errors.append(u".sharp 文件不存在。")
            if settings["rosy_file"] and not os.path.isfile(settings["rosy_file"]):
                errors.append(u".rosy 文件不存在。")
            if settings["enable_viz_export"] and not os.path.isfile(settings["viz_mesh_results_binary"]):
                errors.append(u"viz_mesh_results 二进制不存在。")

        if workflow in ("full_pipeline", "quad_from_patches_only"):
            if not os.path.isfile(settings["quad_from_patches_binary"]):
                errors.append(u"quad_from_patches 二进制不存在。")
            if workflow == "quad_from_patches_only" and not os.path.isfile(settings["quad_from_patches_input_mesh"]):
                errors.append(u"quad_from_patches 输入网格不存在。")
        return errors

    def collect_settings(self):
        workflow = ensure_text(self.workflow_combo.currentData())
        quadwild_config_data = self.collect_main_config_data("quadwild")
        qfp_config_data = self.collect_main_config_data("qfp")
        flow_solver_config_data = self.collect_config_data("flow_solver")
        satsuma_solver_config_data = self.collect_config_data("satsuma_solver")
        return {
            "workflow": workflow,
            "output_root": ensure_text(self.output_root_edit.text()).strip(),
            "job_name": ensure_text(self.job_name_edit.text()).strip() or generate_job_name(workflow, self.current_primary_input_path()),
            "quadwild_binary_requested": ensure_text(self.quadwild_binary_edit.text()).strip(),
            "quad_from_patches_binary_requested": ensure_text(self.qfp_binary_edit.text()).strip(),
            "viz_mesh_results_binary_requested": ensure_text(self.viz_binary_edit.text()).strip(),
            "quadwild_binary": normalize_binary_path(self.quadwild_binary_edit.text(), "quadwild.exe"),
            "quad_from_patches_binary": normalize_binary_path(self.qfp_binary_edit.text(), "quad_from_patches.exe"),
            "viz_mesh_results_binary": normalize_binary_path(self.viz_binary_edit.text(), "viz_mesh_results.exe"),
            "quadwild_input_mesh": ensure_text(self.quadwild_input_edit.text()).strip(),
            "quad_from_patches_input_mesh": ensure_text(self.qfp_input_edit.text()).strip(),
            "enable_viz_export": self.enable_viz_checkbox.isChecked(),
            "quadwild_stop_step": ensure_text(self.stop_step_combo.currentData()),
            "sharp_file": ensure_text(self.sharp_edit.text()).strip(),
            "rosy_file": ensure_text(self.rosy_edit.text()).strip(),
            "quadwild_extra_args": ensure_text(self.quadwild_extra_args_edit.text()).strip(),
            "quad_from_patches_num": text_type(self.qfp_num_spin.value()),
            "stats_json": ensure_text(self.stats_json_edit.text()).strip(),
            "quad_from_patches_extra_args": ensure_text(self.qfp_extra_args_edit.text()).strip(),
            "quadwild_config_path": ensure_text(self.quadwild_config_path_edit.text()).strip(),
            "quad_from_patches_config_path": ensure_text(self.qfp_config_path_edit.text()).strip(),
            "flow_solver_config_path": ensure_text(self.flow_solver_config_path_edit.text()).strip(),
            "satsuma_solver_config_path": ensure_text(self.satsuma_solver_config_path_edit.text()).strip(),
            "quadwild_config_data": quadwild_config_data,
            "quad_from_patches_config_data": qfp_config_data,
            "flow_solver_config_data": flow_solver_config_data,
            "satsuma_solver_config_data": satsuma_solver_config_data,
            "quadwild_config_text": json.dumps(quadwild_config_data, indent=2, ensure_ascii=False, sort_keys=False),
            "quad_from_patches_config_text": json.dumps(qfp_config_data, indent=2, ensure_ascii=False, sort_keys=False),
            "flow_solver_config_text": json.dumps(flow_solver_config_data, indent=2, ensure_ascii=False, sort_keys=False),
            "satsuma_solver_config_text": json.dumps(satsuma_solver_config_data, indent=2, ensure_ascii=False, sort_keys=False),
            "process_cwd": repo_root()
        }

    def build_preview_lines(self, settings):
        lines = [u"工作目录: {0}".format(settings["process_cwd"])]
        lines.append(u"输出根目录: {0}".format(settings["output_root"] or u"<未设置>"))
        lines.append(u"任务目录名: {0}".format(settings["job_name"]))
        lines.append(u"Qt 绑定: {0}".format(QT_BINDING))

        workflow = settings["workflow"]
        if workflow in ("full_pipeline", "quadwild_only"):
            quadwild_command = [
                settings["quadwild_binary"] or u"<quadwild.exe>",
                u"<工作目录中的输入网格副本>",
                settings["quadwild_stop_step"] if workflow == "quadwild_only" else u"2",
                u"<工作目录中的 quadwild_config.json>"
            ]
            if settings["sharp_file"]:
                quadwild_command.append(u"<复制后的 .sharp>")
            if settings["rosy_file"]:
                quadwild_command.append(u"<复制后的 .rosy>")
            quadwild_command.extend(split_extra_args(settings["quadwild_extra_args"]))
            lines.append(u"")
            lines.append(u"[quadwild]")
            lines.append(command_to_text(quadwild_command))

            if settings["enable_viz_export"]:
                if workflow == "full_pipeline" or settings["quadwild_stop_step"] in ("2", "3"):
                    viz_command = [
                        settings["viz_mesh_results_binary"] or u"<viz_mesh_results.exe>",
                        u"<工作目录中的 *_rem.obj>"
                    ]
                    lines.append(u"")
                    lines.append(u"[viz_mesh_results]")
                    lines.append(command_to_text(viz_command))
                else:
                    lines.append(u"")
                    lines.append(u"[viz_mesh_results]")
                    lines.append(u"<已启用，但当前会在 step 1 停止，因此不会执行>")

        if workflow == "full_pipeline":
            qfp_command = [
                settings["quad_from_patches_binary"] or u"<quad_from_patches.exe>",
                u"<工作目录中的 *_rem_p0.obj>",
                settings["quad_from_patches_num"],
                u"<工作目录中的 quad_from_patches_config.json>"
            ]
            if settings["stats_json"]:
                qfp_command.append(settings["stats_json"])
            qfp_command.extend(split_extra_args(settings["quad_from_patches_extra_args"]))
            lines.append(u"")
            lines.append(u"[quad_from_patches]")
            lines.append(command_to_text(qfp_command))

        if workflow == "quad_from_patches_only":
            qfp_command = [
                settings["quad_from_patches_binary"] or u"<quad_from_patches.exe>",
                u"<工作目录中的输入网格副本>",
                settings["quad_from_patches_num"],
                u"<工作目录中的 quad_from_patches_config.json>"
            ]
            if settings["stats_json"]:
                qfp_command.append(settings["stats_json"])
            qfp_command.extend(split_extra_args(settings["quad_from_patches_extra_args"]))
            lines.append(u"")
            lines.append(u"[quad_from_patches]")
            lines.append(command_to_text(qfp_command))

        lines.append(u"")
        lines.append(u"[quadwild_config.json]")
        lines.append(settings["quadwild_config_text"][:1200] or u"<空>")
        lines.append(u"")
        lines.append(u"[quad_from_patches_config.json]")
        lines.append(settings["quad_from_patches_config_text"][:1200] or u"<空>")
        lines.append(u"")
        lines.append(u"[flow_solver_config.json]")
        lines.append(settings["flow_solver_config_text"][:1200] or u"<空>")
        lines.append(u"")
        lines.append(u"[satsuma_solver_config.json]")
        lines.append(settings["satsuma_solver_config_text"][:1200] or u"<空>")
        return lines

    def update_command_preview(self):
        try:
            settings = self.collect_settings()
            self.preview_text.setPlainText(u"\n".join(self.build_preview_lines(settings)))
        except Exception as exc:
            self.preview_text.setPlainText(u"[预览失败]\n{0}".format(ensure_text(exc)))

    def append_log(self, message):
        self.log_text.appendPlainText(ensure_text(message))

    def set_running(self, running):
        self.start_button.setEnabled(not running)
        self.cancel_button.setEnabled(running)
        self.reset_button.setEnabled(not running)
        if running:
            self.progress_bar.setRange(0, 0)
        else:
            self.progress_bar.setRange(0, 1)
            self.progress_bar.setValue(0)

    def start_workflow(self):
        try:
            settings = self.collect_settings()
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self, u"参数错误", ensure_text(exc))
            return
        errors = self.validate_settings(settings)
        if errors:
            QtWidgets.QMessageBox.warning(self, u"参数不完整", u"\n".join(errors))
            return

        self.save_settings()
        self.log_text.clear()
        self.last_workspace = text_type("")
        self.open_output_button.setEnabled(False)
        self.set_running(True)
        self.update_runtime_status(u"准备中", u"初始化后台任务")
        self.append_log(u"[INFO] 准备开始执行。")
        if settings["workflow"] in ("full_pipeline", "quadwild_only") and settings["quadwild_binary"] != settings["quadwild_binary_requested"]:
            self.append_log(u"[INFO] quadwild 二进制已自动切换为最新可用版本: {0}".format(settings["quadwild_binary"]))
        if settings["workflow"] in ("full_pipeline", "quad_from_patches_only") and settings["quad_from_patches_binary"] != settings["quad_from_patches_binary_requested"]:
            self.append_log(u"[INFO] quad_from_patches 二进制已自动切换为最新可用版本: {0}".format(settings["quad_from_patches_binary"]))
        if settings["enable_viz_export"] and settings["viz_mesh_results_binary"] != settings["viz_mesh_results_binary_requested"]:
            self.append_log(u"[INFO] viz_mesh_results 二进制已自动切换为最新可用版本: {0}".format(settings["viz_mesh_results_binary"]))

        self.worker_thread = QtCore.QThread(self)
        self.worker = ProcessWorker(settings)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.log_message.connect(self.append_log)
        self.worker.status_changed.connect(self.update_runtime_status)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()

    def cancel_workflow(self):
        if self.worker is not None:
            self.worker.cancel()
            self.update_runtime_status(u"正在中断", u"等待当前进程退出")

    def on_worker_finished(self, success, workspace, state):
        self.set_running(False)
        self.last_workspace = ensure_text(workspace)
        self.workspace_value.setText(self.last_workspace or u"-")
        if workspace:
            self.open_output_button.setEnabled(True)

        if state == "success":
            self.append_log(u"[INFO] 任务完成。输出目录: {0}".format(self.last_workspace))
            QtWidgets.QMessageBox.information(self, u"执行完成", u"处理完成。\n输出目录：\n{0}".format(self.last_workspace))
        elif state == "canceled":
            self.append_log(u"[WARN] 任务已中断。")
            QtWidgets.QMessageBox.warning(self, u"已中断", u"任务已被用户中断。")
        else:
            self.append_log(u"[ERROR] 任务失败。")
            QtWidgets.QMessageBox.critical(self, u"执行失败", u"处理失败，请检查日志。")

        self.worker = None
        self.worker_thread = None

    def open_output_directory(self):
        if not self.last_workspace:
            return
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(self.last_workspace))


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = QuadWildWindow()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
