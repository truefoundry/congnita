import React, {
  createContext,
  useState,
  useEffect,
  ReactNode,
  useContext,
} from 'react'

import {
  useGetAllEnabledChatModelsQuery,
  useGetDataSourcesQuery,
} from '@/stores/qafoundry'

import { StructuredQAContextType, SelectedTableConfigType } from './types'

interface StructuredQAProviderProps {
  children: ReactNode
}

const defaultTableConfig = `[
  {
    "column": "",
    "operator": "",
    "value": ""
  }
]`

const StructuredQAContext = createContext<StructuredQAContextType | undefined>(
  undefined
)

export const StructuredQAProvider: React.FC<StructuredQAProviderProps> = ({
  children,
}) => {
  const [selectedQueryModel, setSelectedQueryModel] = React.useState('')
  const [selectedDataSource, setSelectedDataSource] = useState('')
  const [table, setTable] = useState('')
  const [tableConfig, setTableConfig] = useState(defaultTableConfig)
  const [selectedTableConfig, setSelectedTableConfig] = useState<
    SelectedTableConfigType[] | undefined
  >([])
  const [selectedQueryController, setSelectedQueryController] =
    useState('structured')

  const [errorMessage, setErrorMessage] = useState(false)
  const [answer, setAnswer] = useState('')
  const [image_base64, setImageBase64] = useState('')
  const [prompt, setPrompt] = useState('')
  const [description, setDescription] = useState('')

  const { data: dataSources, isLoading: isDataSourcesLoading } =
    useGetDataSourcesQuery()
  const { data: allEnabledModels } = useGetAllEnabledChatModelsQuery()

  const resetQA = () => {
    setAnswer('')
    setErrorMessage(false)
    setPrompt('')
  }

  useEffect(() => {
    if (dataSources && dataSources.length)
      setSelectedDataSource(dataSources[0].fqn)
  }, [dataSources])

  useEffect(() => {
    if (allEnabledModels && allEnabledModels.length) {
      setSelectedQueryModel(allEnabledModels[0].name)
    }
  }, [allEnabledModels])

  useEffect(() => {
    if (tableConfig) setSelectedTableConfig(JSON.parse(tableConfig))
  }, [tableConfig])

  const value = {
    selectedQueryModel,
    selectedDataSource,
    dataSources,
    selectedQueryController,
    prompt,
    answer,
    image_base64,
    errorMessage,
    description,
    isDataSourcesLoading,
    allEnabledModels,
    table,
    tableConfig,
    selectedTableConfig,
    setSelectedQueryModel,
    setAnswer,
    setImageBase64,
    setPrompt,
    setSelectedDataSource,
    setTable,
    setTableConfig,
    setSelectedTableConfig,
    setErrorMessage,
    resetQA,
    setDescription,
  }

  return (
    <StructuredQAContext.Provider value={value}>
      {children}
    </StructuredQAContext.Provider>
  )
}

export const useStructuredQAContext = () => {
  const context = useContext(StructuredQAContext)
  if (!context) {
    throw new Error(
      'useStructuredQAContext must be used within a StructuredQAProvider'
    )
  }
  return context
}
