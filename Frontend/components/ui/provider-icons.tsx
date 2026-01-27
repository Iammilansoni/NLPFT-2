"use client"

/**
 * Provider Icons - SVG brand logos for LLM providers
 * 
 * Icons from Icons8 and official brand assets
 */

import { useId } from "react"
import { cn } from "@/lib/utils"

interface ProviderIconProps {
  provider: 'openai' | 'google' | 'grok' | 'claude' | 'ollama' | 'deepseek' | 'huggingface' | 'custom'
  className?: string
  size?: number
}

// OpenAI ChatGPT Icon
const OpenAIIcon = ({ className, size = 24 }: { className?: string; size?: number }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <path
      d="M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729zm-9.022 12.6081a4.4755 4.4755 0 0 1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1686a.071.071 0 0 1 .038.052v5.5826a4.504 4.504 0 0 1-4.4945 4.4944zm-9.6607-4.1254a4.4708 4.4708 0 0 1-.5346-3.0137l.142.0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 19.9502a4.4992 4.4992 0 0 1-6.1408-1.6464zM2.3408 7.8956a4.485 4.485 0 0 1 2.3655-1.9728V11.6a.7664.7664 0 0 0 .3879.6765l5.8144 3.3543-2.0201 1.1685a.0757.0757 0 0 1-.071 0l-4.8303-2.7865A4.504 4.504 0 0 1 2.3408 7.872zm16.5963 3.8558L13.1038 8.364l2.0201-1.1638a.0757.0757 0 0 1 .071 0l4.8303 2.7913a4.4944 4.4944 0 0 1-.6765 8.1042v-5.6772a.79.79 0 0 0-.4091-.6813zm2.0107-3.0231l-.142-.0852-4.7735-2.7818a.7759.7759 0 0 0-.7854 0L9.409 9.2297V6.8974a.0662.0662 0 0 1 .0284-.0615l4.8303-2.7866a4.4992 4.4992 0 0 1 6.6802 4.66zM8.3065 12.863l-2.02-1.1638a.0804.0804 0 0 1-.038-.0567V6.0742a4.4992 4.4992 0 0 1 7.3757-3.4537l-.142.0805L8.704 5.459a.7948.7948 0 0 0-.3927.6813zm1.0976-2.3654l2.602-1.4998 2.6069 1.4998v2.9994l-2.5974 1.4997-2.6099-1.4997z"
      fill="currentColor"
    />
  </svg>
)

// Google Gemini Icon
const GoogleIcon = ({ className, size = 24 }: { className?: string; size?: number }) => {
  const gradientId = useId()
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <defs>
        <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#4285F4" />
          <stop offset="50%" stopColor="#9B72CB" />
          <stop offset="100%" stopColor="#D96570" />
        </linearGradient>
      </defs>
      <path
        d="M12 24C18.6274 24 24 18.6274 24 12C24 5.37258 18.6274 0 12 0C5.37258 0 0 5.37258 0 12C0 18.6274 5.37258 24 12 24Z"
        fill={`url(#${gradientId})`}
      />
      <path
        d="M12 4.5L12 19.5M4.5 12L19.5 12"
        stroke="white"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <circle cx="12" cy="12" r="3" fill="white" />
    </svg>
  )
}

// Grok (xAI) Icon - Based on the provided SVG
const GrokIcon = ({ className, size = 24 }: { className?: string; size?: number }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <path
      d="M4.5 2C3.5 2.5 2.8 4 2.5 6C2.3 7.5 2.5 9.5 3 11C3.3 11.8 3.3 12.2 3 12.8C2 14.3 1.5 16.5 1.5 18.5C1.5 20 1.8 21 2.5 22H5C4.5 21 4.5 19 5 17C5.5 15 6 14 7 13V12C6.5 11.5 6 10.5 5.5 9.5C4.5 7 4.5 4.5 6 3C6.5 2.5 6.5 2.5 5.5 2.5C5 2.5 4.7 2.1 4.5 2ZM19.5 2C19.3 2.1 19 2.5 18.5 2.5C17.5 2.5 17.5 2.5 18 3C19.5 4.5 19.5 7 18.5 9.5C18 10.5 17.5 11.5 17 12V13C18 14 18.5 15 19 17C19.5 19 19.5 21 19 22H22C22.2 21 22.5 20 22.5 18.5C22.5 16.5 22 14.3 21 12.8C20.7 12.2 20.7 11.8 21 11C21.5 9.5 21.7 7.5 21.5 6C21.2 4 20.5 2.5 19.5 2Z"
      fill="currentColor"
    />
    <path
      d="M12 7C10 7 8.5 8 7.5 9.5C6.5 11 6.5 13 7.5 14.5C8.5 16 10 17 12 17C14 17 15.5 16 16.5 14.5C17.5 13 17.5 11 16.5 9.5C15.5 8 14 7 12 7ZM12 9C13.5 9 14.5 10 15 11C15.5 12 15 13 14 14C13 15 11 15 10 14C9 13 8.5 12 9 11C9.5 10 10.5 9 12 9Z"
      fill="currentColor"
    />
    <circle cx="11" cy="11.5" r="1" fill="currentColor" />
  </svg>
)

// Claude (Anthropic) Icon
const ClaudeIcon = ({ className, size = 24 }: { className?: string; size?: number }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <path
      d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM12 20C7.59 20 4 16.41 4 12C4 7.59 7.59 4 12 4C16.41 4 20 7.59 20 12C20 16.41 16.41 20 12 20Z"
      fill="#D97706"
    />
    <path
      d="M12 6C9.24 6 7 8.24 7 11C7 12.62 7.81 14.05 9.06 14.94L8.29 17.86C8.18 18.25 8.56 18.6 8.94 18.46L12 17.23L15.06 18.46C15.44 18.6 15.82 18.25 15.71 17.86L14.94 14.94C16.19 14.05 17 12.62 17 11C17 8.24 14.76 6 12 6ZM10 10C10.55 10 11 10.45 11 11C11 11.55 10.55 12 10 12C9.45 12 9 11.55 9 11C9 10.45 9.45 10 10 10ZM14 10C14.55 10 15 10.45 15 11C15 11.55 14.55 12 14 12C13.45 12 13 11.55 13 11C13 10.45 13.45 10 14 10Z"
      fill="#D97706"
    />
  </svg>
)

// Ollama Icon (Llama)
const OllamaIcon = ({ className, size = 24 }: { className?: string; size?: number }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <path
      d="M12 2C8.5 2 6 4 5 7C4 10 4 13 5 15C5.5 16 6 17 7 17.5V21C7 21.5 7.5 22 8 22H16C16.5 22 17 21.5 17 21V17.5C18 17 18.5 16 19 15C20 13 20 10 19 7C18 4 15.5 2 12 2Z"
      stroke="currentColor"
      strokeWidth="1.5"
      fill="none"
    />
    <circle cx="9" cy="9" r="1.5" fill="currentColor" />
    <circle cx="15" cy="9" r="1.5" fill="currentColor" />
    <path
      d="M9 14C9 14 10.5 15.5 12 15.5C13.5 15.5 15 14 15 14"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
    />
    <path
      d="M3 8C3 8 4 7 5 7M21 8C21 8 20 7 19 7"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
    />
  </svg>
)

// DeepSeek Icon
const DeepSeekIcon = ({ className, size = 24 }: { className?: string; size?: number }) => {
  const gradientId = useId()
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <defs>
        <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#0066ff" />
          <stop offset="100%" stopColor="#00ccff" />
        </linearGradient>
      </defs>
      <circle cx="12" cy="12" r="10" fill={`url(#${gradientId})`} />
      <path
        d="M8 12C8 9.79 9.79 8 12 8M16 12C16 14.21 14.21 16 12 16"
        stroke="white"
        strokeWidth="2"
        strokeLinecap="round"
      />
      <circle cx="12" cy="12" r="2" fill="white" />
    </svg>
  )
}

// HuggingFace Icon
const HuggingFaceIcon = ({ className, size = 24 }: { className?: string; size?: number }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <circle cx="12" cy="12" r="10" fill="#FFD21E" />
    <circle cx="8.5" cy="10" r="1.5" fill="#1A1A1A" />
    <circle cx="15.5" cy="10" r="1.5" fill="#1A1A1A" />
    <path
      d="M7 14C7 14 9 17 12 17C15 17 17 14 17 14"
      stroke="#1A1A1A"
      strokeWidth="1.5"
      strokeLinecap="round"
    />
    <path
      d="M6.5 7C6.5 7 7 5.5 8.5 5.5M17.5 7C17.5 7 17 5.5 15.5 5.5"
      stroke="#1A1A1A"
      strokeWidth="1.5"
      strokeLinecap="round"
    />
  </svg>
)

// Custom/Generic Icon
const CustomIcon = ({ className, size = 24 }: { className?: string; size?: number }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <rect x="3" y="3" width="18" height="18" rx="3" stroke="currentColor" strokeWidth="2" />
    <circle cx="12" cy="12" r="4" stroke="currentColor" strokeWidth="2" />
    <path d="M12 3V8M12 16V21M3 12H8M16 12H21" stroke="currentColor" strokeWidth="2" />
  </svg>
)

export const ProviderIcon = ({ provider, className, size = 24 }: ProviderIconProps) => {
  const icons = {
    openai: OpenAIIcon,
    google: GoogleIcon,
    grok: GrokIcon,
    claude: ClaudeIcon,
    ollama: OllamaIcon,
    deepseek: DeepSeekIcon,
    huggingface: HuggingFaceIcon,
    custom: CustomIcon,
  }

  const IconComponent = icons[provider] || CustomIcon

  return <IconComponent className={cn(className)} size={size} />
}

export default ProviderIcon
