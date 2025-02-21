import Logo from '@/assets/img/logos/CognitaLogo.png'
import LightLogo from '@/assets/img/logos/CognitaLightLogo.png'
import Bars from '@/assets/img/drawer_bars.svg'
import { IconProp } from '@fortawesome/fontawesome-svg-core'
import {
  IconDefinition,
  faDatabase,
  faRocket,
  faGear,
  faPlay,
  faTable,
} from '@fortawesome/free-solid-svg-icons'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { Drawer } from '@mui/material'
import classNames from 'classnames'
import React from 'react'
import { NavLink } from 'react-router-dom'

import IconProvider from '@/components/assets/IconProvider'
import { Link } from 'react-router-dom'
import Button from '@/components/base/atoms/Button'
import { baseQAFoundryPath } from '@/stores/qafoundry'

function getMenuOptions(): {
  label: string
  route: string
  icon: IconDefinition
}[] {
  return [
    {
      label: 'DocsQA',
      route: '/',
      icon: faPlay,
    },
    {
      label: 'StructuredQA',
      route: '/structured',
      icon: faTable,
    },
    {
      label: 'Collections',
      route: '/collections',
      icon: faGear,
    },
    {
      label: 'Data Sources',
      route: '/data-sources',
      icon: faDatabase,
    },
    {
      label: 'Applications',
      route: '/applications',
      icon: faRocket,
    },
  ]
}

export default function NavBar({ children }: any) {
  const [isDrawerOpen, setIsDrawerOpen] = React.useState(false)

  const menu = getMenuOptions().map((menuOption, index) => (
    <div key={index} className="align-middle mt-1 flex items-center">
      <NavLink
        to={menuOption.route}
        className={({ isActive }) =>
          classNames('pb-2 flex flex-row gap-2 items-center', {
            'cursor-default border-b-[3px] border-[#2300F7]': isActive,
            'cursor-pointer border-b-[3px] border-white': !isActive,
          })
        }
      >
        {({ isActive }) => (
          <>
            <FontAwesomeIcon
              icon={menuOption.icon as IconProp}
              className={`text-[12px] ${
                isActive ? 'text-[#2300F7]' : 'text-[#82a0ce]'
              }`}
            />
            <p
              className={
                isActive
                  ? 'text-base font-semibold'
                  : 'text-base font-medium text-gray-500 hover:text-gray-900'
              }
            >
              {menuOption.label}
            </p>
          </>
        )}
      </NavLink>
    </div>
  ))

  return (
    <>
      <Drawer
        anchor={'left'}
        open={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        className="feature-importance"
      >
        <div
          className="bg-white w-[24rem] h-full feature-content text-white font-lab"
          style={{
            background:
              'radial-gradient(246.99% 59.28% at 50.13% 1.56%, #4F46E5 0%, #000000 100%)',
          }}
        >
          <div className="flex items-center gap-4 pt-5 px-8">
            <IconProvider
              icon="xmark"
              className="px-1 cursor-pointer"
              size={1.5}
              onClick={() => setIsDrawerOpen(false)}
            />
            <img src={LightLogo} className="h-8" />
          </div>
          <div className="border-t border-t-[#82A0CE] w-full mt-[1.125rem]"></div>
          <div className="flex flex-col gap-4 py-6 px-8 text-lg font-medium">
            <a
              href="https://www.truefoundry.com/blog/cognita-building-an-open-source-modular-rag-applications-for-production"
              target="_blank"
              className="p-1.5"
            >
              What is Cognita?
            </a>
            <a
              href="https://github.com/truefoundry/cognita"
              target="_blank"
              className="p-1.5 flex gap-2 items-center"
            >
              <IconProvider
                icon={'fa-brands fa-github' as IconProp}
                size={1.125}
              />
              Github
            </a>
            <Button
              className="w-full h-10 bg-white text-black hover:bg-white text-lg font-bold mt-3"
              text="Talk to us"
              onClick={() => {
                window.open(
                  'https://www.truefoundry.com/book-demo?utm_source=cognita&utm_medium=cognita&utm_campaign=cognita',
                  '_blank'
                )
              }}
            />
          </div>
        </div>
      </Drawer>
      <div className="flex flex-col border bg-white font-inter">
        <div className="flex items-center inline-block pl-5 px-5 py-4 gap-x-4 flex-wrap">
          <div className="flex items-center">
            <Link to={'/'} className="mr-6">
              <img src={Logo} className="h-8" />
            </Link>
            <div className="flex gap-5 items-center">{menu}</div>
          </div>

          <div className="flex-1" />
          <Button
            white
            className="btn-xs text-sm h-7"
            text="View All APIs"
            onClick={() => {
              window.open(
                baseQAFoundryPath?.includes('http')
                  ? `${baseQAFoundryPath}/`
                  : `${window.location.origin}${baseQAFoundryPath}/`,
                '_blank'
              )
            }}
          />
          <div
            className="cursor-pointer flex justify-end items-center self-flex-end"
            onClick={() => {
              window.open(
                'https://github.com/truefoundry/docs-qa-playground',
                '_blank'
              )
            }}
          >
            <IconProvider
              icon={'fa-brands fa-github' as IconProp}
              size={1.25}
            />
          </div>
          <Button
            className="btn-xs text-sm h-7 bg-black text-white hover:bg-gray-700"
            text="Tweet"
            icon="x-twitter"
            onClick={() => {
              window.open('https://ctt.ac/XM87B', '_blank')
            }}
          />
          {children}
        </div>
      </div>
    </>
  )
}
