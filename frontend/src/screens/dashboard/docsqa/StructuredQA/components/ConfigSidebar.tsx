import { MenuItem, Switch, TextareaAutosize } from '@mui/material'
import React from 'react'
import SimpleCodeEditor from '@/components/base/molecules/SimpleCodeEditor'
import ConfigSelector from './ConfigSelector'
import { useStructuredQAContext } from '../context'

const Left = (props: any) => {
  const {
    selectedDataSource,
    selectedQueryModel,
    dataSources,
    description,
    allEnabledModels,
    table,
    tableConfig,
    setSelectedDataSource,
    setSelectedQueryModel,
    setDescription,
    setTable,
    setTableConfig,
    resetQA,
  } = useStructuredQAContext()

  return (
    <div className="h-full border rounded-lg border-[#CEE0F8] w-[23.75rem] bg-white p-4 overflow-auto">
      <div className="flex flex-col gap-3">
        <ConfigSelector
          title="Data Source"
          placeholder="Select Data Source..."
          initialValue={selectedDataSource}
          data={dataSources}
          handleOnChange={(e) => {
            resetQA()
            setSelectedDataSource(e.target.value)
          }}
          renderItem={(item) =>
            item.type === 'structured' && (
              <MenuItem key={item.fqn} value={item.fqn}>
                {/* {item.fqn.split('/').slice(-1)[0]} */}
                {item.fqn}
              </MenuItem>
            )
          }
        />

        {selectedDataSource &&
          (selectedDataSource.includes('postgresql://') ||
            selectedDataSource.includes('mysql://') ||
            selectedDataSource.includes('sqlite://')) && (
            <>
              <div>
                <div className="mb-1 text-sm">Table Name:</div>
                <input
                  type="text"
                  className="w-full bg-[#f0f7ff] border border-[#CEE0F8] rounded-lg p-2 text-sm"
                  placeholder="Enter table name..."
                  value={table}
                  onChange={(e) => setTable(e.target.value)}
                />
              </div>

              <div className="mb-1 mt-3 text-sm">Where Clause (optional):</div>
              <div className="text-xs text-gray-500 mb-2">
                <p>
                  Note: Where clause is optional and filters the data to reduce
                  the size of the dataframe. It is a list of dict, with keys:
                </p>
                <ul className="list-disc ml-4 mt-1">
                  <li>
                    <strong>column:</strong> Filter column name
                  </li>
                  <li>
                    <strong>operator:</strong> Relational condition like '=',
                    '!=', '&lt;', '&gt;', etc
                  </li>
                  <li>
                    <strong>value:</strong> Value to filter on
                  </li>
                </ul>
              </div>
              <SimpleCodeEditor
                language="json"
                height={130}
                defaultValue={tableConfig}
                onChange={(updatedConfig) =>
                  setTableConfig(updatedConfig ?? '')
                }
              />
            </>
          )}

        <ConfigSelector
          title="Model"
          placeholder="Select Model..."
          initialValue={selectedQueryModel}
          data={allEnabledModels}
          handleOnChange={(e) => {
            resetQA()
            setSelectedQueryModel(e.target.value)
          }}
          renderItem={(item) => (
            <MenuItem key={item.name} value={item.name}>
              {item.name}
            </MenuItem>
          )}
        />
      </div>

      <div className="mb-1 mt-2 text-sm">Description (optional):</div>
      <TextareaAutosize
        className="w-full h-20 bg-[#f0f7ff] border border-[#CEE0F8] rounded-lg p-2 text-sm"
        placeholder="E.g: A dataframe / table with countries with their GDPs and happiness scores"
        minRows={3}
        value={description}
        onChange={(e) => setDescription(e.target.value)}
      />
    </div>
  )
}

export default Left
