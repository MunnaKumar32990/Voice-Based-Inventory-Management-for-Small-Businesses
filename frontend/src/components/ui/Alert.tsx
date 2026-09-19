import React from 'react';
import { AlertCircle, CheckCircle, Info, AlertTriangle } from 'lucide-react';

interface AlertProps {
  variant?: 'info' | 'success' | 'warning' | 'error';
  title?: string;
  children: React.ReactNode;
}

export const Alert: React.FC<AlertProps> = ({ variant = 'info', title, children }) => {
  const variants = {
    info: {
      bg: 'bg-blue-50',
      text: 'text-blue-800',
      icon: <Info className="h-5 w-5 text-blue-400" />,
    },
    success: {
      bg: 'bg-green-50',
      text: 'text-green-800',
      icon: <CheckCircle className="h-5 w-5 text-green-400" />,
    },
    warning: {
      bg: 'bg-yellow-50',
      text: 'text-yellow-800',
      icon: <AlertTriangle className="h-5 w-5 text-yellow-400" />,
    },
    error: {
      bg: 'bg-red-50',
      text: 'text-red-800',
      icon: <AlertCircle className="h-5 w-5 text-red-400" />,
    },
  };

  const style = variants[variant];

  return (
    <div className={`rounded-md p-4 ${style.bg}`}>
      <div className="flex">
        <div className="flex-shrink-0">{style.icon}</div>
        <div className="ml-3">
          {title && <h3 className={`text-sm font-medium ${style.text}`}>{title}</h3>}
          <div className={`text-sm ${style.text} ${title ? 'mt-2' : ''}`}>
            {children}
          </div>
        </div>
      </div>
    </div>
  );
};
