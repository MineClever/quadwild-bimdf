#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import datetime
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


QUADWILD_DEFAULTS = read_json_file(default_prep_config(), {})
QFP_DEFAULTS = read_json_file(default_main_config(), {})


QUADWILD_FORM_FIELDS = [
    {"key": "do_remesh", "label": u"执行重网格", "type": "bool"},
    {"key": "sharp_feature_thr", "label": u"锐边阈值", "type": "double", "decimals": 4, "minimum": -99999.0, "maximum": 99999.0},
    {"key": "alpha", "label": u"Alpha", "type": "double", "decimals": 6, "minimum": 0.0, "maximum": 99999.0},
    {"key": "scaleFact", "label": u"Scale Factor", "type": "double", "decimals": 6, "minimum": 0.0, "maximum": 99999.0},
    {"key": "fixedChartClusters", "label": u"Fixed Chart Clusters", "type": "int", "minimum": 0, "maximum": 1000000},
    {"key": "ilpMethod", "label": u"ILP 方法", "type": "combo", "choices": [(0, u"ABS"), (1, u"Least Squares")]},
    {"key": "timeLimit", "label": u"Time Limit", "type": "double", "decimals": 3, "minimum": 0.0, "maximum": 999999.0},
    {"key": "gapLimit", "label": u"Gap Limit", "type": "double", "decimals": 9, "minimum": 0.0, "maximum": 999999.0},
    {"key": "minimumGap", "label": u"Minimum Gap", "type": "double", "decimals": 6, "minimum": 0.0, "maximum": 999999.0},
    {"key": "callbackTimeLimit", "label": u"Callback Time Limit", "type": "float_list"},
    {"key": "callbackGapLimit", "label": u"Callback Gap Limit", "type": "float_list"},
    {"key": "isometry", "label": u"Isometry", "type": "bool"},
    {"key": "regularityQuadrilaterals", "label": u"Quadrilateral Regularity", "type": "bool"},
    {"key": "regularityNonQuadrilaterals", "label": u"Non-Quad Regularity", "type": "bool"},
    {"key": "regularityNonQuadrilateralsWeight", "label": u"Non-Quad Regularity Weight", "type": "double", "decimals": 6, "minimum": 0.0, "maximum": 999999.0},
    {"key": "alignSingularities", "label": u"Align Singularities", "type": "bool"},
    {"key": "alignSingularitiesWeight", "label": u"Align Singularities Weight", "type": "double", "decimals": 6, "minimum": 0.0, "maximum": 999999.0},
    {"key": "repeatLosingConstraintsIterations", "label": u"Repeat Losing Iterations", "type": "bool"},
    {"key": "repeatLosingConstraintsQuads", "label": u"Repeat Losing Quads", "type": "bool"},
    {"key": "repeatLosingConstraintsNonQuads", "label": u"Repeat Losing Non-Quads", "type": "bool"},
    {"key": "repeatLosingConstraintsAlign", "label": u"Repeat Losing Align", "type": "bool"},
    {"key": "hardParityConstraint", "label": u"Hard Parity Constraint", "type": "bool"},
    {"key": "chartSmoothingIterations", "label": u"Chart Smoothing Iterations", "type": "int", "minimum": 0, "maximum": 1000000},
    {"key": "quadrangulationFixedSmoothingIterations", "label": u"Fixed Smoothing Iterations", "type": "int", "minimum": 0, "maximum": 1000000},
    {"key": "quadrangulationNonFixedSmoothingIterations", "label": u"Non-Fixed Smoothing Iterations", "type": "int", "minimum": 0, "maximum": 1000000},
    {"key": "feasibilityFix", "label": u"Feasibility Fix", "type": "bool"},
    {"key": "useFlowSolver", "label": u"Use Flow Solver", "type": "bool"},
    {"key": "flow_config_filename", "label": u"Flow Config JSON", "type": "path_file"},
    {"key": "satsuma_config_filename", "label": u"Satsuma Config JSON", "type": "path_file"},
]


QFP_FORM_FIELDS = [
    {"key": "alpha", "label": u"Alpha", "type": "double", "decimals": 6, "minimum": 0.0, "maximum": 99999.0},
    {"key": "scaleFact", "label": u"Scale Factor", "type": "double", "decimals": 6, "minimum": 0.0, "maximum": 99999.0},
    {"key": "fixedChartClusters", "label": u"Fixed Chart Clusters", "type": "int", "minimum": 0, "maximum": 1000000},
    {"key": "ilpMethod", "label": u"ILP 方法", "type": "combo", "choices": [(0, u"ABS"), (1, u"Least Squares")]},
    {"key": "timeLimit", "label": u"Time Limit", "type": "double", "decimals": 3, "minimum": 0.0, "maximum": 999999.0},
    {"key": "gapLimit", "label": u"Gap Limit", "type": "double", "decimals": 9, "minimum": 0.0, "maximum": 999999.0},
    {"key": "minimumGap", "label": u"Minimum Gap", "type": "double", "decimals": 6, "minimum": 0.0, "maximum": 999999.0},
    {"key": "callbackTimeLimit", "label": u"Callback Time Limit", "type": "float_list"},
    {"key": "callbackGapLimit", "label": u"Callback Gap Limit", "type": "float_list"},
    {"key": "isometry", "label": u"Isometry", "type": "bool"},
    {"key": "regularityQuadrilaterals", "label": u"Quadrilateral Regularity", "type": "bool"},
    {"key": "regularityNonQuadrilaterals", "label": u"Non-Quad Regularity", "type": "bool"},
    {"key": "regularityNonQuadrilateralsWeight", "label": u"Non-Quad Regularity Weight", "type": "double", "decimals": 6, "minimum": 0.0, "maximum": 999999.0},
    {"key": "alignSingularities", "label": u"Align Singularities", "type": "bool"},
    {"key": "alignSingularitiesWeight", "label": u"Align Singularities Weight", "type": "double", "decimals": 6, "minimum": 0.0, "maximum": 999999.0},
    {"key": "repeatLosingConstraintsIterations", "label": u"Repeat Losing Iterations", "type": "bool"},
    {"key": "repeatLosingConstraintsQuads", "label": u"Repeat Losing Quads", "type": "bool"},
    {"key": "repeatLosingConstraintsNonQuads", "label": u"Repeat Losing Non-Quads", "type": "bool"},
    {"key": "repeatLosingConstraintsAlign", "label": u"Repeat Losing Align", "type": "bool"},
    {"key": "hardParityConstraint", "label": u"Hard Parity Constraint", "type": "bool"},
    {"key": "useFlowSolver", "label": u"Use Flow Solver", "type": "bool"},
    {"key": "flow_config_filename", "label": u"Flow Config JSON", "type": "path_file"},
    {"key": "satsuma_config_filename", "label": u"Satsuma Config JSON", "type": "path_file"},
]


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

        staged_quadwild_config = os.path.join(workspace, "quadwild_config.json")
        staged_qfp_config = os.path.join(workspace, "quad_from_patches_config.json")
        write_text_file(staged_quadwild_config, self._settings["quadwild_config_text"])
        write_text_file(staged_qfp_config, self._settings["quad_from_patches_config_text"])

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
        self.quadwild_form_widgets = {}
        self.qfp_form_widgets = {}
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
        binary_form.addRow(u"quadwild.exe", self.browse_row(self.quadwild_binary_edit, self.quadwild_binary_button))
        binary_form.addRow(u"quad_from_patches.exe", self.browse_row(self.qfp_binary_edit, self.qfp_binary_button))
        layout.addWidget(binary_group)

        overview_input_group = QtWidgets.QGroupBox(u"QuadWild 快速输入")
        overview_form = QtWidgets.QFormLayout(overview_input_group)
        self.quadwild_input_general_edit = QtWidgets.QLineEdit()
        self.quadwild_input_general_button = QtWidgets.QPushButton(u"浏览...")
        overview_form.addRow(u"输入网格", self.browse_row(self.quadwild_input_general_edit, self.quadwild_input_general_button))
        layout.addWidget(overview_input_group)
        layout.addStretch(1)

        self.workflow_combo.currentIndexChanged.connect(self.update_mode)
        self.output_root_button.clicked.connect(lambda: self.choose_directory(self.output_root_edit))
        self.job_name_generate_button.clicked.connect(self.regenerate_job_name)
        self.quadwild_binary_button.clicked.connect(lambda: self.choose_file(self.quadwild_binary_edit, u"选择 quadwild 可执行文件", u"Executable (*.exe);;All Files (*)"))
        self.qfp_binary_button.clicked.connect(lambda: self.choose_file(self.qfp_binary_edit, u"选择 quad_from_patches 可执行文件", u"Executable (*.exe);;All Files (*)"))
        self.quadwild_input_general_button.clicked.connect(lambda: self.choose_file(self.quadwild_input_general_edit, u"选择 QuadWild 输入网格", u"Mesh Files (*.obj *.ply);;All Files (*)"))
        self.connect_preview_updates([self.output_root_edit, self.job_name_edit, self.quadwild_binary_edit, self.qfp_binary_edit])
        return tab

    def build_quadwild_tab(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)

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
        form_layout = QtWidgets.QFormLayout(form_container)
        form_layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)

        widget_map = {}
        for spec in field_specs:
            widget = self.create_config_field_widget(kind, spec)
            widget_map[spec["key"]] = widget
            form_layout.addRow(spec["label"], widget if spec["type"] != "bool" else self.wrap_checkbox(widget))

        if kind == "quadwild":
            self.quadwild_form_widgets = widget_map
        else:
            self.qfp_form_widgets = widget_map

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
        else:
            self.qfp_json_preview = preview

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
            widget.setPlaceholderText(u"例如: 3.0, 5.0, 10.0")
            widget.textChanged.connect(self.on_config_changed)
            return widget

        if field_type == "path_file":
            edit = QtWidgets.QLineEdit()
            button = QtWidgets.QPushButton(u"浏览...")
            button.clicked.connect(lambda: self.choose_file(edit, u"选择 JSON 文件", u"JSON Files (*.json);;All Files (*)"))
            edit.textChanged.connect(self.on_config_changed)
            container = self.browse_row(edit, button)
            container._line_edit = edit  # noqa
            return container

        widget = QtWidgets.QLineEdit()
        widget.textChanged.connect(self.on_config_changed)
        return widget

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
        return QFP_FORM_FIELDS

    def config_widgets(self, kind):
        if kind == "quadwild":
            return self.quadwild_form_widgets
        return self.qfp_form_widgets

    def config_defaults(self, kind):
        if kind == "quadwild":
            return dict(QUADWILD_DEFAULTS)
        return dict(QFP_DEFAULTS)

    def config_path_edit(self, kind):
        if kind == "quadwild":
            return self.quadwild_config_path_edit
        return self.qfp_config_path_edit

    def config_preview_widget(self, kind):
        if kind == "quadwild":
            return self.quadwild_json_preview
        return self.qfp_json_preview

    def load_config_data_into_form(self, kind, data):
        defaults = self.config_defaults(kind)
        defaults.update(data or {})
        widgets = self.config_widgets(kind)
        for spec in self.config_field_specs(kind):
            self.set_config_widget_value(widgets[spec["key"]], spec["type"], defaults.get(spec["key"]))
        self.refresh_json_previews()
        self.update_command_preview()

    def collect_config_data(self, kind):
        data = {}
        widgets = self.config_widgets(kind)
        for spec in self.config_field_specs(kind):
            data[spec["key"]] = self.config_widget_value(widgets[spec["key"]], spec["type"])
        return data

    def collect_config_text(self, kind):
        return json.dumps(self.collect_config_data(kind), indent=2, ensure_ascii=False, sort_keys=False)

    def refresh_json_previews(self):
        for kind in ("quadwild", "qfp"):
            preview = self.config_preview_widget(kind)
            try:
                preview.setPlainText(self.collect_config_text(kind))
            except Exception as exc:
                preview.setPlainText(u"[配置错误]\n{0}".format(ensure_text(exc)))

    def on_config_changed(self, *_args):
        self.refresh_json_previews()
        self.update_command_preview()

    def load_config_from_file(self, kind, title):
        path_edit = self.config_path_edit(kind)
        path, _selected = QtWidgets.QFileDialog.getOpenFileName(self, title, path_edit.text(), u"JSON Files (*.json);;All Files (*)")
        if not path:
            return
        try:
            data = read_json_file(path, self.config_defaults(kind))
            path_edit.setText(path)
            self.load_config_data_into_form(kind, data)
            self.append_log(u"[INFO] 已加载配置文件: {0}".format(path))
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, u"加载失败", ensure_text(exc))

    def save_config_to_file(self, kind):
        path_edit = self.config_path_edit(kind)
        current_path = ensure_text(path_edit.text()).strip()
        path, _selected = QtWidgets.QFileDialog.getSaveFileName(
            self,
            u"保存 JSON 配置",
            current_path or default_prep_config(),
            u"JSON Files (*.json);;All Files (*)"
        )
        if not path:
            return
        try:
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
        if not self.quadwild_config_path_edit.text().strip():
            self.quadwild_config_path_edit.setText(default_prep_config())
        if not self.qfp_config_path_edit.text().strip():
            self.qfp_config_path_edit.setText(default_main_config())
        if not self.job_name_edit.text().strip():
            self.regenerate_job_name()

    def default_settings_dict(self):
        return {
            "workflow": "full_pipeline",
            "output_root": default_output_root(),
            "job_name": text_type(""),
            "quadwild_binary": preferred_repo_binary("quadwild.exe"),
            "quad_from_patches_binary": preferred_repo_binary("quad_from_patches.exe"),
            "quadwild_input_mesh": text_type(""),
            "quad_from_patches_input_mesh": text_type(""),
            "quadwild_stop_step": "3",
            "sharp_file": text_type(""),
            "rosy_file": text_type(""),
            "quadwild_extra_args": text_type(""),
            "quad_from_patches_num": "0",
            "stats_json": "run_stats.json",
            "quad_from_patches_extra_args": text_type(""),
            "quadwild_config_path": default_prep_config(),
            "quad_from_patches_config_path": default_main_config(),
            "quadwild_config_data": dict(QUADWILD_DEFAULTS),
            "quad_from_patches_config_data": dict(QFP_DEFAULTS)
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

        quadwild_config_data = data.get("quadwild_config_data")
        if not isinstance(quadwild_config_data, dict):
            quadwild_config_data = self.migrate_legacy_config_data(data, "quadwild_config_text", QUADWILD_DEFAULTS)
        qfp_config_data = data.get("quad_from_patches_config_data")
        if not isinstance(qfp_config_data, dict):
            qfp_config_data = self.migrate_legacy_config_data(data, "quad_from_patches_config_text", QFP_DEFAULTS)

        self.load_config_data_into_form("quadwild", quadwild_config_data)
        self.load_config_data_into_form("qfp", qfp_config_data)

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
        self.load_config_data_into_form("quadwild", defaults["quadwild_config_data"])
        self.load_config_data_into_form("qfp", defaults["quad_from_patches_config_data"])
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

        if workflow in ("full_pipeline", "quad_from_patches_only"):
            if not os.path.isfile(settings["quad_from_patches_binary"]):
                errors.append(u"quad_from_patches 二进制不存在。")
            if workflow == "quad_from_patches_only" and not os.path.isfile(settings["quad_from_patches_input_mesh"]):
                errors.append(u"quad_from_patches 输入网格不存在。")
        return errors

    def collect_settings(self):
        workflow = ensure_text(self.workflow_combo.currentData())
        quadwild_config_data = self.collect_config_data("quadwild")
        qfp_config_data = self.collect_config_data("qfp")
        return {
            "workflow": workflow,
            "output_root": ensure_text(self.output_root_edit.text()).strip(),
            "job_name": ensure_text(self.job_name_edit.text()).strip() or generate_job_name(workflow, self.current_primary_input_path()),
            "quadwild_binary_requested": ensure_text(self.quadwild_binary_edit.text()).strip(),
            "quad_from_patches_binary_requested": ensure_text(self.qfp_binary_edit.text()).strip(),
            "quadwild_binary": normalize_binary_path(self.quadwild_binary_edit.text(), "quadwild.exe"),
            "quad_from_patches_binary": normalize_binary_path(self.qfp_binary_edit.text(), "quad_from_patches.exe"),
            "quadwild_input_mesh": ensure_text(self.quadwild_input_edit.text()).strip(),
            "quad_from_patches_input_mesh": ensure_text(self.qfp_input_edit.text()).strip(),
            "quadwild_stop_step": ensure_text(self.stop_step_combo.currentData()),
            "sharp_file": ensure_text(self.sharp_edit.text()).strip(),
            "rosy_file": ensure_text(self.rosy_edit.text()).strip(),
            "quadwild_extra_args": ensure_text(self.quadwild_extra_args_edit.text()).strip(),
            "quad_from_patches_num": text_type(self.qfp_num_spin.value()),
            "stats_json": ensure_text(self.stats_json_edit.text()).strip(),
            "quad_from_patches_extra_args": ensure_text(self.qfp_extra_args_edit.text()).strip(),
            "quadwild_config_path": ensure_text(self.quadwild_config_path_edit.text()).strip(),
            "quad_from_patches_config_path": ensure_text(self.qfp_config_path_edit.text()).strip(),
            "quadwild_config_data": quadwild_config_data,
            "quad_from_patches_config_data": qfp_config_data,
            "quadwild_config_text": json.dumps(quadwild_config_data, indent=2, ensure_ascii=False, sort_keys=False),
            "quad_from_patches_config_text": json.dumps(qfp_config_data, indent=2, ensure_ascii=False, sort_keys=False),
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
