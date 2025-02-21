export interface FormInputData {
  dataSourceType: string
  dataSourceUri?: string
  localdir?: {
    name: string
    files: FileObject[]
  }
  webConfig?: {
    use_sitemap: boolean
  }
  structured?: {
    type: 'file' | 'database'
    connectionString?: string
  }
}

export type FileObject = {
  id: string
  file: File
}
