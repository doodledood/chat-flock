from typing import Any, Callable, Dict, Generator, Generic, Optional, Sequence, TypeVar

T = TypeVar("T")


class Step(Generic[T]):
    def __init__(
        self,
        name: str,
        func: Callable[[T, Any], Optional[Generator[T, None, None]]],
        on_step_start: Optional[Callable[[T], None]] = None,
        on_step_completed: Optional[Callable[[T], None]] = None,
        on_step_failed: Optional[Callable[[T], None]] = None,
    ):
        self.name = name
        self.func = func
        self.on_step_start = on_step_start
        self.on_step_completed = on_step_completed
        self.on_step_failed = on_step_failed

    def run(self, state: T, **kwargs: Any) -> Generator[T, None, None]:
        res = self.func(state, **kwargs)  # type: ignore
        if res is None:
            return

        for new_state in res:
            yield new_state


class SequentialProcess(Generic[T]):
    def __init__(self, steps: Sequence[Step[T]], initial_state: T, save_state: Callable[[T], None]):
        self.steps = steps
        self.state = initial_state
        self.save_state_func = save_state

    def save_state(self, state: T) -> None:
        self.save_state_func(state)

    def run(self) -> T:
        for step in self.steps:
            if step.on_step_start:
                step.on_step_start(self.state)

            try:
                for new_state in step.run(self.state) or []:
                    self.state = new_state
                    self.save_state(state=self.state)

                self.save_state(state=self.state)

                if step.on_step_completed:
                    step.on_step_completed(self.state)
            except Exception as e:
                if step.on_step_failed:
                    step.on_step_failed(self.state)

                raise e

        return self.state
