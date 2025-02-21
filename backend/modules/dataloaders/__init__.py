from backend.constants import DataSourceType
from backend.modules.dataloaders.loader import register_dataloader
from backend.modules.dataloaders.local_dir_loader import LocalDirLoader
from backend.modules.dataloaders.structured_loader import StructuredLoader
from backend.modules.dataloaders.web_loader import WebLoader
from backend.settings import settings

register_dataloader(DataSourceType.LOCAL, LocalDirLoader)
register_dataloader(DataSourceType.WEB, WebLoader)
register_dataloader(DataSourceType.STRUCTURED, StructuredLoader)

if settings.TFY_API_KEY:
    from backend.modules.dataloaders.truefoundry_loader import TrueFoundryLoader

    register_dataloader(DataSourceType.TRUEFOUNDRY, TrueFoundryLoader)
