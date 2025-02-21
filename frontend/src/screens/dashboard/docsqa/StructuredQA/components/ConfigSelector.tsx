import React from 'react'

import { FormControl, MenuItem, Select } from '@mui/material'

interface ConfigProps {
  title: string
  placeholder: string
  initialValue: string
  data: any[] | undefined
  handleOnChange: (e: any) => void
  renderItem?: (e: any) => React.ReactNode
  className?: string
}

const ConfigSelector = (props: ConfigProps) => {
  const {
    title,
    placeholder,
    initialValue,
    data,
    className,
    handleOnChange,
    renderItem,
  } = props
  return (
    <div className={`flex justify-between items-center ${className}`}>
      <div className="text-sm">{title}:</div>
      <FormControl>
        <Select
          value={initialValue}
          onChange={(e) => handleOnChange(e)}
          label={placeholder + '...'}
          sx={{
            background: 'white',
            height: '2rem',
            width: '13.1875rem',
            border: '1px solid #CEE0F8 !important',
            outline: 'none !important',
            '& fieldset': {
              border: 'none !important',
            },
          }}
        >
          {data?.map((item: any) =>
            renderItem ? (
              renderItem(item)
            ) : (
              <MenuItem value={item} key={item}>
                {item}
              </MenuItem>
            )
          )}
        </Select>
      </FormControl>
    </div>
  )
}

export default ConfigSelector
