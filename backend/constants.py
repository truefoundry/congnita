from enum import StrEnum

DATA_POINT_FQN_METADATA_KEY = "_data_point_fqn"

DATA_POINT_HASH_METADATA_KEY = "_data_point_hash"

DATA_POINT_SIGNED_URL_METADATA_KEY = "_signed_url"

DATA_POINT_FILE_PATH_METADATA_KEY = "_data_point_file_path"

DEFAULT_BATCH_SIZE = 100

DEFAULT_BATCH_SIZE_FOR_VECTOR_STORE = 1000

FQN_SEPARATOR = "::"

# parser constants

MULTI_MODAL_PARSER_PROMPT = """Given an image containing one or more charts/graphs, and texts, provide a detailed analysis of the data represented in the charts. Your task is to analyze the image and provide insights based on the data it represents.
    Specifically, the information should include but not limited to:
    Title of the Image: Provide a title from the charts or image if any.
    Type of Chart: Determine the type of each chart (e.g., bar chart, line chart, pie chart, scatter plot, etc.) and its key features (e.g., labels, legends, data points).
    Data Trends: Describe any notable trends or patterns visible in the data. This may include increasing/decreasing trends, seasonality, outliers, etc.
    Key Insights: Extract key insights or observations from the charts. What do the charts reveal about the underlying data? Are there any significant findings that stand out?
    Data Points: Identify specific data points or values represented in the charts, especially those that contribute to the overall analysis or insights.
    Comparisons: Compare different charts within the same image or compare data points within a single chart. Highlight similarities, differences, or correlations between datasets.
    Conclude with a summary of the key findings from your analysis and any recommendations based on those findings.
"""
MULTI_MODAL_PARSER_SUPPORTED_IMAGE_EXTENSIONS = [".png", ".jpeg", ".jpg"]
MULTI_MODAL_PARSER_SUPPORTED_PDF_EXTENSION = [".pdf"]
MULTI_MODAL_PARSER_SUPPORTED_FILE_EXTENSIONS = (
    MULTI_MODAL_PARSER_SUPPORTED_IMAGE_EXTENSIONS
    + MULTI_MODAL_PARSER_SUPPORTED_PDF_EXTENSION
)


## Data source types
class DataSourceType(StrEnum):
    TRUEFOUNDRY = "truefoundry"
    LOCAL = "localdir"
    WEB = "web"
    STRUCTURED = "structured"
