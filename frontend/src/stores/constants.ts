export const IS_DOCS_QA_REDIRECT_ENABLED =
  import.meta.env.VITE_DOCS_QA_ENABLE_REDIRECT === 'true'
export const DOCS_QA_STANDALONE_PATH = import.meta.env
  .VITE_DOCS_QA_STANDALONE_PATH
export const DOCS_QA_MAX_UPLOAD_SIZE_MB = parseInt(
  import.meta.env.VITE_DOCS_QA_MAX_UPLOAD_SIZE_MB || '200'
)
export const IS_LOCAL_DEVELOPMENT = import.meta.env.VITE_USE_LOCAL === 'true'
export const GTAG_ID = import.meta.env.VITE_GTAG_ID

// https://stackoverflow.com/a/58172035/7799568
export const WEBPAGE_URL_REGEX =
  '[Hh][Tt][Tt][Pp][Ss]?://(?:(?:[a-zA-Z\u00a1-\uffff0-9]+-?)*[a-zA-Z\u00a1-\uffff0-9]+)(?:.(?:[a-zA-Z\u00a1-\uffff0-9]+-?)*[a-zA-Z\u00a1-\uffff0-9]+)*(?:.(?:[a-zA-Z\u00a1-\uffff]{2,}))(?::d{2,5})?(?:/[^s]*)?'

// DATA SOURCES

export const WEB_SOURCE_NAME = 'web'
export const LOCAL_SOURCE_NAME = 'localdir'
export const TFY_SOURCE_NAME = 'truefoundry'
export const STRUCTURED_SOURCE_NAME = 'structured'
