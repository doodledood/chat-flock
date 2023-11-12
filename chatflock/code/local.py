import io
import sys
import traceback
import subprocess
from typing import Optional, Sequence

from halo import Halo

from .base import CodeExecutor


class LocalCodeExecutor(CodeExecutor):
    def __init__(self, spinner: Optional[Halo] = None):
        self.spinner = spinner

    def execute(self, code: str, dependencies: Optional[Sequence[str]] = None) -> str:
        captured_output = io.StringIO()
        saved_stdout = sys.stdout
        sys.stdout = captured_output

        # Install dependencies before executing code using pip
        if dependencies is not None:
            if self.spinner is not None:
                self.spinner.start('🐍 Installing dependencies...')

            subprocess.check_call([sys.executable, "-m", "pip", "install", *dependencies])

            if self.spinner is not None:
                self.spinner.stop_and_persist(symbol='🐍', text='Dependencies installed.')

        local_vars = {}

        if self.spinner is not None:
            self.spinner.start('🐍 Executing code...')

        try:
            for line in code.splitlines(keepends=False):
                if not line:
                    continue

                exec(code, None, local_vars)
        except:
            return f'Error executing code: {traceback.format_exc()}'
        finally:
            sys.stdout = saved_stdout

        if self.spinner is not None:
            self.spinner.stop_and_persist(symbol='🐍', text='Code executed.')

        res = captured_output.getvalue()

        return res
