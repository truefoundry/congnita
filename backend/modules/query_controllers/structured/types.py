from typing import List, Optional, Union

from backend.modules.query_controllers.types import ModelConfig
from backend.types import ConfiguredBaseModel


class SQLFilter(ConfiguredBaseModel):
    column: str
    operator: str
    value: Union[str, int, float, bool]


class StructuredQueryInput(ConfiguredBaseModel):
    data_source_fqn: str
    model_configuration: ModelConfig
    query: str
    description: Optional[str] = None
    table: Optional[str] = None
    where: Optional[List[SQLFilter]] = None
