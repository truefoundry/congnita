export interface SelectedTableConfigType {
  column: string
  operator: string
  value: string
}

export interface StructuredQAContextType {
  selectedQueryModel: string
  selectedDataSource: string
  // FIXME: add type
  dataSources: any
  table: string
  tableConfig: string
  selectedTableConfig: SelectedTableConfigType[] | undefined
  selectedQueryController: string
  prompt: string
  answer: string
  image_base64: string
  errorMessage: boolean
  description: string
  isDataSourcesLoading: boolean
  allEnabledModels: any

  setSelectedQueryModel: React.Dispatch<React.SetStateAction<string>>
  setSelectedDataSource: React.Dispatch<React.SetStateAction<string>>
  setAnswer: React.Dispatch<React.SetStateAction<string>>
  setPrompt: React.Dispatch<React.SetStateAction<string>>
  setImageBase64: React.Dispatch<React.SetStateAction<string>>
  setErrorMessage: React.Dispatch<React.SetStateAction<boolean>>
  setDescription: React.Dispatch<React.SetStateAction<string>>
  setTable: React.Dispatch<React.SetStateAction<string>>
  setTableConfig: React.Dispatch<React.SetStateAction<string>>
  setSelectedTableConfig: React.Dispatch<
    React.SetStateAction<SelectedTableConfigType[] | undefined>
  >
  resetQA: () => void
}
