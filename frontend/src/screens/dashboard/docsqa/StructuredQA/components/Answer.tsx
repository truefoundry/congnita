import React from 'react'
import IconProvider from '@/components/assets/IconProvider'
import Markdown from 'react-markdown'
import { useStructuredQAContext } from '../context'

const Answer = (props: any) => {
  const { answer, image_base64 } = useStructuredQAContext()

  return (
    <div className="overflow-y-auto flex flex-col gap-4 mt-7 h-[calc(100%-70px)]">
      <div className="max-h h-full overflow-y-auto flex gap-4">
        <div className="bg-indigo-400 w-6 h-6 rounded-full flex items-center justify-center mt-0.5">
          <IconProvider icon="message" className="text-white" />
        </div>
        <div className="w-full font-inter text-base">
          <div className="font-bold text-lg">Answer:</div>
          <Markdown>{answer}</Markdown>
          {image_base64 && (
            <div className="w-full">
              <img src={`data:image/png;base64,${image_base64}`} alt="answer" />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Answer
