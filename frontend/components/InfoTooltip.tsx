'use client';

import { InformationCircleIcon } from '@heroicons/react/24/outline';
import { useState } from 'react';

interface InfoTooltipProps {
  label: string;
  tooltip: string;
}

export default function InfoTooltip({ label, tooltip }: InfoTooltipProps) {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <span className="inline-flex items-center gap-1.5 relative group">
      <span className="font-medium">{label}</span>
      <button
        type="button"
        className="text-blue-500 hover:text-blue-600 focus:outline-none"
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        onFocus={() => setIsVisible(true)}
        onBlur={() => setIsVisible(false)}
        aria-label={`Information about ${label}`}
      >
        <InformationCircleIcon className="h-4 w-4" />
      </button>

      {isVisible && (
        <div className="absolute left-0 top-full mt-2 w-80 z-50 bg-gray-900 text-white text-sm rounded-lg shadow-lg p-3 pointer-events-none">
          <div className="absolute -top-1 left-4 w-2 h-2 bg-gray-900 transform rotate-45"></div>
          {tooltip}
        </div>
      )}
    </span>
  );
}
