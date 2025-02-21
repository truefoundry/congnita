import React from 'react'
import IconProvider from '@/components/assets/IconProvider'

const ErrorAnswer = () => {
  return (
    <div className="overflow-y-auto flex gap-4 mt-7">
      <div className="bg-error w-6 h-6 rounded-full flex items-center justify-center mt-0.5">
        <IconProvider icon="message" className="text-white" />
      </div>
      <div className="w-full font-inter text-base text-error">
        <div className="font-bold text-lg">Error</div>
        We failed to get answer for your query, please try again by resending
        query or try again in some time.
      </div>
    </div>
  )
}

export default ErrorAnswer
