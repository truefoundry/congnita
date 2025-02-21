import React from 'react'

import DocsQaInformation from '../../DocsQaInformation'

const NoAnswer = () => {
  return (
    <div className="h-[calc(100%-3.125rem)] flex justify-center items-center overflow-y-auto">
      <div className="min-h-[23rem]">
        <DocsQaInformation
          header={'Welcome to DocsQA'}
          subHeader={
            <>
              <p className="text-center max-w-[28.125rem] mt-2">
                Select a collection from sidebar,
                <br /> review all the settings and start asking Questions
              </p>
            </>
          }
        />
      </div>
    </div>
  )
}

export default NoAnswer
