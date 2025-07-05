from typing import List, AsyncGenerator, Any
import asyncio

from app.pipeline.pipeline_calls import StageCall
from app.pipeline.stages.stage import Stage


class AsyncPipeline:
    def __init__(self, stages: List[Stage]):
        self.stages = stages

    async def run(self, data: StageCall) -> AsyncGenerator[Any, None]:
        """Run pipeline with async generator support."""
        current_data = data
        
        try:
            for i, stage in enumerate(self.stages):
                try:
                    if i == len(self.stages) - 1:
                        # Last stage - yield results as they come
                        result = stage(current_data)
                        if hasattr(result, '__aiter__'):
                            # Async generator
                            async for item in result:
                                yield item
                        else:
                            # Regular generator or single value
                            if hasattr(result, '__iter__') and not isinstance(result, str):
                                for item in result:
                                    yield item
                            else:
                                yield result
                    else:
                        # Intermediate stage
                        current_data = stage(current_data)
                        
                except Exception as e:
                    print(f"Error in pipeline stage {i} ({stage.__class__.__name__}): {e}")
                    import traceback
                    traceback.print_exc()
                    break
                    
        except Exception as e:
            print(f"Fatal error in pipeline: {e}")
            import traceback
            traceback.print_exc()