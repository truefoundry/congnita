import React from 'react'
import classNames from '@/utils/classNames'

interface RadioGroupProps {
  label: string
  value: string
  onChange: (value: any) => void
  options: Array<{
    label: string
    value: string
  }>
}

export const RadioGroup: React.FC<RadioGroupProps> = ({
  label,
  value,
  onChange,
  options,
}) => {
  return (
    <div className="form-control">
      <label className="label">
        <span className="label-text font-inter">{label}</span>
      </label>
      <div className="flex gap-4">
        {options.map((option) => (
          <label
            key={option.value}
            className={classNames(
              'flex items-center gap-2 cursor-pointer p-2 rounded',
              value === option.value ? 'bg-gray-250' : ''
            )}
          >
            <input
              type="radio"
              className="radio"
              checked={value === option.value}
              onChange={() => onChange(option.value)}
            />
            <span>{option.label}</span>
          </label>
        ))}
      </div>
    </div>
  )
}
