from abc import abstractmethod, ABC
from typing import Any

from app.pipeline.pipeline_calls import StageCall


class Stage(ABC):
    @abstractmethod
    def __call__(self, stage_call: StageCall) -> Any:
        """Transform data from previous stage and return output."""