import { createApi } from '@reduxjs/toolkit/query/react'

// import * as T from './types'
import { createBaseQuery } from '../utils'

export enum ModelType {
  chat = 'chat',
  embedding = 'embedding',
  reranking = 'reranking',
}

export interface ModelConfig {
  name: string
  type?: ModelType
  parameters: {
    temperature?: number
    maximum_length?: number
    top_p?: number
    top_k?: number
    repetition_penalty?: number
    frequency_penalty?: number
    presence_penalty?: number
    stop_sequences?: string[]
  }
}

export interface CollectionQueryDto {
  collection_name?: string
  data_source_fqn?: string
  table?: string
  where?: []
  retriever_name?: string
  retriever_config?: {
    search_type: string
    search_kwargs?: any
    k?: number
    fetch_k?: number
  }
  prompt_template?: string
  description?: string
  query: string
  model_configuration: ModelConfig
  stream?: boolean
  queryController?: string
}

interface DataSource {
  type: string
  uri?: string
  metadata?: object
  fqn: string
}

interface ParserConfig {
  name: string
  parameters?: {
    [key: string]: any
  }
}

export interface AssociatedDataSource {
  data_source_fqn: string
  parser_config: {
    [key: string]: ParserConfig
  }
  data_source: DataSource
}

interface EmbedderConfig {
  name: string
  parameters?: {
    [key: string]: any
  }
}

export interface Collection {
  name: string
  description?: string
  embedder_config: EmbedderConfig
  associated_data_sources: {
    [key: string]: AssociatedDataSource
  }
}

interface AddDataSourcePayload {
  type: string
  uri: string
  metadata?: object
}

interface DataIngestionRun {
  collection_name: string
  data_source_fqn: string
  parser_config?: {
    chunk_size?: number
    chunk_overlap?: number
    parser_map?: {
      [key: string]: string
    }
  }
  data_ingestion_mode: string
  raise_error_on_failure: boolean
  name: string
  status: string
}

export interface SourceDocs {
  page_content: string
  metadata: {
    _data_point_fqn: string
    _data_point_hash: string
    page_num?: number
    page_number?: number
    relevance_score?: number
    file_format?: string
    type: string
    _id: string
    _collection_name: string
  }
  type: string
}

interface QueryAnswer {
  answer: string
  docs: SourceDocs[]
}

export const customerId = 'cognita'

export const baseQAFoundryPath = import.meta.env.VITE_QA_FOUNDRY_URL

export const qafoundryApi = createApi({
  reducerPath: 'qafoundry',
  baseQuery: createBaseQuery({
    baseUrl: baseQAFoundryPath,
  }),
  tagTypes: [
    'Collections',
    'CollectionNames',
    'CollectionDetails',
    'DataSources',
    'Applications',
  ],
  endpoints: (builder) => ({
    // * Queries
    getCollections: builder.query<Collection[], void>({
      query: () => ({
        url: '/v1/collections',
        responseHandler: (response) =>
          response
            .json()
            .then((data: { collections: Collection[] }) => data.collections),
      }),
      providesTags: ['Collections'],
    }),
    getCollectionNames: builder.query<string[], void>({
      query: () => ({
        url: '/v1/collections/list',
        method: 'GET',
        responseHandler: (response) =>
          response
            .json()
            .then((data: { collections: string[] }) => data.collections),
      }),
      providesTags: ['CollectionNames'],
    }),
    getCollectionDetails: builder.query<Collection, string>({
      query: (collectionName) => ({
        url: `/v1/collections/${collectionName}`,
        method: 'GET',
        responseHandler: (response) =>
          response
            .json()
            .then((data: { collection: Collection }) => data.collection),
      }),
      providesTags: ['CollectionDetails'],
    }),
    getCollectionStatus: builder.query({
      query: (payload: { collectionName: string }) => ({
        url: `/v1/collections/data_ingestion_run/${payload.collectionName}/status`,
        method: 'GET',
      }),
    }),
    getDataLoaders: builder.query<any, void>({
      query: () => ({
        url: '/v1/components/dataloaders',
        method: 'GET',
      }),
    }),
    getAllEnabledChatModels: builder.query<any, void>({
      query: () => ({
        url: '/v1/internal/models?model_type=chat',
        method: 'GET',
        responseHandler: (response) =>
          response.json().then((data: { models: object[] }) => data.models),
      }),
    }),
    getAllEnabledEmbeddingModels: builder.query<any, void>({
      query: () => ({
        url: '/v1/internal/models?model_type=embedding',
        method: 'GET',
        responseHandler: (response) =>
          response.json().then((data: { models: object[] }) => data.models),
      }),
    }),
    getDataSources: builder.query<DataSource[], void>({
      query: () => ({
        url: '/v1/data_source/list',
        method: 'GET',
        responseHandler: (response) =>
          response
            .json()
            .then((data: { data_sources: DataSource[] }) => data.data_sources),
      }),
      providesTags: ['DataSources'],
    }),
    getDataIngestionRuns: builder.query<DataIngestionRun[], any>({
      query: (payload: {
        collection_name: string
        data_source_fqn: string
      }) => ({
        url: '/v1/collections/data_ingestion_runs/list',
        body: payload,
        method: 'POST',
        responseHandler: (response) =>
          response
            .json()
            .then(
              (data: { data_ingestion_runs: DataIngestionRun[] }) =>
                data.data_ingestion_runs
            ),
      }),
    }),
    getOpenapiSpecs: builder.query<any, void>({
      query: () => ({
        url: '/openapi.json',
        method: 'GET',
      }),
    }),
    getApplications: builder.query<string[], void>({
      query: () => ({
        url: '/v1/apps/list',
        method: 'GET',
        responseHandler: (response) =>
          response.json().then((data) => data.rag_apps),
      }),
      providesTags: ['Applications'],
    }),
    getApplicationDetailsByName: builder.query<any, string>({
      query: (appName) => ({
        url: `/v1/apps/${appName}`,
        method: 'GET',
        responseHandler: (response) =>
          response.json().then((data) => data.rag_app),
      }),
    }),

    // * Mutations
    uploadDataToDataDirectory: builder.mutation({
      query: (payload: { filepaths: string[]; upload_name: string }) => ({
        url: '/v1/internal/upload-to-data-directory',
        body: payload,
        method: 'POST',
      }),
    }),
    uploadDataToLocalDirectory: builder.mutation<
      { data_source: { fqn: string } },
      {
        files: File[]
        upload_name: string
        is_structured?: boolean
      }
    >({
      query: (payload: {
        files: File[]
        upload_name: string
        is_structured?: boolean
      }) => {
        var bodyFormData = new FormData()
        bodyFormData.append('upload_name', payload.upload_name)
        payload.files.forEach((file) => {
          bodyFormData.append('files', file)
        })
        if (payload.is_structured) {
          bodyFormData.append('is_structured', 'true')
        }
        return {
          url: '/v1/internal/upload-to-local-directory',
          body: bodyFormData,
          method: 'POST',
          formData: true,
        }
      },
    }),
    createCollection: builder.mutation({
      query: (payload: object) => ({
        url: '/v1/collections',
        body: payload,
        method: 'POST',
      }),
      invalidatesTags: ['Collections', 'CollectionNames'],
    }),
    addDocsToCollection: builder.mutation({
      query: (payload: object) => ({
        url: '/v1/collections/associate_data_source',
        body: payload,
        method: 'POST',
      }),
      invalidatesTags: ['Collections', 'CollectionDetails'],
    }),
    unassociateDataSource: builder.mutation({
      query: (payload: object) => ({
        url: '/v1/collections/unassociate_data_source',
        body: payload,
        method: 'POST',
      }),
      invalidatesTags: ['Collections', 'CollectionDetails'],
    }),
    deleteCollection: builder.mutation({
      query: (payload: { collectionName: string }) => ({
        url: `/v1/collections/${payload.collectionName}`,
        body: payload,
        method: 'DELETE',
      }),
      invalidatesTags: ['Collections', 'CollectionNames', 'CollectionDetails'],
    }),
    deleteDataSource: builder.mutation({
      query: (payload: { data_source_fqn: string }) => ({
        url: `/v1/data_source/delete?data_source_fqn=${encodeURIComponent(
          payload.data_source_fqn
        )}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['DataSources'],
    }),
    queryCollection: builder.mutation<
      QueryAnswer,
      CollectionQueryDto & { queryController: string }
    >({
      query: (payload) => ({
        url: `/retrievers/${payload.queryController}/answer`,
        body: payload,
        method: 'POST',
      }),
    }),
    addDataSource: builder.mutation({
      query: (payload: AddDataSourcePayload) => ({
        url: '/v1/data_source',
        body: payload,
        method: 'POST',
      }),
      invalidatesTags: (_result, _opts) => [{ type: 'DataSources' }],
    }),
    ingestDataSource: builder.mutation({
      query: (payload: {
        collection_name: string
        data_source_fqn: string
        data_ingestion_mode: string
        raise_error_on_failure: boolean
        run_as_job: boolean
        batch_size?: number
      }) => ({
        url: '/v1/collections/ingest',
        body: payload,
        method: 'POST',
      }),
      invalidatesTags: ['CollectionDetails'],
    }),
    createApplication: builder.mutation({
      query: (payload: object) => ({
        url: '/v1/apps',
        body: payload,
        method: 'POST',
      }),
      invalidatesTags: ['Applications'],
    }),
    deleteApplication: builder.mutation({
      query: (payload: { app_name: string }) => ({
        url: `/v1/apps/${payload.app_name}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Applications'],
    }),
  }),
})

export const {
  // queries
  useGetCollectionsQuery,
  useGetCollectionNamesQuery,
  useGetCollectionDetailsQuery,
  useGetCollectionStatusQuery,
  useGetAllEnabledChatModelsQuery,
  useGetAllEnabledEmbeddingModelsQuery,
  useGetDataLoadersQuery,
  useGetDataSourcesQuery,
  useGetDataIngestionRunsQuery,
  useGetOpenapiSpecsQuery,
  useGetApplicationsQuery,
  useGetApplicationDetailsByNameQuery,

  // mutations
  useUploadDataToDataDirectoryMutation,
  useUploadDataToLocalDirectoryMutation,
  useCreateCollectionMutation,
  useAddDocsToCollectionMutation,
  useUnassociateDataSourceMutation,
  useDeleteCollectionMutation,
  useDeleteDataSourceMutation,
  useQueryCollectionMutation,
  useAddDataSourceMutation,
  useIngestDataSourceMutation,
  useCreateApplicationMutation,
  useDeleteApplicationMutation,
} = qafoundryApi
