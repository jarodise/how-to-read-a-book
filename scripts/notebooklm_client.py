#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NotebookLM Client - Wrapper for notebooklm-py CLI operations.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, List, Dict, Tuple


class NotebookLMError(Exception):
    """Raised when NotebookLM CLI operations fail."""
    pass


class NotebookLMClient:
    """Client for interacting with NotebookLM CLI."""

    def __init__(self, timeout: int = 120):
        self.timeout = timeout

    def _run_command(self, args: List[str]) -> Tuple[bool, str]:
        """
        Run a notebooklm command and return (success, output).
        """
        try:
            result = subprocess.run(
                ["notebooklm"] + args,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            output = result.stdout + result.stderr
            return result.returncode == 0, output
        except subprocess.TimeoutExpired:
            return False, f"Command timed out after {self.timeout}s"
        except FileNotFoundError:
            return False, "notebooklm command not found"
        except Exception as e:
            return False, str(e)

    def check_installed(self) -> bool:
        """Check if notebooklm CLI is installed."""
        return shutil.which("notebooklm") is not None

    def check_authenticated(self) -> bool:
        """Check if user is authenticated with NotebookLM."""
        success, _ = self._run_command(["list"])
        return success

    def create_notebook(self, title: str) -> Optional[str]:
        """
        Create a new notebook and return its ID.
        """
        print(f"📚 Creating notebook: {title}")

        success, output = self._run_command(["create", title])

        if not success:
            raise NotebookLMError(f"Failed to create notebook: {output}")

        # Parse output for notebook ID (UUID pattern)
        for line in output.split("\n"):
            match = re.search(r'[a-f0-9-]{36}', line)
            if match:
                notebook_id = match.group(0)
                print(f"✅ Created notebook: {notebook_id}")
                return notebook_id

        # Fallback: try to extract from last word
        words = output.strip().split()
        if words:
            return words[-1]

        raise NotebookLMError(f"Could not extract notebook ID from output: {output}")

    def set_active_notebook(self, notebook_id: str) -> bool:
        """
        Set the active notebook context.
        """
        success, output = self._run_command(["use", notebook_id])
        return success

    def upload_source(self, notebook_id: str, file_path: str) -> bool:
        """
        Upload a file as a source to the notebook.
        """
        filename = os.path.basename(file_path)
        print(f"  📄 Uploading: {filename}")

        # Set notebook context first
        if not self.set_active_notebook(notebook_id):
            print(f"    ❌ Failed to set notebook context")
            return False

        # Upload the file
        success, output = self._run_command(["source", "add", file_path])

        if success:
            print(f"    ✅ Uploaded")
            return True
        else:
            print(f"    ❌ Failed: {output}")
            return False

    def configure_notebook(self, notebook_id: str, prompt_path: str) -> bool:
        """
        Configure notebook with custom persona prompt.
        """
        if not os.path.exists(prompt_path):
            raise NotebookLMError(f"Prompt file not found: {prompt_path}")

        print(f"⚙️  Configuring notebook with reading companion persona...")

        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt = f.read()
        except Exception as e:
            raise NotebookLMError(f"Failed to read prompt file: {e}")

        # Apply configuration
        success, output = self._run_command([
            "configure",
            "--notebook", notebook_id,
            "--persona", prompt,
            "--response-length", "longer"
        ])

        if success:
            print(f"  ✅ Persona configured")
            return True
        else:
            raise NotebookLMError(f"Failed to configure notebook: {output}")

    def upload_all_sources(self, notebook_id: str, file_paths: List[str]) -> Dict[str, List[str]]:
        """
        Upload multiple files and return results summary.
        """
        results = {"success": [], "failed": []}

        for file_path in file_paths:
            if self.upload_source(notebook_id, file_path):
                results["success"].append(file_path)
            else:
                results["failed"].append(file_path)

        return results
