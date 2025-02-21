import React, { useState } from 'react'

import Spinner from '@/components/base/atoms/Spinner'
import { useStructuredQAContext } from '../context'
import PromptForm from './PromptForm'
import ErrorAnswer from './ErrorAnswer'
import Answer from './Answer'
import NoAnswer from './NoAnswer'

const Right = () => {
  const { errorMessage, answer } = useStructuredQAContext()

  const [isRunningPrompt, setIsRunningPrompt] = useState(false)

  return (
    <div className="h-full border rounded-lg border-[#CEE0F8] w-[calc(100%-25rem)] bg-white p-4">
      <PromptForm
        isRunningPrompt={isRunningPrompt}
        setIsRunningPrompt={setIsRunningPrompt}
      />
      {answer ? (
        <Answer />
      ) : isRunningPrompt ? (
        <div className="overflow-y-auto flex flex-col justify-center items-center gap-2 h-[calc(100%-4.375rem)]">
          <Spinner center medium />
          <div className="text-center">Fetching Answer...</div>
        </div>
      ) : errorMessage ? (
        <ErrorAnswer />
      ) : (
        <NoAnswer />
      )}
    </div>
  )
}

export default Right
