import Badge from '@/components/base/atoms/Badge'
import Button from '@/components/base/atoms/Button'
import LinkButton from '@/components/base/atoms/Link'
import Spinner from '@/components/base/atoms/Spinner/Spinner'
import {
  useGetCollectionDetailsQuery,
  useGetCollectionNamesQuery,
} from '@/stores/qafoundry'
import React, { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import AddDataSourceToCollection from '../AddDataSourceToCollection'
import CollectionCard from '../CollectionCard'
import NewCollection from '../NewCollection'
import NoCollections from '../NoCollections'
import RunsHistoryDrawer from '../RunsHistoryDrawer'
import DataSourcesTable from './DataSourcesTable'

const DocsQASettings = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const [newCollectionModalOpen, setNewCollectionModalOpen] = useState(
    searchParams.get('newCollectionOpen') === 'true'
  )
  const [selectedCollection, setSelectedCollection] = useState<
    string | undefined
  >()
  const [openDataSourceLinkForm, setOpenDataSourceLinkForm] = useState(false)
  const [runsHistoryDrawerOpen, setRunsHistoryDrawerOpen] = useState(false)
  const [selectedDataSourceFqn, setSelectedDataSourceFqn] = useState('')

  const { data: collectionsNames, isLoading: isCollectionsLoading } =
    useGetCollectionNamesQuery()
  const {
    data: collectionDetails,
    isLoading: isCollectionDetailsLoading,
    isFetching: isCollectionDetailsFetching,
  } = useGetCollectionDetailsQuery(selectedCollection ?? '', {
    skip: !selectedCollection || selectedCollection === '',
  })

  const associatedDataSourcesRows = useMemo(() => {
    const rows = []
    if (collectionDetails) {
      for (const [key, value] of Object.entries(
        collectionDetails.associated_data_sources ?? {}
      )) {
        const dataSourceType = key.split(':')[0]
        if (dataSourceType === 'data-dir') {
          rows.push({
            id: key,
            type: 'local',
            source: '-',
            fqn: key,
          })
        } else if (!value?.data_source?.uri) {
          rows.push({
            id: key,
            type: dataSourceType,
            source: '-',
            fqn: key,
          })
        } else {
          rows.push({
            id: key,
            type: dataSourceType,
            source: value.data_source.uri,
            fqn: key,
          })
        }
      }
    }

    return rows
  }, [collectionDetails])

  useEffect(() => {
    if (collectionsNames?.length) {
      if (
        !selectedCollection ||
        !collectionsNames.includes(selectedCollection)
      ) {
        setSelectedCollection(collectionsNames[0])
      }
    } else {
      setSelectedCollection(undefined)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [collectionsNames])

  const openRunsHistoryDrawer = (fqn: string) => {
    setSelectedDataSourceFqn(fqn)
    setRunsHistoryDrawerOpen(true)
  }

  useEffect(() => {
    setNewCollectionModalOpen(searchParams.get('newCollectionOpen') === 'true')
  }, [searchParams])

  return (
    <>
      <div className="flex justify-between">
        <div className="text-[24px] font-bold font-inter">Collections</div>
        <LinkButton
          icon="plus"
          iconClasses="fa-xs text-slate-400"
          text={<span className="whitespace-nowrap">New Collection</span>}
          rounded
          className="bg-black text-white hover:bg-gray-700 btn-sm flex-nowrap mb-4 px-5"
          onClick={() => setNewCollectionModalOpen(true)}
        />
      </div>
      <div className="flex gap-5 flex-1 w-full">
        <div className="h-full bg-[#f0f7ff] rounded-lg py-5 w-[17.5rem] border border-gray-250 pt-3">
          <div
            className="h-[calc(100vh-202px)] overflow-y-auto custom-scrollbar px-3"
            style={{
              paddingRight: '0.75rem',
            }}
          >
            {isCollectionsLoading && <Spinner center />}
            {collectionsNames?.map((collection, index) => (
              <CollectionCard
                key={index}
                collectionName={collection}
                isSelectedCollection={selectedCollection === collection}
                enableErrorSelection
                onClick={() => {
                  setSelectedCollection(collection)
                }}
              />
            ))}
          </div>
        </div>
        {selectedCollection ? (
          <div className="flex-1 border rounded-lg border-[#CEE0F8] w-[calc(100%-300px)] bg-white p-4">
            {isCollectionDetailsFetching || isCollectionDetailsLoading ? (
              <div className="flex justify-center items-center h-full w-full">
                <Spinner center medium />
              </div>
            ) : (
              <>
                <div className="flex justify-between mb-3">
                  <div>
                    <div className="text-base font-medium mb-1">
                      Data Sources for{' '}
                      <Badge
                        text={selectedCollection}
                        type="white"
                        textClasses="text-base"
                      />{' '}
                      collection
                    </div>
                    {collectionDetails && (
                      <div className="text-sm">
                        Embedder Used :{' '}
                        {collectionDetails?.embedder_config?.name}
                      </div>
                    )}
                  </div>
                  <Button
                    white
                    icon={'plus'}
                    iconClasses="text-gray-400"
                    text={'Link Data Source'}
                    className="btn-sm text-sm bg-white"
                    onClick={() => setOpenDataSourceLinkForm(true)}
                  />
                </div>
                <div className="h-[calc(100%-4.125rem)]">
                  <DataSourcesTable
                    collectionName={selectedCollection}
                    rows={associatedDataSourcesRows}
                    openRunsHistoryDrawer={openRunsHistoryDrawer}
                  />
                </div>
              </>
            )}
          </div>
        ) : isCollectionsLoading ? (
          <Spinner center medium />
        ) : (
          <NoCollections />
        )}
      </div>
      {newCollectionModalOpen && (
        <NewCollection
          open={newCollectionModalOpen}
          onClose={(newCollectionName) => {
            if (searchParams.has('newCollectionOpen')) {
              searchParams.delete('newCollectionOpen')
              setSearchParams(searchParams)
            }
            if (newCollectionName) {
              setSelectedCollection(newCollectionName)
            }
            setNewCollectionModalOpen(false)
          }}
        />
      )}
      {selectedCollection && openDataSourceLinkForm && (
        <AddDataSourceToCollection
          open={openDataSourceLinkForm}
          onClose={() => {
            setOpenDataSourceLinkForm(false)
          }}
          collectionName={selectedCollection}
        />
      )}
      {runsHistoryDrawerOpen && selectedCollection && selectedDataSourceFqn && (
        <RunsHistoryDrawer
          open={runsHistoryDrawerOpen}
          onClose={() => setRunsHistoryDrawerOpen(false)}
          collectionName={selectedCollection}
          selectedDataSource={selectedDataSourceFqn}
        />
      )}
    </>
  )
}

export default DocsQASettings
