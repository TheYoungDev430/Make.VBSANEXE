import os
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox, QProgressBar, QLineEdit, QComboBox,
    QTextEdit, QCheckBox, QStackedWidget
)
from PyQt6.QtCore import Qt

LICENSES = {
    "MIT": """MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
...""",
    "GPL": """GNU GENERAL PUBLIC LICENSE

This program is free software: you can redistribute it and/or modify
...""",
    "Apache": """Apache License

Licensed under the Apache License, Version 2.0 (the "License");
..."""
}

def generate_cpp_wrapper(vbs_path, license_text=None):
    with open(vbs_path, 'r', encoding='utf-8') as f:
        vbs_content = f.read()
    escaped_vbs = vbs_content.replace('\\', '\\\\').replace('"', '\\"')

    license_comment = f"/*\n{license_text}\n*/\n" if license_text else ""

    cpp_code = f'''
{license_comment}
#include <windows.h>
#include <fstream>
#include <string>
#include <shlobj.h>

int WINAPI WinMain(HINSTANCE, HINSTANCE, LPSTR, int) {{
    char tempPath[MAX_PATH];
    GetTempPathA(MAX_PATH, tempPath);
    std::string tempFile = std::string(tempPath) + "embedded_script.vbs";

    std::ofstream out(tempFile);
    out << "{escaped_vbs}";
    out.close();

    ShellExecuteA(NULL, "open", "wscript.exe", tempFile.c_str(), NULL, SW_HIDE);
    return 0;
}}
'''
    cpp_output_path = os.path.join(os.path.dirname(vbs_path), 'vbs_embedded_wrapper.cpp')
    with open(cpp_output_path, 'w', encoding='utf-8') as f:
        f.write(cpp_code)
    return cpp_output_path

def compile_cpp_to_exe(cpp_path, output_path):
    compile_command = f'g++ "{cpp_path}" -o "{output_path}" -mwindows'
    result = os.system(compile_command)
    return result == 0

class VBSCompiler(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VBS to EXE Compiler")
        self.setGeometry(100, 100, 600, 400)

        self.stack = QStackedWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.stack)
        self.setLayout(layout)

        self.vbs_path = ""
        self.output_folder = ""
        self.exe_name = ""
        self.selected_license = ""
        self.skip_license = False

        self.init_input_screen()
        self.init_license_screen()
        self.init_compile_screen()

    def init_input_screen(self):
        screen = QWidget()
        layout = QVBoxLayout()

        self.label = QLabel("Select a .vbs file to compile into .exe")
        layout.addWidget(self.label)

        self.select_button = QPushButton("Choose VBS File")
        self.select_button.clicked.connect(self.select_vbs_file)
        layout.addWidget(self.select_button)

        self.output_name_input = QLineEdit()
        self.output_name_input.setPlaceholderText("Enter EXE name (without .exe)")
        layout.addWidget(self.output_name_input)

        self.output_folder_button = QPushButton("Choose Output Folder")
        self.output_folder_button.clicked.connect(self.select_output_folder)
        layout.addWidget(self.output_folder_button)

        self.output_folder_label = QLabel("No folder selected")
        layout.addWidget(self.output_folder_label)

        next_button = QPushButton("Next")
        next_button.clicked.connect(self.go_to_license_screen)
        layout.addWidget(next_button)

        screen.setLayout(layout)
        self.stack.addWidget(screen)

    def init_license_screen(self):
        screen = QWidget()
        layout = QVBoxLayout()

        self.skip_license_checkbox = QCheckBox("Skip license embedding")
        self.skip_license_checkbox.stateChanged.connect(self.toggle_license_options)
        layout.addWidget(self.skip_license_checkbox)

        self.license_dropdown = QComboBox()
        self.license_dropdown.addItems(LICENSES.keys())
        self.license_dropdown.currentTextChanged.connect(self.update_license_preview)
        layout.addWidget(self.license_dropdown)

        self.license_preview = QTextEdit()
        self.license_preview.setReadOnly(True)
        layout.addWidget(self.license_preview)

        next_button = QPushButton("Next")
        next_button.clicked.connect(self.go_to_compile_screen)
        layout.addWidget(next_button)

        screen.setLayout(layout)
        self.stack.addWidget(screen)

    def init_compile_screen(self):
        screen = QWidget()
        layout = QVBoxLayout()

        self.compile_button = QPushButton("Compile to EXE")
        self.compile_button.clicked.connect(self.compile)
        layout.addWidget(self.compile_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        screen.setLayout(layout)
        self.stack.addWidget(screen)

    def select_vbs_file(self):
        vbs_path, _ = QFileDialog.getOpenFileName(self, "Select VBS File", "", "VBScript Files (*.vbs)")
        if vbs_path:
            self.vbs_path = vbs_path
            self.label.setText(f"Selected: {os.path.basename(vbs_path)}")

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_folder = folder
            self.output_folder_label.setText(f"Output Folder: {folder}")

    def go_to_license_screen(self):
        self.exe_name = self.output_name_input.text().strip()
        if not self.vbs_path:
            QMessageBox.warning(self, "Warning", "Please select a VBS file.")
            return
        if not self.exe_name:
            QMessageBox.warning(self, "Warning", "Please enter a name for the output EXE.")
            return
        if not self.output_folder:
            QMessageBox.warning(self, "Warning", "Please select an output folder.")
            return
        self.stack.setCurrentIndex(1)
        self.update_license_preview()

    def toggle_license_options(self, state):
        disabled = state == Qt.CheckState.Checked
        self.license_dropdown.setDisabled(disabled)
        self.license_preview.setDisabled(disabled)
        self.skip_license = disabled

    def update_license_preview(self):
        license_name = self.license_dropdown.currentText()
        self.selected_license = license_name
        self.license_preview.setPlainText(LICENSES.get(license_name, ""))

    def go_to_compile_screen(self):
        self.stack.setCurrentIndex(2)

    def compile(self):
        self.progress_bar.setValue(10)
        try:
            license_text = None if self.skip_license else LICENSES.get(self.selected_license, "")
            cpp_path = generate_cpp_wrapper(self.vbs_path, license_text)
            self.progress_bar.setValue(40)

            output_exe_path = os.path.join(self.output_folder, self.exe_name + ".exe")
            success = compile_cpp_to_exe(cpp_path, output_exe_path)
            self.progress_bar.setValue(100 if success else 0)

            if success:
                QMessageBox.information(self, "Success", f"Executable created at:\n{output_exe_path}")
            else:
                QMessageBox.critical(self, "Compilation Failed", "Failed to compile the generated C++ file.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            self.progress_bar.setValue(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VBSCompiler()
    window.show()
    sys.exit(app.exec())