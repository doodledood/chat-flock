from typing import List, Optional, Type, Any

from halo import Halo
from langchain import pydantic_v1
from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain.tools import BaseTool

from .base import CodeExecutor


class CodeExecutionToolArgs(pydantic_v1.BaseModel):
    python_code: str = pydantic_v1.Field(
        description='The verbatim python code to execute. Ensure code prints something or else the result will not be '
                    'captured. You do not have access to any external libraries. Use vanilla python 3 ONLY.')
    dependencies: Optional[List[str]] = pydantic_v1.Field(
        description='List of pip dependencies to install before executing code. Ensure you specify the version, e.g. '
                    '"requests==2.26.0". You can also specify the version using the "<" and ">" operators, e.g. '
                    '"requests>2.26.0".',
        default=None)


class CodeExecutionTool(BaseTool):
    executor: CodeExecutor
    name: str = 'code_executor'
    description: str = ('Use this for any capability you are missing that you think some python code will solve. That '
                        'includes math, time, data analysis, etc. Code will get executed and the result will be '
                        'returned as a string. Please specify dependencies if you want to use them in code.')
    args_schema: Type[pydantic_v1.BaseModel] = CodeExecutionToolArgs
    progress_text: str = '🐍 Executing code...'
    spinner: Optional[Halo] = None

    def _run(
            self,
            python_code: str,
            dependencies: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForToolRun] = None,
            **kwargs: Any
    ) -> Any:
        if self.spinner is not None:
            self.spinner.stop_and_persist(symbol='🐍',
                                          text='Will execute the following code:\n```\n' + python_code + '\n```')
            self.spinner.start(self.progress_text)

        res = self.executor.execute(code=python_code, dependencies=dependencies)

        return res
