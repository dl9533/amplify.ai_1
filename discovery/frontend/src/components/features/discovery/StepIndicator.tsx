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
  currentStep: _currentStep,
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
            flex items-center gap-2 px-3 py-2 rounded-md transition-colors duration-150
            ${step.status === 'completed' ? 'text-success bg-success/10' : ''}
            ${step.status === 'current' ? 'text-primary bg-primary/10 font-semibold' : ''}
            ${step.status === 'upcoming' ? 'text-foreground-subtle opacity-50' : ''}
          `}
        >
          {step.status === 'completed' && (
            <span className="text-success font-bold" aria-hidden="true">
              ✓
            </span>
          )}
          {step.status === 'current' && (
            <span
              className="w-2 h-2 rounded-full bg-primary"
              aria-hidden="true"
            />
          )}
          {step.status === 'upcoming' && (
            <span
              className="w-2 h-2 rounded-full bg-background-accent"
              aria-hidden="true"
            />
          )}
          <span>{step.title}</span>
        </li>
      ))}
    </ul>
  )
}
