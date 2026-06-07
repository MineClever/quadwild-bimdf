#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import datetime
import json
import os
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


def default_release_binary(filename):
    path = os.path.join(repo_root(), "release", "windows", filename)
    if os.path.exists(path):
        return path
    return text_type("")


def default_prep_config():
    return os.path.join(repo_root(), "config", "prep_config", "basic_setup.txt")


def default_main_config():
    return os.path.join(repo_root(), "config", "main_config", "flow_noalign_lemon.txt")


def safe_makedirs(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def split_extra_args(raw_text):
    raw_text = ensure_text(raw_text).strip()
    if not raw_text:
        return []
    try:
        return shlex.split(raw_text)
    except Exception:
        return raw_text.split()


def command_to_text(parts):
    return u" ".join([quote_argument(part) for part in parts])


def quote_argument(value):
    value = ensure_text(value)
    if not value:
        return u'""'
    if u" " in value or u"\t" in value or u"\"" in value:
        return u"\"" + value.replace(u"\"", u"\\\"") + u"\""
    return value


def unique_workspace(output_root, job_name):
    safe_makedirs(output_root)
    candidate = os.path.join(output_root, job_name)
    if not os.path.exists(candidate):
        return candidate

    index = 1
    while True:
        test_path = candidate + "_" + text_type(index)
        if not os.path.exists(test_path):
            return test_path
        index += 1


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


class ProcessWorker(QtCore.QObject):
    log_message = QtCore.Signal(str)
    finished = QtCore.Signal(bool, str)

    def __init__(self, settings):
        QtCore.QObject.__init__(self)
        self._settings = settings

    def emit_log(self, message):
        self.log_message.emit(ensure_text(message))

    def run(self):
        workspace = text_type("")
        try:
            workspace, command_specs = self.prepare_workspace_and_commands()
            commands_file = os.path.join(workspace, "commands.txt")
            with open(commands_file, "wb") as handle:
                joined = u"\n".join([u"{0}: {1}".format(label, command_to_text(cmd)) for label, cmd in command_specs])
                handle.write(joined.encode("utf-8"))

            for label, command in command_specs:
                self.emit_log(u"[INFO] 开始执行: {0}".format(label))
                self.emit_log(command_to_text(command))
                exit_code = self.run_process(command)
                if exit_code != 0:
                    raise RuntimeError(u"{0} 执行失败，退出码 {1}".format(label, exit_code))

            self.emit_log(u"[INFO] 全部流程执行完成。")
            self.finished.emit(True, workspace)
        except Exception as exc:
            self.emit_log(u"[ERROR] {0}".format(ensure_text(exc)))
            self.emit_log(ensure_text(traceback.format_exc()))
            self.finished.emit(False, workspace)

    def run_process(self, command):
        popen = subprocess.Popen(
            command,
            cwd=self._settings["process_cwd"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        while True:
            line = popen.stdout.readline()
            if not line:
                break
            self.emit_log(ensure_text(line.rstrip()))
        popen.stdout.close()
        return popen.wait()

    def prepare_workspace_and_commands(self):
        workflow = self._settings["workflow"]
        output_root = self._settings["output_root"]
        job_name = self._settings["job_name"]
        workspace = unique_workspace(output_root, job_name)
        safe_makedirs(workspace)
        self.emit_log(u"[INFO] 输出工作目录: {0}".format(workspace))

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
                self._settings["prep_config"]
            ]
            if staged_sharp:
                quadwild_command.append(staged_sharp)
            if staged_rosy:
                quadwild_command.append(staged_rosy)
            quadwild_command.extend(split_extra_args(self._settings["quadwild_extra_args"]))
            command_specs.append((u"quadwild", quadwild_command))

            if workflow == "full_pipeline":
                rem_p0_mesh = os.path.splitext(staged_quadwild_mesh)[0] + "_rem_p0.obj"
                quad_from_patches_command = self.build_quad_from_patches_command(
                    rem_p0_mesh,
                    workspace
                )
                command_specs.append((u"quad_from_patches", quad_from_patches_command))

        if workflow == "quad_from_patches_only":
            staged_qfp_mesh = copy_file_to_directory(self._settings["quad_from_patches_input_mesh"], workspace)
            copy_sidecars(
                self._settings["quad_from_patches_input_mesh"],
                workspace,
                [".patch", ".corners", ".feature", ".c_feature"],
                self.emit_log
            )
            quad_from_patches_command = self.build_quad_from_patches_command(staged_qfp_mesh, workspace)
            command_specs.append((u"quad_from_patches", quad_from_patches_command))

        return workspace, command_specs

    def build_quad_from_patches_command(self, mesh_path, workspace):
        command = [
            self._settings["quad_from_patches_binary"],
            mesh_path,
            self._settings["quad_from_patches_num"],
            self._settings["main_config"]
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
        self.setWindowTitle(u"QuadWild Binary UI")
        self.resize(1100, 820)
        self.build_ui()
        self.load_settings()
        self.apply_defaults_if_needed()
        self.update_mode()
        self.update_command_preview()

    def build_ui(self):
        central = QtWidgets.QWidget(self)
        self.setCentralWidget(central)
        root_layout = QtWidgets.QVBoxLayout(central)

        root_layout.addWidget(self.build_workflow_group())
        root_layout.addWidget(self.build_quadwild_group())
        root_layout.addWidget(self.build_quad_from_patches_group())
        root_layout.addWidget(self.build_preview_group(), 1)
        root_layout.addWidget(self.build_log_group(), 1)

        button_layout = QtWidgets.QHBoxLayout()
        self.start_button = QtWidgets.QPushButton(u"开始执行")
        self.open_output_button = QtWidgets.QPushButton(u"打开输出目录")
        self.open_output_button.setEnabled(False)
        self.save_settings_button = QtWidgets.QPushButton(u"保存界面设置")
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.open_output_button)
        button_layout.addStretch(1)
        button_layout.addWidget(self.save_settings_button)
        root_layout.addLayout(button_layout)

        self.start_button.clicked.connect(self.start_workflow)
        self.open_output_button.clicked.connect(self.open_output_directory)
        self.save_settings_button.clicked.connect(self.save_settings)

    def build_workflow_group(self):
        group = QtWidgets.QGroupBox(u"流程与输出")
        layout = QtWidgets.QFormLayout(group)

        self.workflow_combo = QtWidgets.QComboBox()
        self.workflow_combo.addItem(u"完整流程：quadwild -> quad_from_patches", "full_pipeline")
        self.workflow_combo.addItem(u"仅运行 quadwild", "quadwild_only")
        self.workflow_combo.addItem(u"仅运行 quad_from_patches", "quad_from_patches_only")

        self.output_root_edit = QtWidgets.QLineEdit()
        self.output_root_button = QtWidgets.QPushButton(u"浏览...")
        self.job_name_edit = QtWidgets.QLineEdit()

        output_layout = QtWidgets.QHBoxLayout()
        output_layout.addWidget(self.output_root_edit, 1)
        output_layout.addWidget(self.output_root_button)

        layout.addRow(u"工作流", self.workflow_combo)
        layout.addRow(u"输出根目录", self.wrap_layout(output_layout))
        layout.addRow(u"任务文件夹名", self.job_name_edit)

        self.workflow_combo.currentIndexChanged.connect(self.update_mode)
        self.output_root_button.clicked.connect(lambda: self.choose_directory(self.output_root_edit))
        self.workflow_combo.currentIndexChanged.connect(self.update_command_preview)
        self.output_root_edit.textChanged.connect(self.update_command_preview)
        self.job_name_edit.textChanged.connect(self.update_command_preview)
        return group

    def build_quadwild_group(self):
        group = QtWidgets.QGroupBox(u"QuadWild 阶段")
        self.quadwild_group = group
        layout = QtWidgets.QFormLayout(group)

        self.quadwild_binary_edit = QtWidgets.QLineEdit()
        self.quadwild_binary_button = QtWidgets.QPushButton(u"浏览...")
        self.quadwild_input_edit = QtWidgets.QLineEdit()
        self.quadwild_input_button = QtWidgets.QPushButton(u"浏览...")
        self.stop_step_combo = QtWidgets.QComboBox()
        self.stop_step_combo.addItem(u"1 - 仅重网格与场", "1")
        self.stop_step_combo.addItem(u"2 - 处理到 Tracing", "2")
        self.stop_step_combo.addItem(u"3 - 处理到 Quadrangulation", "3")
        self.prep_config_edit = QtWidgets.QLineEdit()
        self.prep_config_button = QtWidgets.QPushButton(u"浏览...")
        self.sharp_edit = QtWidgets.QLineEdit()
        self.sharp_button = QtWidgets.QPushButton(u"浏览...")
        self.rosy_edit = QtWidgets.QLineEdit()
        self.rosy_button = QtWidgets.QPushButton(u"浏览...")
        self.quadwild_extra_args_edit = QtWidgets.QLineEdit()

        layout.addRow(u"quadwild 二进制", self.browse_row(self.quadwild_binary_edit, self.quadwild_binary_button))
        layout.addRow(u"输入网格", self.browse_row(self.quadwild_input_edit, self.quadwild_input_button))
        layout.addRow(u"停止步骤", self.stop_step_combo)
        layout.addRow(u"预处理配置", self.browse_row(self.prep_config_edit, self.prep_config_button))
        layout.addRow(u"可选 .sharp", self.browse_row(self.sharp_edit, self.sharp_button))
        layout.addRow(u"可选 .rosy", self.browse_row(self.rosy_edit, self.rosy_button))
        layout.addRow(u"额外参数", self.quadwild_extra_args_edit)

        self.quadwild_binary_button.clicked.connect(lambda: self.choose_file(self.quadwild_binary_edit, u"选择 quadwild 可执行文件", u"Executable (*.exe);;All Files (*)"))
        self.quadwild_input_button.clicked.connect(lambda: self.choose_file(self.quadwild_input_edit, u"选择输入网格", u"Mesh Files (*.obj *.ply);;All Files (*)"))
        self.prep_config_button.clicked.connect(lambda: self.choose_file(self.prep_config_edit, u"选择预处理配置", u"Text Files (*.txt);;All Files (*)"))
        self.sharp_button.clicked.connect(lambda: self.choose_file(self.sharp_edit, u"选择 sharp 文件", u"Sharp Files (*.sharp);;All Files (*)"))
        self.rosy_button.clicked.connect(lambda: self.choose_file(self.rosy_edit, u"选择 rosy 文件", u"Rosy Files (*.rosy);;All Files (*)"))

        self.connect_preview_updates([
            self.quadwild_binary_edit,
            self.quadwild_input_edit,
            self.prep_config_edit,
            self.sharp_edit,
            self.rosy_edit,
            self.quadwild_extra_args_edit
        ])
        self.stop_step_combo.currentIndexChanged.connect(self.update_command_preview)
        return group

    def build_quad_from_patches_group(self):
        group = QtWidgets.QGroupBox(u"Quad From Patches 阶段")
        self.qfp_group = group
        layout = QtWidgets.QFormLayout(group)

        self.qfp_binary_edit = QtWidgets.QLineEdit()
        self.qfp_binary_button = QtWidgets.QPushButton(u"浏览...")
        self.qfp_input_edit = QtWidgets.QLineEdit()
        self.qfp_input_button = QtWidgets.QPushButton(u"浏览...")
        self.qfp_num_spin = QtWidgets.QSpinBox()
        self.qfp_num_spin.setMinimum(0)
        self.qfp_num_spin.setMaximum(999999999)
        self.main_config_edit = QtWidgets.QLineEdit()
        self.main_config_button = QtWidgets.QPushButton(u"浏览...")
        self.stats_json_edit = QtWidgets.QLineEdit()
        self.stats_json_button = QtWidgets.QPushButton(u"浏览...")
        self.qfp_extra_args_edit = QtWidgets.QLineEdit()
        self.qfp_auto_label = QtWidgets.QLabel(u"完整流程模式下会自动使用 <输入网格>_rem_p0.obj")
        self.qfp_auto_label.setWordWrap(True)

        layout.addRow(u"quad_from_patches 二进制", self.browse_row(self.qfp_binary_edit, self.qfp_binary_button))
        layout.addRow(u"输入网格", self.browse_row(self.qfp_input_edit, self.qfp_input_button))
        layout.addRow(u"自动输入说明", self.qfp_auto_label)
        layout.addRow(u"编号参数 num", self.qfp_num_spin)
        layout.addRow(u"主配置文件", self.browse_row(self.main_config_edit, self.main_config_button))
        layout.addRow(u"统计 JSON", self.browse_row(self.stats_json_edit, self.stats_json_button))
        layout.addRow(u"额外参数", self.qfp_extra_args_edit)

        self.qfp_binary_button.clicked.connect(lambda: self.choose_file(self.qfp_binary_edit, u"选择 quad_from_patches 可执行文件", u"Executable (*.exe);;All Files (*)"))
        self.qfp_input_button.clicked.connect(lambda: self.choose_file(self.qfp_input_edit, u"选择 quad_from_patches 输入网格", u"Mesh Files (*.obj);;All Files (*)"))
        self.main_config_button.clicked.connect(lambda: self.choose_file(self.main_config_edit, u"选择主配置文件", u"Text Files (*.txt);;All Files (*)"))
        self.stats_json_button.clicked.connect(lambda: self.choose_save_file(self.stats_json_edit, u"选择统计 JSON 输出", u"JSON Files (*.json);;All Files (*)"))

        self.connect_preview_updates([
            self.qfp_binary_edit,
            self.qfp_input_edit,
            self.main_config_edit,
            self.stats_json_edit,
            self.qfp_extra_args_edit
        ])
        self.qfp_num_spin.valueChanged.connect(self.update_command_preview)
        return group

    def build_preview_group(self):
        group = QtWidgets.QGroupBox(u"命令预览")
        layout = QtWidgets.QVBoxLayout(group)
        self.preview_text = QtWidgets.QPlainTextEdit()
        self.preview_text.setReadOnly(True)
        layout.addWidget(self.preview_text)
        return group

    def build_log_group(self):
        group = QtWidgets.QGroupBox(u"运行日志")
        layout = QtWidgets.QVBoxLayout(group)
        self.log_text = QtWidgets.QPlainTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        return group

    def wrap_layout(self, layout):
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        return widget

    def browse_row(self, edit_widget, button_widget):
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(edit_widget, 1)
        layout.addWidget(button_widget)
        return self.wrap_layout(layout)

    def connect_preview_updates(self, widgets):
        for widget in widgets:
            widget.textChanged.connect(self.update_command_preview)

    def apply_defaults_if_needed(self):
        if not self.output_root_edit.text().strip():
            self.output_root_edit.setText(os.path.join(repo_root(), "ui_runs"))
        if not self.quadwild_binary_edit.text().strip():
            self.quadwild_binary_edit.setText(default_release_binary("quadwild.exe"))
        if not self.qfp_binary_edit.text().strip():
            self.qfp_binary_edit.setText(default_release_binary("quad_from_patches.exe"))
        if not self.prep_config_edit.text().strip():
            self.prep_config_edit.setText(default_prep_config())
        if not self.main_config_edit.text().strip():
            self.main_config_edit.setText(default_main_config())
        if not self.job_name_edit.text().strip():
            self.job_name_edit.setText(self.default_job_name())

    def default_job_name(self):
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return "quadwild_job_" + stamp

    def load_settings(self):
        path = settings_path()
        if not os.path.exists(path):
            return
        try:
            with open(path, "rb") as handle:
                data = json.loads(ensure_text(handle.read()))
        except Exception:
            return

        self.set_combo_by_data(self.workflow_combo, data.get("workflow", "full_pipeline"))
        self.output_root_edit.setText(ensure_text(data.get("output_root", "")))
        self.job_name_edit.setText(ensure_text(data.get("job_name", "")))
        self.quadwild_binary_edit.setText(ensure_text(data.get("quadwild_binary", "")))
        self.qfp_binary_edit.setText(ensure_text(data.get("quad_from_patches_binary", "")))
        self.quadwild_input_edit.setText(ensure_text(data.get("quadwild_input_mesh", "")))
        self.qfp_input_edit.setText(ensure_text(data.get("quad_from_patches_input_mesh", "")))
        self.prep_config_edit.setText(ensure_text(data.get("prep_config", "")))
        self.main_config_edit.setText(ensure_text(data.get("main_config", "")))
        self.sharp_edit.setText(ensure_text(data.get("sharp_file", "")))
        self.rosy_edit.setText(ensure_text(data.get("rosy_file", "")))
        self.stats_json_edit.setText(ensure_text(data.get("stats_json", "")))
        self.quadwild_extra_args_edit.setText(ensure_text(data.get("quadwild_extra_args", "")))
        self.qfp_extra_args_edit.setText(ensure_text(data.get("quad_from_patches_extra_args", "")))
        self.set_combo_by_data(self.stop_step_combo, data.get("quadwild_stop_step", "3"))
        try:
            self.qfp_num_spin.setValue(int(data.get("quad_from_patches_num", 0)))
        except Exception:
            self.qfp_num_spin.setValue(0)

    def save_settings(self):
        data = self.collect_settings()
        path = settings_path()
        with open(path, "wb") as handle:
            handle.write(json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))
        self.append_log(u"[INFO] 已保存界面设置: {0}".format(path))

    def set_combo_by_data(self, combo, value):
        for index in range(combo.count()):
            if ensure_text(combo.itemData(index)) == ensure_text(value):
                combo.setCurrentIndex(index)
                return

    def choose_file(self, target_edit, title, filter_text):
        path, _selected = QtWidgets.QFileDialog.getOpenFileName(self, title, target_edit.text(), filter_text)
        if path:
            target_edit.setText(path)
            if target_edit is self.quadwild_input_edit and not self.job_name_edit.text().strip():
                self.job_name_edit.setText(self.default_job_name())

    def choose_save_file(self, target_edit, title, filter_text):
        path, _selected = QtWidgets.QFileDialog.getSaveFileName(self, title, target_edit.text(), filter_text)
        if path:
            target_edit.setText(path)

    def choose_directory(self, target_edit):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, u"选择目录", target_edit.text())
        if path:
            target_edit.setText(path)

    def update_mode(self):
        workflow = ensure_text(self.workflow_combo.currentData())
        quadwild_enabled = workflow in ("full_pipeline", "quadwild_only")
        qfp_enabled = workflow in ("full_pipeline", "quad_from_patches_only")
        qfp_input_enabled = workflow == "quad_from_patches_only"

        self.quadwild_group.setEnabled(quadwild_enabled)
        self.qfp_group.setEnabled(qfp_enabled)
        self.qfp_input_edit.setEnabled(qfp_input_enabled)
        self.qfp_input_button.setEnabled(qfp_input_enabled)
        self.qfp_auto_label.setVisible(workflow == "full_pipeline")
        self.stop_step_combo.setEnabled(workflow == "quadwild_only")
        self.update_command_preview()

    def validate_settings(self, settings):
        workflow = settings["workflow"]
        errors = []

        if not settings["output_root"]:
            errors.append(u"请选择输出根目录。")

        if workflow in ("full_pipeline", "quadwild_only"):
            if not os.path.isfile(settings["quadwild_binary"]):
                errors.append(u"quadwild 二进制不存在。")
            if not os.path.isfile(settings["quadwild_input_mesh"]):
                errors.append(u"quadwild 输入网格不存在。")
            if not os.path.isfile(settings["prep_config"]):
                errors.append(u"预处理配置文件不存在。")
            if settings["sharp_file"] and not os.path.isfile(settings["sharp_file"]):
                errors.append(u".sharp 文件不存在。")
            if settings["rosy_file"] and not os.path.isfile(settings["rosy_file"]):
                errors.append(u".rosy 文件不存在。")

        if workflow in ("full_pipeline", "quad_from_patches_only"):
            if not os.path.isfile(settings["quad_from_patches_binary"]):
                errors.append(u"quad_from_patches 二进制不存在。")
            if workflow == "quad_from_patches_only" and not os.path.isfile(settings["quad_from_patches_input_mesh"]):
                errors.append(u"quad_from_patches 输入网格不存在。")
            if not os.path.isfile(settings["main_config"]):
                errors.append(u"主配置文件不存在。")

        return errors

    def collect_settings(self):
        workflow = ensure_text(self.workflow_combo.currentData())
        return {
            "workflow": workflow,
            "output_root": ensure_text(self.output_root_edit.text()).strip(),
            "job_name": ensure_text(self.job_name_edit.text()).strip() or self.default_job_name(),
            "quadwild_binary": ensure_text(self.quadwild_binary_edit.text()).strip(),
            "quad_from_patches_binary": ensure_text(self.qfp_binary_edit.text()).strip(),
            "quadwild_input_mesh": ensure_text(self.quadwild_input_edit.text()).strip(),
            "quad_from_patches_input_mesh": ensure_text(self.qfp_input_edit.text()).strip(),
            "prep_config": ensure_text(self.prep_config_edit.text()).strip(),
            "main_config": ensure_text(self.main_config_edit.text()).strip(),
            "sharp_file": ensure_text(self.sharp_edit.text()).strip(),
            "rosy_file": ensure_text(self.rosy_edit.text()).strip(),
            "quadwild_stop_step": ensure_text(self.stop_step_combo.currentData()),
            "quad_from_patches_num": text_type(self.qfp_num_spin.value()),
            "stats_json": ensure_text(self.stats_json_edit.text()).strip(),
            "quadwild_extra_args": ensure_text(self.quadwild_extra_args_edit.text()).strip(),
            "quad_from_patches_extra_args": ensure_text(self.qfp_extra_args_edit.text()).strip(),
            "process_cwd": repo_root()
        }

    def build_preview_lines(self, settings):
        lines = [u"工作目录: {0}".format(settings["process_cwd"])]
        lines.append(u"输出根目录: {0}".format(settings["output_root"] or u"<未设置>"))
        lines.append(u"任务目录名: {0}".format(settings["job_name"] or u"<自动生成>"))

        workflow = settings["workflow"]
        if workflow in ("full_pipeline", "quadwild_only"):
            quadwild_command = [
                settings["quadwild_binary"] or u"<quadwild.exe>",
                u"<工作目录中的输入网格副本>",
                settings["quadwild_stop_step"] if workflow == "quadwild_only" else u"2",
                settings["prep_config"] or u"<prep config>"
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
                settings["main_config"] or u"<main config>"
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
                settings["main_config"] or u"<main config>"
            ]
            if settings["stats_json"]:
                qfp_command.append(settings["stats_json"])
            qfp_command.extend(split_extra_args(settings["quad_from_patches_extra_args"]))
            lines.append(u"")
            lines.append(u"[quad_from_patches]")
            lines.append(command_to_text(qfp_command))
        return lines

    def update_command_preview(self):
        settings = self.collect_settings()
        lines = self.build_preview_lines(settings)
        self.preview_text.setPlainText(u"\n".join(lines))

    def append_log(self, message):
        self.log_text.appendPlainText(ensure_text(message))

    def start_workflow(self):
        settings = self.collect_settings()
        errors = self.validate_settings(settings)
        if errors:
            QtWidgets.QMessageBox.warning(self, u"参数不完整", u"\n".join(errors))
            return

        self.save_settings()
        self.log_text.clear()
        self.append_log(u"[INFO] 准备开始执行。")
        self.start_button.setEnabled(False)
        self.open_output_button.setEnabled(False)
        self.last_workspace = text_type("")

        self.worker_thread = QtCore.QThread(self)
        self.worker = ProcessWorker(settings)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.log_message.connect(self.append_log)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()

    def on_worker_finished(self, success, workspace):
        self.start_button.setEnabled(True)
        self.last_workspace = ensure_text(workspace)
        if workspace:
            self.open_output_button.setEnabled(True)
        if success:
            self.append_log(u"[INFO] 任务完成。输出目录: {0}".format(self.last_workspace))
            QtWidgets.QMessageBox.information(self, u"执行完成", u"处理完成。\n输出目录：\n{0}".format(self.last_workspace))
        else:
            self.append_log(u"[ERROR] 任务失败。")
            QtWidgets.QMessageBox.critical(self, u"执行失败", u"处理失败，请检查日志。")

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
