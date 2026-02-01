import React from 'react'

export interface Step {
  id: number
  title: string
  status: 'completed' | 'current' | 'upcoming'
}

export interface StepIndicatorProps {
  steps: Step[]
  currentStep: number
  orientation?: 'horizontal' | 'vertical'
}

export function StepIndicator({
  steps,
  currentStep,
  orientation = 'horizontal',
}: StepIndicatorProps): React.ReactElement {
  const isVertical = orientation === 'vertical'

  return (
    <ul
      className={`flex ${isVertical ? 'flex-col' : ''} gap-2`}
      role="list"
    >
      {steps.map((step) => (
        <li
          key={step.id}
          data-status={step.status}
          className={`
            flex items-center gap-2 px-3 py-2 rounded-md
            ${step.status === 'completed' ? 'text-green-700 bg-green-50' : ''}
            ${step.status === 'current' ? 'text-blue-700 bg-blue-100 font-semibold' : ''}
            ${step.status === 'upcoming' ? 'text-gray-500 opacity-50' : ''}
          `}
        >
          {step.status === 'completed' && (
            <span className="text-green-600 font-bold" aria-hidden="true">
              ✓
            </span>
          )}
          {step.status === 'current' && (
            <span
              className="w-2 h-2 rounded-full bg-blue-600"
              aria-hidden="true"
            />
          )}
          {step.status === 'upcoming' && (
            <span
              className="w-2 h-2 rounded-full bg-gray-300"
              aria-hidden="true"
            />
          )}
          <span>{step.title}</span>
        </li>
      ))}
    </ul>
  )
}
