from typing import List

from app.pipeline.stage import Stage


class Pipeline:
    def __init__(self, stages: List[Stage]):
        self.stages = stages

    def run(self, data):
        for stage in self.stages:
            data = stage(data)
        return data