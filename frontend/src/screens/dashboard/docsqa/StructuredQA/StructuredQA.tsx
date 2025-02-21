import React, { useState } from 'react'

import Spinner from '@/components/base/atoms/Spinner/Spinner'
import NoCollections from '../NoCollections'
import { useStructuredQAContext } from './context'
import ConfigSidebar from './components/ConfigSidebar'
import Chat from './components/Chat'

const StructuredQA = () => {
  const { selectedDataSource, isDataSourcesLoading } = useStructuredQAContext()

  return (
    <>
      <div className="flex gap-5 h-[calc(100vh-6.5rem)] w-full">
        {isDataSourcesLoading ? (
          <div className="h-full w-full flex items-center">
            <Spinner center big />
          </div>
        ) : selectedDataSource ? (
          <>
            <ConfigSidebar />
            <Chat />
          </>
        ) : (
          <NoCollections fullWidth />
        )}
      </div>
    </>
  )
}

export default StructuredQA
