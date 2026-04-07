import asyncio
from core.orchestrator import orchestrator
from core.structured_logger import system_logger

class RoomDesignPipeline:
    """
    Autonomous Room Design Pipeline (Pixel -> HQ).
    Shows stages: Input, Semantic Understanding, Planning, Rendering.
    """
    def __init__(self):
        self.is_running = False
        self.history = []

    async def execute_pipeline(self, image_input: str):
        if self.is_running:
            orchestrator.emit_error("Pipeline is already processing an image.")
            return

        self.is_running = True
        self.history = []
        orchestrator.emit_state_update("Room Design Pipeline Started")

        try:
            await self._stage_input_processing(image_input)
            await self._stage_semantic_understanding()
            await self._stage_planning()
            await self._stage_hq_rendering()

            orchestrator.emit_tool_result("Room_Pipeline", "HQ Render Complete. Saved to gallery.")
        except asyncio.CancelledError:
            orchestrator.emit_error("Pipeline Interrupted")
        except Exception as e:
            orchestrator.emit_error(f"Pipeline Failed: {str(e)}")
            system_logger.error(f"RoomDesign Error: {e}")
        finally:
            self.is_running = False

    async def _stage_input_processing(self, image_input: str):
        orchestrator.events.publish("SUBTASK_START", {"name": "Input Processing: Feature Extraction"})
        orchestrator.emit_reasoning_step("Stage 1/4", "Parsing pixel noise and extracting rough features", 0.85)
        self.history.append("Input Processing: OK")
        await asyncio.sleep(2) # simulate heavy compute

    async def _stage_semantic_understanding(self):
        orchestrator.events.publish("SUBTASK_START", {"name": "Semantic Understanding: Segmentation"})
        orchestrator.emit_reasoning_step("Stage 2/4", "Classifying furniture and layout dimensions", 0.90)
        self.history.append("Semantic Understanding: OK")
        await asyncio.sleep(2)

    async def _stage_planning(self):
        orchestrator.events.publish("SUBTASK_START", {"name": "Planning: Spatial Optimization"})
        orchestrator.emit_reasoning_step("Stage 3/4", "Optimizing space and aligning stylistic lighting", 0.92)
        self.history.append("Planning: OK")
        await asyncio.sleep(2.5)

    async def _stage_hq_rendering(self):
        orchestrator.events.publish("SUBTASK_START", {"name": "HQ Rendering: Final Composition"})
        orchestrator.emit_reasoning_step("Stage 4/4", "Upscaling textures and compositing final output", 0.98)
        self.history.append("Rendering: OK")
        await asyncio.sleep(3)

# Global singleton
room_pipeline = RoomDesignPipeline()
