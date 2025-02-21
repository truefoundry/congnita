import React, { useState } from 'react'
// import { SSE } from 'sse.js'

import { baseQAFoundryPath, CollectionQueryDto } from '@/stores/qafoundry'
import Input from '@/components/base/atoms/Input'
import Button from '@/components/base/atoms/Button'
import { useStructuredQAContext } from '../context'
import { notifyError } from '@/utils/error'

const Form = (props: any) => {
  const {
    setErrorMessage,
    setImageBase64,
    setAnswer,
    setPrompt,
    setTable,
    prompt,
    answer,
    image_base64,
    description,
    table,
    selectedQueryModel,
    allEnabledModels,
    selectedDataSource,
    selectedQueryController,
    tableConfig,
  } = useStructuredQAContext()

  const { isRunningPrompt, setIsRunningPrompt } = props

  const handlePromptSubmit = async () => {
    setIsRunningPrompt(true)
    setAnswer('')
    setErrorMessage(false)
    try {
      const selectedModel = allEnabledModels.find(
        (model: any) => model.name == selectedQueryModel
      )
      if (!selectedModel) {
        throw new Error('Model not found')
      }

      try {
        JSON.parse(tableConfig)
      } catch (err: any) {
        throw new Error('Invalid Table Configuration')
      }

      const params: CollectionQueryDto = Object.assign({
        data_source_fqn: selectedDataSource,
        query: prompt,
        model_configuration: {
          name: selectedModel.name,
          provider: selectedModel.provider,
        },
        description: description,
      })

      if (
        selectedDataSource.includes('postgresql://') ||
        selectedDataSource.includes('mysql://') ||
        selectedDataSource.includes('sqlite://')
      ) {
        params.table = table
        params.where = JSON.parse(tableConfig)
      }

      try {
        const response = await fetch(
          `${baseQAFoundryPath}/retrievers/structured/answer`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(params),
          }
        )

        if (!response.ok) {
          const error = await response.json()
          throw new Error(error.detail[0].msg)
        }

        const data = await response.json()
        if (data?.type === 'answer') {
          setAnswer(data.content)
          setImageBase64(data.image_base64 ?? '')
          setIsRunningPrompt(false)
        }
      } catch (err: any) {
        setPrompt('')
        setIsRunningPrompt(false)
        notifyError('Failed to retrieve answer', { message: err.message })
      }
    } catch (err: any) {
      setPrompt('')
      setIsRunningPrompt(false)
      notifyError('Failed to retrieve answer', err)
    }
  }

  return (
    <div className="flex gap-4 items-center">
      <form className="w-full relative" onSubmit={(e) => e.preventDefault()}>
        <Input
          className="w-full min-h-[2.75rem] text-sm pr-14"
          placeholder="Ask any question related to this document"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
        />
        <Button
          icon="paper-plane-top"
          className="btn-sm btn-neutral absolute right-2 top-[0.375rem]"
          onClick={handlePromptSubmit}
          loading={isRunningPrompt}
          disabled={!prompt || !selectedQueryModel}
        />
      </form>
    </div>
  )
}

export default Form
