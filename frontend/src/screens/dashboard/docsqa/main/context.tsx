import React, {
  createContext,
  useState,
  useEffect,
  useMemo,
  ReactNode,
  useContext,
} from 'react'

import {
  SourceDocs,
  useGetAllEnabledChatModelsQuery,
  useGetCollectionNamesQuery,
  useGetOpenapiSpecsQuery,
} from '@/stores/qafoundry'

import { DocsQAContextType, SelectedRetrieverType } from './types'

interface DocsQAProviderProps {
  children: ReactNode
}

const defaultRetrieverConfig = `{
  "search_type": "similarity",
  "k": 20,
  "fetch_k": 20,
  "filter": {}
}`

const defaultModelConfig = `{
  "parameters": {
    "temperature": 0.1
  }
}`

const defaultPrompt =
  'Answer the question based only on the following context:\nContext: {context} \nQuestion: {question}'

const DocsQAContext = createContext<DocsQAContextType | undefined>(undefined)

export const DocsQAProvider: React.FC<DocsQAProviderProps> = ({ children }) => {
  const [selectedQueryModel, setSelectedQueryModel] = React.useState('')
  const [selectedCollection, setSelectedCollection] = useState('')
  const [selectedQueryController, setSelectedQueryController] = useState('')
  const [selectedRetriever, setSelectedRetriever] = useState<
    SelectedRetrieverType | undefined
  >()

  const [isInternetSearchEnabled, setIsInternetSearchEnabled] = useState(false)
  const [retrieverConfig, setRetrieverConfig] = useState(defaultRetrieverConfig)
  const [modelConfig, setModelConfig] = useState(defaultModelConfig)
  const [promptTemplate, setPromptTemplate] = useState(defaultPrompt)
  const [sourceDocs, setSourceDocs] = useState<SourceDocs[]>([])
  const [errorMessage, setErrorMessage] = useState(false)
  const [answer, setAnswer] = useState('')
  const [prompt, setPrompt] = useState('')

  const { data: collections, isLoading: isCollectionsLoading } =
    useGetCollectionNamesQuery()
  const { data: allEnabledModels } = useGetAllEnabledChatModelsQuery()
  const { data: openapiSpecs } = useGetOpenapiSpecsQuery()

  const allQueryControllers = useMemo(() => {
    if (!openapiSpecs?.paths) return []
    return Object.keys(openapiSpecs?.paths)
      .filter((path) => path.includes('/retrievers/'))
      .filter((path) => !path.includes('/structured/'))
      .map((str) => {
        var parts = str.split('/')
        return parts[2]
      })
  }, [openapiSpecs])

  const allRetrieverOptions = useMemo(() => {
    const queryControllerPath = `/retrievers/${selectedQueryController}/answer`
    const examples =
      openapiSpecs?.paths[queryControllerPath]?.post?.requestBody?.content?.[
        'application/json'
      ]?.examples
    if (!examples) return []
    return Object.entries(examples).map(([key, value]: [string, any]) => ({
      key,
      name: value.value.retriever_name,
      summary: value.summary,
      config: value.value.retriever_config,
      promptTemplate: value.value.prompt_template ?? defaultPrompt,
    }))
  }, [selectedQueryController, openapiSpecs])

  const resetQA = () => {
    setAnswer('')
    setErrorMessage(false)
    setPrompt('')
  }

  useEffect(() => {
    if (collections && collections.length) setSelectedCollection(collections[0])
  }, [collections])

  useEffect(() => {
    if (allQueryControllers && allQueryControllers.length)
      setSelectedQueryController(allQueryControllers[0])
  }, [allQueryControllers])

  useEffect(() => {
    if (allEnabledModels && allEnabledModels.length) {
      setSelectedQueryModel(allEnabledModels[0].name)
    }
  }, [allEnabledModels])

  useEffect(() => {
    if (allRetrieverOptions && allRetrieverOptions.length) {
      setSelectedRetriever(allRetrieverOptions[0])
      setPromptTemplate(allRetrieverOptions[0].promptTemplate)
    }
  }, [allRetrieverOptions])

  useEffect(() => {
    if (selectedRetriever)
      setRetrieverConfig(JSON.stringify(selectedRetriever.config, null, 2))
  }, [selectedRetriever])

  const value = {
    selectedQueryModel,
    selectedCollection,
    selectedQueryController,
    selectedRetriever,
    prompt,
    answer,
    sourceDocs,
    errorMessage,
    modelConfig,
    retrieverConfig,
    promptTemplate,
    isInternetSearchEnabled,
    collections,
    isCollectionsLoading,
    allEnabledModels,
    allQueryControllers,
    allRetrieverOptions,
    setSelectedQueryModel,
    setSelectedCollection,
    setSelectedQueryController,
    setSelectedRetriever,
    setSourceDocs,
    setErrorMessage,
    setModelConfig,
    setRetrieverConfig,
    setPromptTemplate,
    setIsInternetSearchEnabled,
    resetQA,
    setPrompt,
    setAnswer,
  }

  return (
    <DocsQAContext.Provider value={value}>{children}</DocsQAContext.Provider>
  )
}

export const useDocsQAContext = () => {
  const context = useContext(DocsQAContext)
  if (!context) {
    throw new Error('useDocsQAContext must be used within a DocsQAProvider')
  }
  return context
}
