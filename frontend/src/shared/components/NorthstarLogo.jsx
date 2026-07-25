import React from 'react'
import { motion } from 'framer-motion'

/**
 * Northstar Logo Component — Clean Minimalist 2D Flat Vector Brand Mark
 * Concept: Minimalist 2D Northstar Compass + Upward Financial Vector Arc + AI Pulse Point
 */
export default function NorthstarLogo({ size = 32, showText = true, className = '', animated = true }) {
  const iconMarkup = (
    <div
      className={`relative flex items-center justify-center flex-shrink-0 cursor-pointer ${className}`}
      style={{ width: size, height: size }}
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 40 40"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full"
      >
        {/* Minimalist 2D Northstar Star Mark (Flat Geometry) */}
        {/* Top Blade */}
        <path d="M20 3 L23.5 17 L20 20 L16.5 17 Z" fill="#2dd4bf" />
        
        {/* Bottom Blade */}
        <path d="M20 37 L23.5 23 L20 20 L16.5 23 Z" fill="#2dd4bf" fillOpacity="0.7" />
        
        {/* Right Blade */}
        <path d="M37 20 L23 23.5 L20 20 L23 16.5 Z" fill="#2dd4bf" />
        
        {/* Left Blade */}
        <path d="M3 20 L17 23.5 L20 20 L17 16.5 Z" fill="#2dd4bf" fillOpacity="0.7" />

        {/* Diagonal Small Star Points */}
        <path d="M29 11 L22.5 17.5 L20 20 L22.5 17.5 Z" fill="#34d399" />
        <path d="M11 29 L17.5 22.5 L20 20 L17.5 22.5 Z" fill="#34d399" />

        {/* Smooth 2D Upward Financial Growth Arc */}
        <path
          d="M8 32 C 14 32, 18 24, 23 21 C 28 18, 32 10, 36 6"
          stroke="#34d399"
          strokeWidth="2.5"
          strokeLinecap="round"
          fill="none"
        />

        {/* AI Pulse Dot */}
        <circle cx="36" cy="6" r="2.5" fill="#2dd4bf" />
        <circle cx="20" cy="20" r="2" fill="#ffffff" />
      </svg>
    </div>
  )

  if (!showText) {
    return animated ? (
      <motion.div whileHover={{ scale: 1.04 }} transition={{ duration: 0.15 }}>
        {iconMarkup}
      </motion.div>
    ) : (
      iconMarkup
    )
  }

  return (
    <motion.div
      className={`inline-flex items-center gap-2.5 select-none bg-transparent ${className}`}
      whileHover={animated ? { scale: 1.04 } : undefined}
      transition={{ duration: 0.18, ease: 'easeOut' }}
    >
      {iconMarkup}
      <div className="flex flex-col text-left leading-none">
        <span className="text-sm font-bold tracking-tight text-white flex items-center gap-1 font-sans">
          Northstar <span className="text-teal-400 font-semibold">Finance</span>
        </span>
        <span className="text-[8.5px] font-semibold uppercase tracking-[0.18em] text-zinc-400 mt-0.5">
          Intelligence Lab
        </span>
      </div>
    </motion.div>
  )
}
