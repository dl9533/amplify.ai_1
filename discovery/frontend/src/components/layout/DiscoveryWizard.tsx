import { ReactNode, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import {
  IconStepUpload,
  IconStepMap,
  IconStepActivities,
  IconStepAnalysis,
  IconStepRoadmap,
  IconCheck,
  IconArrowLeft,
  IconArrowRight,
  IconChat,
  IconX,
} from '../ui/Icons'
import { ChatPanel } from '../features/discovery/ChatPanel'

// Step configuration
export const DISCOVERY_STEPS = [
  {
    id: 1,
    key: 'upload',
    title: 'Upload',
    description: 'Import workforce data',
    icon: IconStepUpload,
    path: 'upload',
  },
  {
    id: 2,
    key: 'map-roles',
    title: 'Map Roles',
    description: 'Match to O*NET occupations',
    icon: IconStepMap,
    path: 'map-roles',
  },
  {
    id: 3,
    key: 'activities',
    title: 'Activities',
    description: 'Select work activities',
    icon: IconStepActivities,
    path: 'activities',
  },
  {
    id: 4,
    key: 'analysis',
    title: 'Analysis',
    description: 'Review automation scores',
    icon: IconStepAnalysis,
    path: 'analysis',
  },
  {
    id: 5,
    key: 'roadmap',
    title: 'Roadmap',
    description: 'Prioritize candidates',
    icon: IconStepRoadmap,
    path: 'roadmap',
  },
] as const

interface DiscoveryWizardProps {
  children: ReactNode
  currentStep: number
  onStepChange?: (step: number) => void
  sessionName?: string
  canProceed?: boolean
}

export function DiscoveryWizard({
  children,
  currentStep,
  onStepChange,
  sessionName,
  canProceed = true,
}: DiscoveryWizardProps) {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const [chatOpen, setChatOpen] = useState(false)

  const handleStepClick = (stepId: number) => {
    // Only allow navigating to completed steps or current step
    if (stepId <= currentStep && onStepChange) {
      onStepChange(stepId)
      const step = DISCOVERY_STEPS.find(s => s.id === stepId)
      if (step && sessionId) {
        navigate(`/discovery/${sessionId}/${step.path}`)
      }
    }
  }

  const handleNext = () => {
    if (currentStep < 5 && canProceed) {
      const nextStep = DISCOVERY_STEPS[currentStep]
      if (nextStep && sessionId) {
        navigate(`/discovery/${sessionId}/${nextStep.path}`)
      }
    }
  }

  const handleBack = () => {
    if (currentStep > 1) {
      const prevStep = DISCOVERY_STEPS[currentStep - 2]
      if (prevStep && sessionId) {
        navigate(`/discovery/${sessionId}/${prevStep.path}`)
      }
    }
  }

  return (
    <div className="min-h-[calc(100vh-3.5rem)] flex flex-col">
      {/* Wizard header with step indicator */}
      <div className="border-b border-border bg-elevated/30">
        <div className="max-w-[1600px] mx-auto px-6">
          {/* Session name and back link */}
          <div className="py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Link
                to="/discovery"
                className="flex items-center gap-1.5 text-sm text-muted hover:text-default transition-colors"
              >
                <IconArrowLeft size={16} />
                <span>Sessions</span>
              </Link>
              {sessionName && (
                <>
                  <span className="text-faint">/</span>
                  <span className="text-sm font-medium text-default">{sessionName}</span>
                </>
              )}
            </div>

            {/* Chat toggle button */}
            <button
              onClick={() => setChatOpen(!chatOpen)}
              className={`btn-ghost btn-sm ${chatOpen ? 'text-accent' : 'text-muted'}`}
            >
              <IconChat size={18} />
              <span className="hidden sm:inline">
                {chatOpen ? 'Hide Assistant' : 'Assistant'}
              </span>
            </button>
          </div>

          {/* Step indicator */}
          <div className="py-4">
            <nav aria-label="Discovery progress">
              <ol className="flex items-center">
                {DISCOVERY_STEPS.map((step, index) => {
                  const isCompleted = step.id < currentStep
                  const isCurrent = step.id === currentStep
                  const isClickable = step.id <= currentStep

                  return (
                    <li key={step.id} className="flex items-center flex-1 last:flex-none">
                      {/* Step */}
                      <button
                        onClick={() => handleStepClick(step.id)}
                        disabled={!isClickable}
                        className={`
                          group flex items-center gap-3 px-3 py-2 rounded-lg transition-all
                          ${isClickable ? 'cursor-pointer' : 'cursor-not-allowed'}
                          ${isCurrent ? 'bg-accent/10' : 'hover:bg-bg-muted'}
                        `}
                      >
                        {/* Step icon/number */}
                        <div
                          className={`
                            w-9 h-9 rounded-lg flex items-center justify-center transition-all
                            ${isCompleted ? 'bg-success text-white' : ''}
                            ${isCurrent ? 'bg-accent text-white' : ''}
                            ${!isCompleted && !isCurrent ? 'bg-bg-muted text-subtle' : ''}
                          `}
                        >
                          {isCompleted ? (
                            <IconCheck size={18} />
                          ) : (
                            <step.icon size={18} />
                          )}
                        </div>

                        {/* Step text */}
                        <div className="hidden lg:block text-left">
                          <div
                            className={`
                              text-sm font-medium font-display
                              ${isCurrent ? 'text-accent' : ''}
                              ${isCompleted ? 'text-default' : ''}
                              ${!isCompleted && !isCurrent ? 'text-subtle' : ''}
                            `}
                          >
                            {step.title}
                          </div>
                          <div className="text-xs text-muted hidden xl:block">
                            {step.description}
                          </div>
                        </div>
                      </button>

                      {/* Connector line */}
                      {index < DISCOVERY_STEPS.length - 1 && (
                        <div
                          className={`
                            flex-1 h-px mx-2
                            ${isCompleted ? 'bg-success/50' : 'bg-border'}
                          `}
                        />
                      )}
                    </li>
                  )
                })}
              </ol>
            </nav>
          </div>
        </div>
      </div>

      {/* Main content area */}
      <div className="flex-1 flex">
        {/* Content */}
        <div className={`flex-1 transition-all duration-300 ${chatOpen ? 'mr-[380px]' : ''}`}>
          <div className="max-w-5xl mx-auto px-6 py-8">
            {children}
          </div>

          {/* Bottom navigation */}
          <div className="sticky bottom-0 border-t border-border bg-elevated/80 backdrop-blur-sm">
            <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
              <button
                onClick={handleBack}
                disabled={currentStep === 1}
                className="btn-secondary btn-md disabled:opacity-30"
              >
                <IconArrowLeft size={18} />
                <span>Back</span>
              </button>

              <div className="text-sm text-muted">
                Step {currentStep} of {DISCOVERY_STEPS.length}
              </div>

              <button
                onClick={handleNext}
                disabled={!canProceed || currentStep === 5}
                className="btn-primary btn-md disabled:opacity-30"
              >
                <span>{currentStep === 5 ? 'Complete' : 'Continue'}</span>
                <IconArrowRight size={18} />
              </button>
            </div>
          </div>
        </div>

        {/* Chat panel (slide in from right) */}
        <div
          className={`
            fixed top-14 right-0 bottom-0 w-[380px] border-l border-border bg-elevated
            transform transition-transform duration-300 ease-out
            ${chatOpen ? 'translate-x-0' : 'translate-x-full'}
          `}
        >
          <ChatPanel onClose={() => setChatOpen(false)} />
        </div>
      </div>
    </div>
  )
}

// Step content wrapper with title
interface StepContentProps {
  title: string
  description?: string
  actions?: ReactNode
  children: ReactNode
}

export function StepContent({ title, description, actions, children }: StepContentProps) {
  return (
    <div className="animate-fade-in">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-display font-semibold text-default">
            {title}
          </h2>
          {description && (
            <p className="mt-1 text-muted">{description}</p>
          )}
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>
      {children}
    </div>
  )
}
