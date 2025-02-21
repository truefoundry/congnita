from backend.modules.query_controllers.example.controller import BasicRAGQueryController
from backend.modules.query_controllers.multimodal.controller import (
    MultiModalRAGQueryController,
)
from backend.modules.query_controllers.query_controller import register_query_controller
from backend.modules.query_controllers.structured.controller import (
    StructuredQueryController,
)

register_query_controller("basic-rag", BasicRAGQueryController)
register_query_controller("multimodal", MultiModalRAGQueryController)
register_query_controller("structured", StructuredQueryController)
