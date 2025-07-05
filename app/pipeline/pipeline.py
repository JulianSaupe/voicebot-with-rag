from typing import List

from app.pipeline.pipeline_calls import StageCall
from app.pipeline.stages.stage import Stage


class Pipeline:
    def __init__(self, stages: List[Stage]):
        self.stages = stages

    def run(self, data: StageCall):
        for stage in self.stages:
            data = stage(data)
        return data