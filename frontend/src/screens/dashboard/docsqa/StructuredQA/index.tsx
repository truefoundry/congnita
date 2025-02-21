import React from 'react'
import { StructuredQAProvider } from './context'
import StructuredQA from './StructuredQA'

const index = () => {
  return (
    <StructuredQAProvider>
      <StructuredQA />
    </StructuredQAProvider>
  )
}

export default index
