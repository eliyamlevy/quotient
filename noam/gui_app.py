import sys
import os
import json
import pandas as pd
from pathlib import Path
from typing import Optional, List
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QTextBrowser, QFileDialog, QProgressBar,
    QTableWidget, QTableWidgetItem, QTabWidget, QMessageBox,
    QGroupBox, QGridLayout, QSpinBox, QDoubleSpinBox, QComboBox
)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon, QPixmap
import time
from openai import OpenAI
from io import StringIO
import requests

# Import your existing modules
from email_parser import parse_email
from extractor import extract_inventory_items_prompt
from excel_exporter import create_excel_exporter

class AIProcessor(QThread):
    """Background thread for AI processing"""
    progress_updated = pyqtSignal(str)
    processing_complete = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    debug_log = pyqtSignal(str)
    
    def __init__(self, email_body: str, provider: str, model_name: str, max_tokens: int, 
                 temperature: float, server_url: str = "", api_key: str = "", inline_images: list = None):
        super().__init__()
        self.email_body = email_body
        self.provider = provider
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.server_url = server_url
        self.api_key = api_key
        self.inline_images = inline_images or []
        
    def run(self):
        start_time = time.time()
        try:
            self.progress_updated.emit("Initializing AI client...")
            
            if self.provider == "Local AI Server":
                self.debug_log.emit(f"Initializing OpenAI client with local server: {self.server_url}")
                client = OpenAI(
                    base_url=self.server_url,
                    api_key=self.api_key,
                )
            else:
                self.debug_log.emit("Initializing OpenAI client with ChatGPT")
                client = OpenAI(
                    api_key=self.api_key,
                )
            
            self.progress_updated.emit("Sending request to AI model...")
            self.debug_log.emit(f"Sending request to model: {self.model_name}")
            self.debug_log.emit(f"Max tokens: {self.max_tokens}")
            
            # Prepare the message content
            message_content = []
            
            # Add text content
            text_content = extract_inventory_items_prompt(self.email_body)
            message_content.append({
                "type": "text",
                "text": text_content
            })
            
            # Add images if available and model supports vision
            if self.inline_images:
                self.debug_log.emit(f"Found {len(self.inline_images)} inline images")
                for i, img in enumerate(self.inline_images):
                    self.debug_log.emit(f"Adding image {i+1}: {img['content_type']} (Content-ID: {img['content_id']})")
                    message_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{img['content_type']};base64,{img['data']}"
                        }
                    })
            else:
                self.debug_log.emit("No inline images found in email")
            
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": message_content,
                    }
                ],
                stream=False,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            
            self.progress_updated.emit("Processing AI response...")
            output = response.choices[0].message.content
            
            # Log the raw LLM output
            debug_output = "="*50 + "\n"
            debug_output += "RAW LLM OUTPUT:\n"
            debug_output += "="*50 + "\n"
            debug_output += output + "\n"
            debug_output += "="*50 + "\n"
            debug_output += "END RAW OUTPUT\n"
            debug_output += "="*50
            self.debug_log.emit(debug_output)
            self.progress_updated.emit(f"Raw LLM Output received (see debug log)")
            # Clean up the output - remove various backtick formats
            output = output.strip()
            if output.startswith("```json\n"):
                output = output.removeprefix("```json\n")
            elif output.startswith("```"):
                output = output.removeprefix("```")
            if output.endswith("\n```"):
                output = output.removesuffix("\n```")
            elif output.endswith("```"):
                output = output.removesuffix("```")
            output = output.strip()
            
            # Parse the JSON response
            try:
                df = pd.read_json(StringIO(output))
                self.progress_updated.emit("JSON parsing successful!")
            except Exception as json_error:
                error_msg = f"JSON parsing failed: {str(json_error)}\nRaw output was:\n{output}"
                self.debug_log.emit(error_msg)
                self.error_occurred.emit(error_msg)
                return
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            self.progress_updated.emit("Processing complete!")
            self.processing_complete.emit({
                'raw_response': output,
                'dataframe': df,
                'items_count': len(df),
                'processing_time': processing_time
            })
            
        except Exception as e:
            self.error_occurred.emit(f"Error during processing: {str(e)}")

class EmailProcessorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_data = None
        self.current_email_file = None
        
        # Batch processing data
        self.batch_email_files = []
        self.batch_results = []
        self.current_batch_index = 0
        
        self.init_ui()
        
        # Initialize model capabilities display
        QTimer.singleShot(1000, lambda: self.update_model_capabilities_display("llama4:scout"))
        
    def init_ui(self):
        self.setWindowTitle("Email Inventory Processor")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set up the main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Create tab widget
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Create tabs
        tabs.addTab(self.create_home_tab(), "Home")
        tabs.addTab(self.create_ai_config_tab(), "AI Config")
        tabs.addTab(self.create_processing_tab(), "Process Email")
        tabs.addTab(self.create_batch_processing_tab(), "Batch Processing")
        tabs.addTab(self.create_results_tab(), "Results")
        tabs.addTab(self.create_raw_output_tab(), "Raw Output")
        tabs.addTab(self.create_debug_tab(), "Debug Log")
        tabs.addTab(self.create_export_tab(), "Export")
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready to process emails")
        
    def create_processing_tab(self):
        """Create the main processing tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # File selection group
        file_group = QGroupBox("Email File Selection")
        file_layout = QVBoxLayout(file_group)
        
        # File selection row
        file_row = QHBoxLayout()
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("padding: 5px; border: 1px solid #ccc; background: #f9f9f9;")
        select_file_btn = QPushButton("Select Email File (.eml)")
        select_file_btn.clicked.connect(self.select_email_file)
        file_row.addWidget(self.file_label, 1)
        file_row.addWidget(select_file_btn)
        file_layout.addLayout(file_row)
        
        layout.addWidget(file_group)
        
        # Email preview group
        preview_group = QGroupBox("Email Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.email_preview = QTextBrowser()
        self.email_preview.setMaximumHeight(300)
        self.email_preview.setOpenExternalLinks(True)
        preview_layout.addWidget(self.email_preview)
        
        layout.addWidget(preview_group)
        
        # Processing controls
        process_group = QGroupBox("Processing")
        process_layout = QVBoxLayout(process_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        process_layout.addWidget(self.progress_bar)
        
        # Process button
        self.process_btn = QPushButton("Process Email")
        self.process_btn.clicked.connect(self.process_email)
        self.process_btn.setEnabled(False)
        process_layout.addWidget(self.process_btn)
        
        layout.addWidget(process_group)
        
        # Status display
        self.status_display = QTextEdit()
        self.status_display.setMaximumHeight(100)
        self.status_display.setReadOnly(True)
        layout.addWidget(self.status_display)
        
        layout.addStretch()
        return widget
    
    def create_home_tab(self):
        """Create the home/welcome tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Center the content
        layout.addStretch()
        
        # App title
        title_label = QLabel("Quotient")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(50)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: white; margin: 20px;")
        layout.addWidget(title_label)
        
        # App description
        desc_label = QLabel(
            "Email Inventory Processor\n\n"
            "Quotient is an intelligent email processing application that extracts inventory items "
            "from email content using AI. Simply load an email file, configure your AI settings, "
            "and let the system automatically identify and extract part numbers, quantities, and descriptions. "
            "Export the results to Excel templates or JSON format for further processing."
        )
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_font = QFont()
        desc_font.setPointSize(36)
        desc_label.setFont(desc_font)
        desc_label.setStyleSheet("color: white; margin: 20px; line-height: 1.5;")
        layout.addWidget(desc_label)
        
        # Quick start section
        quick_start_group = QGroupBox("Quick Start")
        quick_start_layout = QVBoxLayout(quick_start_group)
        
        quick_start_text = QLabel(
            "1. Go to 'Process Email' tab\n"
            "2. Select an email file (.eml)\n"
            "3. Configure AI settings (optional)\n"
            "4. Click 'Process Email' to extract items\n"
            "5. View results and export as needed"
        )
        quick_start_text.setStyleSheet("color: #7f8c8d; margin: 10px;")
        quick_start_layout.addWidget(quick_start_text)
        
        layout.addWidget(quick_start_group)
        
        layout.addStretch()
        return widget
    
    def create_ai_config_tab(self):
        """Create the AI configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # AI Provider Selection
        provider_group = QGroupBox("AI Provider")
        provider_layout = QVBoxLayout(provider_group)
        
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["Local AI Server", "ChatGPT (OpenAI)"])
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        provider_layout.addWidget(self.provider_combo)
        
        layout.addWidget(provider_group)
        
        # Local AI Settings
        self.local_ai_group = QGroupBox("Local AI Server Settings")
        local_layout = QHBoxLayout(self.local_ai_group)
        
        # Left side - Settings
        settings_widget = QWidget()
        settings_layout = QGridLayout(settings_widget)
        
        # Model selection
        settings_layout.addWidget(QLabel("AI Model:"), 0, 0)
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "mistral:7b",
            "llama2:7b",
            "codellama:7b",
            "llama2:13b",
            "mistral:instruct",
            "llama2:chat",
            "llama4:scout"
        ])
        self.model_combo.setCurrentText("llama4:scout")
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        settings_layout.addWidget(self.model_combo, 0, 1)
        
        # Server URL
        settings_layout.addWidget(QLabel("Server URL:"), 1, 0)
        self.server_url_input = QTextEdit()
        self.server_url_input.setMaximumHeight(30)
        self.server_url_input.setPlainText("http://localhost:11434/v1")
        settings_layout.addWidget(self.server_url_input, 1, 1)
        
        # API Key
        settings_layout.addWidget(QLabel("API Key:"), 2, 0)
        self.local_api_key_input = QTextEdit()
        self.local_api_key_input.setMaximumHeight(30)
        self.local_api_key_input.setPlainText("tom")
        settings_layout.addWidget(self.local_api_key_input, 2, 1)
        
        # Add settings widget to left side
        local_layout.addWidget(settings_widget)
        
        # Right side - Model Capabilities
        capabilities_widget = QWidget()
        capabilities_layout = QVBoxLayout(capabilities_widget)
        
        capabilities_label = QLabel("Model Capabilities")
        capabilities_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        capabilities_layout.addWidget(capabilities_label)
        
        self.model_capabilities_display = QTextBrowser()
        self.model_capabilities_display.setMaximumWidth(300)
        self.model_capabilities_display.setMaximumHeight(150)
        self.model_capabilities_display.setStyleSheet("background-color: #2d3748; border: 1px solid #dee2e6; border-radius: 4px; color: white;")
        capabilities_layout.addWidget(self.model_capabilities_display)
        
        # Add capabilities widget to right side
        local_layout.addWidget(capabilities_widget)
        
        layout.addWidget(self.local_ai_group)
        
        # ChatGPT Settings
        self.chatgpt_group = QGroupBox("ChatGPT Settings")
        chatgpt_layout = QGridLayout(self.chatgpt_group)
        
        # ChatGPT API Key
        chatgpt_layout.addWidget(QLabel("OpenAI API Key:"), 0, 0)
        self.chatgpt_api_key_input = QTextEdit()
        self.chatgpt_api_key_input.setMaximumHeight(30)
        self.chatgpt_api_key_input.setPlaceholderText("Enter your OpenAI API key (sk-...)")
        chatgpt_layout.addWidget(self.chatgpt_api_key_input, 0, 1)
        
        # ChatGPT Model
        chatgpt_layout.addWidget(QLabel("Model:"), 1, 0)
        self.chatgpt_model_combo = QComboBox()
        self.chatgpt_model_combo.addItems([
            "gpt-4",
            "gpt-4-turbo-preview",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k"
        ])
        chatgpt_layout.addWidget(self.chatgpt_model_combo, 1, 1)
        
        layout.addWidget(self.chatgpt_group)
        
        # Common Settings
        common_group = QGroupBox("Common Settings")
        common_layout = QGridLayout(common_group)
        
        # Max tokens
        common_layout.addWidget(QLabel("Max Tokens:"), 0, 0)
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 4000)
        self.max_tokens_spin.setValue(1000)
        common_layout.addWidget(self.max_tokens_spin, 0, 1)
        
        # Temperature
        common_layout.addWidget(QLabel("Temperature:"), 1, 0)
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setValue(0.1)
        self.temperature_spin.setSingleStep(0.1)
        common_layout.addWidget(self.temperature_spin, 1, 1)
        
        layout.addWidget(common_group)
        
        # Apply and Test Buttons
        button_layout = QHBoxLayout()
        
        apply_btn = QPushButton("Apply Settings")
        apply_btn.clicked.connect(self.apply_ai_settings)
        button_layout.addWidget(apply_btn)
        
        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(self.test_ai_connection)
        button_layout.addWidget(test_btn)
        
        layout.addLayout(button_layout)
        
        # Status display for AI config
        self.ai_config_status = QLabel("Settings not applied")
        self.ai_config_status.setStyleSheet("color: #e74c3c; padding: 5px;")
        layout.addWidget(self.ai_config_status)
        
        layout.addStretch()
        return widget
    
    def get_model_capabilities(self, model_name: str) -> list:
        """Fetch model capabilities from Ollama API"""
        try:
            url = "http://localhost:11434/api/show"
            payload = {"model": model_name}
            response = requests.post(url, json=payload, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            # Debug: Print the response structure
            print(f"API Response for {model_name}: {data}")
            
            # Handle different response formats
            if isinstance(data, dict):
                return data.get("capabilities", [])
            elif isinstance(data, list) and len(data) > 0:
                return data[0].get("capabilities", [])
            else:
                return []
        except Exception as e:
            print(f"Error fetching model capabilities: {e}")
            return []

    def get_model_info(self, model_name: str) -> dict:
        """Fetch model information from Ollama API"""
        try:
            url = "http://localhost:11434/api/show"
            payload = {"model": model_name}
            response = requests.post(url, json=payload, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            # Handle different response formats
            if isinstance(data, dict):
                return data.get("details", {})
            elif isinstance(data, list) and len(data) > 0:
                return data[0].get("details", {})
            else:
                return {}
        except Exception as e:
            print(f"Error fetching model info: {e}")
            return {}
    
    def update_model_capabilities_display(self, model_name: str):
        """Update the capabilities display for the selected model"""
        capabilities = self.get_model_capabilities(model_name)

        if capabilities:
            capabilities_text = f"<b>Model: {model_name}</b><br><br>"
            capabilities_text += "<b>Capabilities:</b><br>"

            # Check for multimodal capabilities (capabilities is a list)
            if "vision" in capabilities:
                capabilities_text += "✅ <b>Vision/Multimodal</b> - Can process images<br>"
            else:
                capabilities_text += "❌ <b>Text-only</b> - Cannot process images<br>"

            # Add other capabilities if available
            if "tools" in capabilities:
                capabilities_text += f"✅ <b>Tool Use</b><br>"
            if "completion" in capabilities:
                capabilities_text += f"✅ <b>Text Completion</b><br>"
            if "function_calling" in capabilities:
                capabilities_text += f"✅ <b>Function Calling</b><br>"
            if "json_mode" in capabilities:
                capabilities_text += f"✅ <b>JSON Mode</b><br>"

            # Add model details if available in the response
            model_info = self.get_model_info(model_name)
            if model_info:
                if "parameter_size" in model_info:
                    capabilities_text += f"<br><b>Parameters:</b> {model_info['parameter_size']}<br>"
                if "family" in model_info:
                    capabilities_text += f"<b>Family:</b> {model_info['family']}<br>"
        else:
            capabilities_text = f"<b>Model: {model_name}</b><br><br>❌ Could not fetch capabilities"

        self.model_capabilities_display.setHtml(capabilities_text)
    
    def on_model_changed(self, model_name: str):
        """Handle model selection change"""
        self.update_model_capabilities_display(model_name)
    
    def on_provider_changed(self, provider):
        """Handle AI provider selection change"""
        if provider == "Local AI Server":
            self.local_ai_group.setVisible(True)
            self.chatgpt_group.setVisible(False)
            # Update capabilities for current model
            current_model = self.model_combo.currentText()
            self.update_model_capabilities_display(current_model)
        else:
            self.local_ai_group.setVisible(False)
            self.chatgpt_group.setVisible(True)
    
    def apply_ai_settings(self):
        """Apply AI settings and update all references"""
        try:
            # Store current settings
            self.current_server_url = self.server_url_input.toPlainText().strip()
            self.current_api_key = self.local_api_key_input.toPlainText().strip()
            self.current_model = self.model_combo.currentText()
            self.current_max_tokens = self.max_tokens_spin.value()
            self.current_temperature = self.temperature_spin.value()
            
            # Update status
            self.ai_config_status.setText("Settings applied successfully!")
            self.ai_config_status.setStyleSheet("color: #27ae60; padding: 5px;")
            
            # Log the applied settings
            self.log_debug(f"AI Settings Applied:")
            self.log_debug(f"  Server URL: {self.current_server_url}")
            self.log_debug(f"  Model: {self.current_model}")
            self.log_debug(f"  Max Tokens: {self.current_max_tokens}")
            self.log_debug(f"  Temperature: {self.current_temperature}")
            
            QMessageBox.information(self, "Success", "AI settings applied successfully!")
            
        except Exception as e:
            self.ai_config_status.setText("Failed to apply settings")
            self.ai_config_status.setStyleSheet("color: #e74c3c; padding: 5px;")
            QMessageBox.critical(self, "Error", f"Failed to apply settings: {str(e)}")
    
    def test_ai_connection(self):
        """Test the AI connection"""
        try:
            provider = self.provider_combo.currentText()
            
            if provider == "Local AI Server":
                # Use applied settings if available, otherwise use current UI values
                server_url = getattr(self, 'current_server_url', self.server_url_input.toPlainText().strip())
                api_key = getattr(self, 'current_api_key', self.local_api_key_input.toPlainText().strip())
                test_model = getattr(self, 'current_model', self.model_combo.currentText())
                
                client = OpenAI(
                    base_url=server_url,
                    api_key=api_key,
                )
            else:
                client = OpenAI(
                    api_key=self.chatgpt_api_key_input.toPlainText().strip(),
                )
                test_model = "gpt-3.5-turbo"
            
            # Simple test request
            response = client.chat.completions.create(
                model=test_model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5,
            )
            
            QMessageBox.information(self, "Success", f"AI connection test successful using model: {test_model}")
            
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to connect: {str(e)}")
    
    def create_results_tab(self):
        """Create the results display tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Results info
        info_group = QGroupBox("Processing Results")
        info_layout = QHBoxLayout(info_group)
        
        self.items_count_label = QLabel("Items extracted: 0")
        self.processing_time_label = QLabel("Processing time: --")
        info_layout.addWidget(self.items_count_label)
        info_layout.addWidget(self.processing_time_label)
        info_layout.addStretch()
        
        layout.addWidget(info_group)
        
        # Results table
        self.results_table = QTableWidget()
        layout.addWidget(self.results_table)
        
        return widget
    
    def create_raw_output_tab(self):
        """Create the raw output display tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Raw output display
        output_group = QGroupBox("Raw LLM Output")
        output_layout = QVBoxLayout(output_group)
        
        self.raw_output_display = QTextEdit()
        self.raw_output_display.setReadOnly(True)
        self.raw_output_display.setFont(QFont("Courier", 10))
        output_layout.addWidget(self.raw_output_display)
        
        layout.addWidget(output_group)
        
        return widget
    
    def create_debug_tab(self):
        """Create the debug log tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Debug log display
        debug_group = QGroupBox("Debug Log")
        debug_layout = QVBoxLayout(debug_group)
        
        self.debug_log = QTextEdit()
        self.debug_log.setReadOnly(True)
        self.debug_log.setFont(QFont("Courier", 9))
        self.debug_log.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        debug_layout.addWidget(self.debug_log)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        clear_btn = QPushButton("Clear Log")
        clear_btn.clicked.connect(self.clear_debug_log)
        button_layout.addWidget(clear_btn)
        
        save_btn = QPushButton("Save Log")
        save_btn.clicked.connect(self.save_debug_log)
        button_layout.addWidget(save_btn)
        
        button_layout.addStretch()
        debug_layout.addLayout(button_layout)
        
        layout.addWidget(debug_group)
        return widget
    
    def create_batch_processing_tab(self):
        """Create the batch processing tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # File selection group
        file_group = QGroupBox("Batch File Selection")
        file_layout = QVBoxLayout(file_group)
        
        # File selection row
        file_row = QHBoxLayout()
        self.batch_file_label = QLabel("No files selected")
        self.batch_file_label.setStyleSheet("padding: 5px; border: 1px solid #ccc; background: #f9f9f9;")
        select_files_btn = QPushButton("Select Multiple Email Files (.eml)")
        select_files_btn.clicked.connect(self.select_batch_files)
        file_row.addWidget(self.batch_file_label, 1)
        file_row.addWidget(select_files_btn)
        file_layout.addLayout(file_row)
        
        layout.addWidget(file_group)
        
        # Current email display
        current_email_group = QGroupBox("Current Email")
        current_email_layout = QVBoxLayout(current_email_group)
        
        self.current_email_label = QLabel("No emails selected")
        self.current_email_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_email_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        current_email_layout.addWidget(self.current_email_label)
        
        layout.addWidget(current_email_group)
        
        # Results display
        results_group = QGroupBox("Email Results")
        results_layout = QVBoxLayout(results_group)
        
        # Results info
        info_layout = QHBoxLayout()
        self.batch_items_count_label = QLabel("Items extracted: 0")
        self.batch_processing_time_label = QLabel("Processing time: --")
        self.batch_status_label = QLabel("Status: --")
        info_layout.addWidget(self.batch_items_count_label)
        info_layout.addWidget(self.batch_processing_time_label)
        info_layout.addWidget(self.batch_status_label)
        info_layout.addStretch()
        results_layout.addLayout(info_layout)
        
        # Results table
        self.batch_results_table = QTableWidget()
        results_layout.addWidget(self.batch_results_table)
        
        # Action buttons
        action_layout = QHBoxLayout()
        self.batch_export_btn = QPushButton("Export to Excel")
        self.batch_export_btn.clicked.connect(self.export_batch_to_excel)
        self.batch_export_btn.setEnabled(False)
        action_layout.addWidget(self.batch_export_btn)
        
        self.batch_view_raw_btn = QPushButton("View Raw Output")
        self.batch_view_raw_btn.clicked.connect(self.view_batch_raw_output)
        self.batch_view_raw_btn.setEnabled(False)
        action_layout.addWidget(self.batch_view_raw_btn)
        
        self.batch_view_email_btn = QPushButton("View Email")
        self.batch_view_email_btn.clicked.connect(self.view_batch_email)
        self.batch_view_email_btn.setEnabled(False)
        action_layout.addWidget(self.batch_view_email_btn)
        
        action_layout.addStretch()
        results_layout.addLayout(action_layout)
        
        layout.addWidget(results_group)
        
        # Processing controls
        process_group = QGroupBox("Batch Processing")
        process_layout = QVBoxLayout(process_group)
        
        # Progress bar
        self.batch_progress_bar = QProgressBar()
        self.batch_progress_bar.setVisible(False)
        process_layout.addWidget(self.batch_progress_bar)
        
        # Process button
        self.batch_process_btn = QPushButton("Process Batch")
        self.batch_process_btn.clicked.connect(self.process_batch)
        self.batch_process_btn.setEnabled(False)
        process_layout.addWidget(self.batch_process_btn)
        
        layout.addWidget(process_group)
        
        # Navigation controls
        nav_group = QGroupBox("Navigation")
        nav_layout = QVBoxLayout(nav_group)
        
        # Navigation buttons
        nav_button_layout = QHBoxLayout()
        nav_button_layout.addStretch()
        
        self.prev_btn = QPushButton("◀ Previous")
        self.prev_btn.clicked.connect(self.previous_email)
        self.prev_btn.setEnabled(False)
        nav_button_layout.addWidget(self.prev_btn)
        
        self.next_btn = QPushButton("Next ▶")
        self.next_btn.clicked.connect(self.next_email)
        self.next_btn.setEnabled(False)
        nav_button_layout.addWidget(self.next_btn)
        
        nav_button_layout.addStretch()
        nav_layout.addLayout(nav_button_layout)
        
        layout.addWidget(nav_group)
        
        return widget
    
    def log_debug(self, message):
        """Add a message to the debug log"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.debug_log.append(log_entry)
        # Auto-scroll to bottom
        self.debug_log.verticalScrollBar().setValue(
            self.debug_log.verticalScrollBar().maximum()
        )
    
    def clear_debug_log(self):
        """Clear the debug log"""
        self.debug_log.clear()
    
    def save_debug_log(self):
        """Save the debug log to a file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Debug Log", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.debug_log.toPlainText())
                QMessageBox.information(self, "Success", f"Debug log saved to: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save log: {str(e)}")
    
    def create_export_tab(self):
        """Create the export tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Export options
        export_group = QGroupBox("Export Options")
        export_layout = QVBoxLayout(export_group)
        
        # Excel export
        excel_row = QHBoxLayout()
        excel_row.addWidget(QLabel("Excel Template:"))
        self.template_label = QLabel("No template selected")
        self.template_label.setStyleSheet("padding: 5px; border: 1px solid #ccc; background: #f9f9f9;")
        select_template_btn = QPushButton("Select Template")
        select_template_btn.clicked.connect(self.select_excel_template)
        excel_row.addWidget(self.template_label, 1)
        excel_row.addWidget(select_template_btn)
        export_layout.addLayout(excel_row)
        
        # Output filename
        filename_row = QHBoxLayout()
        filename_row.addWidget(QLabel("Output Filename:"))
        self.filename_input = QTextEdit()
        self.filename_input.setMaximumHeight(30)
        self.filename_input.setPlaceholderText("Leave empty for auto-generated name (e.g., Processed_1234567890.xlsx)")
        filename_row.addWidget(self.filename_input, 1)
        export_layout.addLayout(filename_row)
        
        # Export button
        self.export_btn = QPushButton("Export to Excel")
        self.export_btn.clicked.connect(self.export_to_excel)
        self.export_btn.setEnabled(False)
        export_layout.addWidget(self.export_btn)
        
        layout.addWidget(export_group)
        
        # JSON export
        json_group = QGroupBox("JSON Export")
        json_layout = QVBoxLayout(json_group)
        
        json_export_btn = QPushButton("Export as JSON")
        json_export_btn.clicked.connect(self.export_to_json)
        json_layout.addWidget(json_export_btn)
        
        layout.addWidget(json_group)
        
        layout.addStretch()
        return widget
    
    def select_email_file(self):
        """Select an email file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Email File", "", "Email Files (*.eml);;All Files (*)"
        )
        
        if file_path:
            self.current_email_file = file_path
            self.file_label.setText(os.path.basename(file_path))
            self.process_btn.setEnabled(True)
            self.load_email_preview(file_path)
    
    def load_email_preview(self, file_path: str):
        """Load and display email preview with images"""
        try:
            email = parse_email(file_path)
            
            # Create HTML content with better readability
            html_content = f"""
            <div style="font-family: Arial, sans-serif; padding: 15px; background-color: white; color: #333;">
                <div style="background-color: #e8f4fd; padding: 12px; border-radius: 6px; margin-bottom: 15px; border-left: 4px solid #2196F3;">
                    <strong style="color: #1976D2;">From:</strong> <span style="color: #333;">{email.header.get('From', 'Unknown')}</span><br>
                    <strong style="color: #1976D2;">Subject:</strong> <span style="color: #333;">{email.header.get('Subject', 'No Subject')}</span><br>
                    <strong style="color: #1976D2;">Date:</strong> <span style="color: #333;">{email.header.get('Date', 'Unknown')}</span>
                </div>
                <hr style="border: 1px solid #e0e0e0; margin: 15px 0;">
                <div style="margin-top: 15px;">
            """
            
            # Add inline images to HTML
            for img in email.inline_images:
                html_content += f'<img src="data:{img["content_type"]};base64,{img["data"]}" style="max-width: 100%; height: auto; margin: 15px 0; border: 1px solid #e0e0e0; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" alt="Inline Image"><br>'
            
            # Debug: Log inline images found
            if email.inline_images:
                print(f"Found {len(email.inline_images)} inline images")
                for img in email.inline_images:
                    print(f"  - Content-ID: {img['content_id']}, Type: {img['content_type']}")
            else:
                print("No inline images found")
            
            # Add email body - use HTML body for better formatting
            if email.html_body:
                # Use original HTML for better formatting and newlines
                body_html = email.html_body
                # Don't truncate - show full email content
                html_content += f'<div style="line-height: 1.6; color: #333; font-size: 14px;">{body_html}</div>'
            else:
                # Fallback to processed text
                body_text = email.body
                body_text = body_text.replace('\n', '<br>')
                html_content += f'<div style="line-height: 1.6; color: #333; font-size: 14px;">{body_text}</div>'
            
            # Add attachment info if any
            if email.attachments:
                html_content += '<hr style="border: 1px solid #e0e0e0; margin: 20px 0;">'
                html_content += '<div style="background-color: #fff8e1; padding: 12px; border-radius: 6px; border-left: 4px solid #ff9800;">'
                html_content += '<strong style="color: #e65100;">Attachments:</strong><br>'
                for attachment in email.attachments:
                    html_content += f'<span style="color: #333;">• {attachment["filename"]}</span><br>'
                html_content += '</div>'
            
            html_content += '</div>'
            
            self.email_preview.setHtml(html_content)
            self.status_bar.showMessage(f"Loaded email: {os.path.basename(file_path)}")
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load email: {str(e)}")
    
    def select_excel_template(self):
        """Select Excel template file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel Template", "", "Excel Files (*.xlsx);;All Files (*)"
        )
        
        if file_path:
            self.template_label.setText(os.path.basename(file_path))
            self.export_btn.setEnabled(self.current_data is not None)
    
    def process_email(self):
        """Process the selected email"""
        if not self.current_email_file:
            return
        
        try:
            # Parse email
            email = parse_email(self.current_email_file)
            
            # Log image information
            if email.inline_images:
                self.log_debug(f"Found {len(email.inline_images)} inline images in email:")
                for i, img in enumerate(email.inline_images):
                    self.log_debug(f"  Image {i+1}: {img['content_type']} (Content-ID: {img['content_id']})")
            else:
                self.log_debug("No inline images found in email")
            
            # Get AI configuration
            provider = self.provider_combo.currentText()
            
            if provider == "Local AI Server":
                # Use applied settings if available, otherwise use current UI values
                model_name = getattr(self, 'current_model', self.model_combo.currentText())
                server_url = getattr(self, 'current_server_url', self.server_url_input.toPlainText().strip())
                api_key = getattr(self, 'current_api_key', self.local_api_key_input.toPlainText().strip())
                max_tokens = getattr(self, 'current_max_tokens', self.max_tokens_spin.value())
                temperature = getattr(self, 'current_temperature', self.temperature_spin.value())
            else:
                model_name = self.chatgpt_model_combo.currentText()
                server_url = ""
                api_key = self.chatgpt_api_key_input.toPlainText().strip()
                max_tokens = self.max_tokens_spin.value()
                temperature = self.temperature_spin.value()
            
            # Start AI processing in background
            self.processor = AIProcessor(
                email.body,
                provider,
                model_name,
                max_tokens,
                temperature,
                server_url,
                api_key,
                email.inline_images
            )
            
            self.processor.progress_updated.connect(self.update_progress)
            self.processor.processing_complete.connect(self.on_processing_complete)
            self.processor.error_occurred.connect(self.on_processing_error)
            self.processor.debug_log.connect(self.log_debug)
            
            # Update UI
            self.process_btn.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            self.status_display.clear()
            self.status_display.append("Starting processing...")
            
            # Start processing
            self.processor.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start processing: {str(e)}")
    
    def update_progress(self, message: str):
        """Update progress display"""
        self.status_display.append(message)
        self.status_bar.showMessage(message)
    
    def on_processing_complete(self, result: dict):
        """Handle processing completion"""
        self.current_data = result
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)
        
        # Update results tab
        self.display_results(result['dataframe'])
        self.items_count_label.setText(f"Items extracted: {result['items_count']}")
        
        # Update processing time
        processing_time = result.get('processing_time', 0)
        self.processing_time_label.setText(f"Processing time: {processing_time:.2f} seconds")
        
        # Update raw output tab
        self.raw_output_display.setText(result['raw_response'])
        
        # Enable export
        self.export_btn.setEnabled(True)
        
        # Clear filename input for new export
        self.filename_input.clear()
        
        # Switch to results tab
        self.centralWidget().findChild(QTabWidget).setCurrentIndex(4)
        
        QMessageBox.information(self, "Success", "Email processing completed successfully!")
    
    def on_processing_error(self, error: str):
        """Handle processing error"""
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)
        QMessageBox.critical(self, "Processing Error", error)
    
    def display_results(self, df: pd.DataFrame):
        """Display results in table"""
        self.results_table.setRowCount(len(df))
        self.results_table.setColumnCount(len(df.columns))
        self.results_table.setHorizontalHeaderLabels(df.columns)
        
        for i, row in df.iterrows():
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                self.results_table.setItem(i, j, item)
        
        self.results_table.resizeColumnsToContents()
    
    def export_to_excel(self):
        """Export results to Excel using the new Excel exporter"""
        if not self.current_data or self.template_label.text() == "No template selected":
            QMessageBox.warning(self, "Warning", "Please select a template and ensure data is processed")
            return
        
        try:
            template_path = self.template_label.text()
            if not os.path.isabs(template_path):
                # Assume it's in the data directory
                template_path = os.path.join("data", template_path)
            
            # Create Excel exporter with dependency injection
            excel_exporter = create_excel_exporter(
                template_path=template_path,
                output_directory="data",
                starting_row=23
            )
            
            df = self.current_data['dataframe']
            
            # Get custom filename or use default
            custom_filename = self.filename_input.toPlainText().strip()
            if custom_filename:
                # Clean the filename - remove invalid characters
                import re
                custom_filename = re.sub(r'[<>:"/\\|?*]', '_', custom_filename)
                
                # Remove .xlsx extension if present (exporter will add it)
                if custom_filename.lower().endswith('.xlsx'):
                    custom_filename = custom_filename[:-5]
                
                # Check if filename is not empty after cleaning
                if not custom_filename.strip():
                    custom_filename = f"Processed_{int(time.time())}"
            else:
                # Use auto-generated name
                custom_filename = f"Processed_{int(time.time())}"
            
            # Export using the new Excel exporter
            output_path = excel_exporter.export_dataframe(df, custom_filename)
            
            QMessageBox.information(self, "Success", f"Exported to: {output_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export: {str(e)}")
    
    def export_to_json(self):
        """Export results to JSON"""
        if not self.current_data:
            QMessageBox.warning(self, "Warning", "No data to export")
            return
        
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save JSON", "", "JSON Files (*.json)"
            )
            
            if file_path:
                df = self.current_data['dataframe']
                df.to_json(file_path, orient='records', indent=2)
                QMessageBox.information(self, "Success", f"Exported to: {file_path}")
                
        except Exception as e:
                        QMessageBox.critical(self, "Export Error", f"Failed to export: {str(e)}")
    
    # Batch processing methods
    def select_batch_files(self):
        """Select multiple email files for batch processing"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Email Files",
            "data",
            "Email Files (*.eml);;All Files (*)"
        )
        
        if files:
            self.batch_email_files = files
            self.batch_file_label.setText(f"{len(files)} files selected")
            self.batch_process_btn.setEnabled(True)
            self.current_batch_index = 0
            self.batch_results = []  # Clear any previous results
            self.update_batch_display()
            self.log_debug(f"Selected {len(files)} files for batch processing")
    
    def process_batch(self):
        """Process all selected email files"""
        self.log_debug("Batch processing started")
        
        if not self.batch_email_files:
            self.log_debug("No batch files selected")
            return
        
        self.log_debug(f"Starting batch processing of {len(self.batch_email_files)} files")
        
        self.batch_results = []
        self.current_batch_index = 0
        self.batch_process_btn.setEnabled(False)
        self.batch_progress_bar.setVisible(True)
        self.batch_progress_bar.setRange(0, len(self.batch_email_files))
        self.batch_progress_bar.setValue(0)
        
        # Process first email
        self.process_next_batch_email()
    
    def process_next_batch_email(self):
        """Process the next email in the batch"""
        self.log_debug(f"Processing next batch email: index {self.current_batch_index}, total files {len(self.batch_email_files)}")
        
        if self.current_batch_index >= len(self.batch_email_files):
            # Batch complete
            self.log_debug("Batch processing complete")
            self.batch_progress_bar.setVisible(False)
            self.batch_process_btn.setEnabled(True)
            self.current_batch_index = 0
            self.update_batch_display()
            QMessageBox.information(self, "Success", f"Batch processing complete! Processed {len(self.batch_results)} emails.")
            return
        
        current_file = self.batch_email_files[self.current_batch_index]
        self.log_debug(f"Processing batch email {self.current_batch_index + 1}/{len(self.batch_email_files)}: {os.path.basename(current_file)}")
        
        try:
            # Parse email
            email = parse_email(current_file)
            
            # Get AI configuration
            provider = self.provider_combo.currentText()
            
            if provider == "Local AI Server":
                model_name = getattr(self, 'current_model', self.model_combo.currentText())
                server_url = getattr(self, 'current_server_url', self.server_url_input.toPlainText().strip())
                api_key = getattr(self, 'current_api_key', self.local_api_key_input.toPlainText().strip())
                max_tokens = getattr(self, 'current_max_tokens', self.max_tokens_spin.value())
                temperature = getattr(self, 'current_temperature', self.temperature_spin.value())
            else:
                model_name = self.chatgpt_model_combo.currentText()
                server_url = ""
                api_key = self.chatgpt_api_key_input.toPlainText().strip()
                max_tokens = self.max_tokens_spin.value()
                temperature = self.temperature_spin.value()
            
            # Create batch processor
            self.log_debug(f"Creating AIProcessor for {os.path.basename(current_file)}")
            self.log_debug(f"Model: {model_name}, Provider: {provider}")
            
            self.batch_processor = AIProcessor(
                email.body,
                provider,
                model_name,
                max_tokens,
                temperature,
                server_url,
                api_key,
                email.inline_images
            )
            
            self.batch_processor.progress_updated.connect(self.update_batch_progress)
            self.batch_processor.processing_complete.connect(self.on_batch_email_complete)
            self.batch_processor.error_occurred.connect(self.on_batch_email_error)
            self.batch_processor.debug_log.connect(self.log_debug)
            
            # Start processing
            self.log_debug("Starting AIProcessor thread")
            self.batch_processor.start()
            
        except Exception as e:
            self.on_batch_email_error(f"Failed to start processing {os.path.basename(current_file)}: {str(e)}")
    
    def update_batch_progress(self, message: str):
        """Update batch progress display"""
        self.log_debug(f"Batch progress: {message}")
        # Update the status label to show current progress
        self.batch_status_label.setText(f"Status: {message}")
    
    def on_batch_email_complete(self, result: dict):
        """Handle completion of a single email in batch"""
        current_file = self.batch_email_files[self.current_batch_index]
        
        # Store result
        email_result = {
            'file_path': current_file,
            'filename': os.path.basename(current_file),
            'data': result,
            'status': 'success'
        }
        self.batch_results.append(email_result)
        
        # Update progress
        self.batch_progress_bar.setValue(self.current_batch_index + 1)
        self.log_debug(f"Completed email {self.current_batch_index + 1}/{len(self.batch_email_files)}")
        
        # Move to next email
        self.current_batch_index += 1
        self.process_next_batch_email()
    
    def on_batch_email_error(self, error: str):
        """Handle error in batch processing"""
        current_file = self.batch_email_files[self.current_batch_index]
        
        self.log_debug(f"Error processing {os.path.basename(current_file)}: {error}")
        
        # Store error result
        email_result = {
            'file_path': current_file,
            'filename': os.path.basename(current_file),
            'error': error,
            'status': 'error'
        }
        self.batch_results.append(email_result)
        
        # Update progress
        self.batch_progress_bar.setValue(self.current_batch_index + 1)
        self.log_debug(f"Completed email {self.current_batch_index + 1}/{len(self.batch_email_files)} (with error)")
        
        # Move to next email
        self.current_batch_index += 1
        self.process_next_batch_email()
    
    def update_batch_display(self):
        """Update the batch display with current email results"""
        if not self.batch_email_files:
            # No files selected
            self.current_email_label.setText("No emails selected")
            self.batch_items_count_label.setText("Items extracted: 0")
            self.batch_processing_time_label.setText("Processing time: --")
            self.batch_status_label.setText("Status: --")
            self.batch_results_table.setRowCount(0)
            self.batch_results_table.setColumnCount(0)
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            self.batch_export_btn.setEnabled(False)
            self.batch_view_raw_btn.setEnabled(False)
            self.batch_view_email_btn.setEnabled(False)
            return
        
        if not self.batch_results:
            # Files selected but not processed yet
            if self.current_batch_index < len(self.batch_email_files):
                current_file = self.batch_email_files[self.current_batch_index]
                self.current_email_label.setText(f"📧 {os.path.basename(current_file)}")
            else:
                self.current_email_label.setText("No emails processed")
            
            self.batch_items_count_label.setText("Items extracted: 0")
            self.batch_processing_time_label.setText("Processing time: --")
            self.batch_status_label.setText("Status: ⏳ Ready to process")
            self.batch_results_table.setRowCount(0)
            self.batch_results_table.setColumnCount(0)
            
            # Enable navigation buttons for file browsing
            self.prev_btn.setEnabled(self.current_batch_index > 0)
            self.next_btn.setEnabled(self.current_batch_index < len(self.batch_email_files) - 1)
            
            self.batch_export_btn.setEnabled(False)
            self.batch_view_raw_btn.setEnabled(False)
            self.batch_view_email_btn.setEnabled(True)  # Can view email even before processing
            return
        
        # Ensure index is within bounds
        if self.current_batch_index >= len(self.batch_results):
            self.current_batch_index = len(self.batch_results) - 1
        elif self.current_batch_index < 0:
            self.current_batch_index = 0
        
        current_result = self.batch_results[self.current_batch_index]
        
        # Update email label
        self.current_email_label.setText(f"📧 {current_result['filename']}")
        
        # Update navigation buttons
        self.prev_btn.setEnabled(self.current_batch_index > 0)
        self.next_btn.setEnabled(self.current_batch_index < len(self.batch_results) - 1)
        
        if current_result['status'] == 'success':
            # Display successful results
            result_data = current_result['data']
            self.batch_items_count_label.setText(f"Items extracted: {result_data['items_count']}")
            self.batch_processing_time_label.setText(f"Processing time: {result_data.get('processing_time', 0):.2f}s")
            self.batch_status_label.setText("Status: ✅ Success")
            
            # Display results table
            self.display_batch_results(result_data['dataframe'])
            
            # Enable action buttons
            self.batch_export_btn.setEnabled(True)
            self.batch_view_raw_btn.setEnabled(True)
            self.batch_view_email_btn.setEnabled(True)
        else:
            # Display error
            self.batch_items_count_label.setText("Items extracted: 0")
            self.batch_processing_time_label.setText("Processing time: --")
            self.batch_status_label.setText("Status: ❌ Error")
            
            # Clear results table
            self.batch_results_table.setRowCount(0)
            self.batch_results_table.setColumnCount(0)
            
            # Disable action buttons
            self.batch_export_btn.setEnabled(False)
            self.batch_view_raw_btn.setEnabled(False)
            self.batch_view_email_btn.setEnabled(False)
    
    def display_batch_results(self, df: pd.DataFrame):
        """Display batch results in table"""
        self.batch_results_table.setRowCount(len(df))
        self.batch_results_table.setColumnCount(len(df.columns))
        self.batch_results_table.setHorizontalHeaderLabels(df.columns)
        
        for i, row in df.iterrows():
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                self.batch_results_table.setItem(i, j, item)
        
        self.batch_results_table.resizeColumnsToContents()
    
    def previous_email(self):
        """Navigate to previous email in batch"""
        if self.current_batch_index > 0:
            self.current_batch_index -= 1
            self.update_batch_display()
    
    def next_email(self):
        """Navigate to next email in batch"""
        if self.batch_results:
            # After processing - navigate through results
            if self.current_batch_index < len(self.batch_results) - 1:
                self.current_batch_index += 1
                self.update_batch_display()
        elif self.batch_email_files:
            # Before processing - navigate through selected files
            if self.current_batch_index < len(self.batch_email_files) - 1:
                self.current_batch_index += 1
                self.update_batch_display()
    
    def export_batch_to_excel(self):
        """Export current email result to Excel using the new Excel exporter"""
        if not self.batch_results or self.current_batch_index >= len(self.batch_results):
            return
        
        current_result = self.batch_results[self.current_batch_index]
        if current_result['status'] != 'success':
            QMessageBox.warning(self, "Warning", "Cannot export failed email")
            return
        
        try:
            # Check if template is selected
            if self.template_label.text() == "No template selected":
                QMessageBox.warning(self, "Warning", "Please select a template first")
                return
            
            template_path = self.template_label.text()
            if not os.path.isabs(template_path):
                template_path = os.path.join("data", template_path)
            
            # Create Excel exporter with dependency injection
            excel_exporter = create_excel_exporter(
                template_path=template_path,
                output_directory="data",
                starting_row=23
            )
            
            # Generate filename
            timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
            filename = current_result['filename'].replace('.eml', '')
            output_filename = f"{timestamp}_{filename}"
            
            # Export using the new Excel exporter
            df = current_result['data']['dataframe']
            output_path = excel_exporter.export_dataframe(df, output_filename)
            
            QMessageBox.information(self, "Success", f"Exported to: {output_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export: {str(e)}")
    
    def view_batch_raw_output(self):
        """View raw output for current email"""
        if not self.batch_results or self.current_batch_index >= len(self.batch_results):
            return
        
        current_result = self.batch_results[self.current_batch_index]
        if current_result['status'] != 'success':
            QMessageBox.warning(self, "Warning", "No raw output available for failed email")
            return
        
        # Switch to raw output tab and display
        self.raw_output_display.setText(current_result['data']['raw_response'])
        self.centralWidget().findChild(QTabWidget).setCurrentIndex(5)  # Raw Output tab
    
    def view_batch_email(self):
        """View the current email content"""
        if not self.batch_email_files or self.current_batch_index >= len(self.batch_email_files):
            return
        
        current_file = self.batch_email_files[self.current_batch_index]
        
        try:
            # Load and display email preview
            self.load_email_preview(current_file)
            # Switch to processing tab to show email preview
            self.centralWidget().findChild(QTabWidget).setCurrentIndex(2)  # Process Email tab
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load email: {str(e)}")
    
def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show the main window
    window = EmailProcessorGUI()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 