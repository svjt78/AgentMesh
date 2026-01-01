'use client';

import { useState, useEffect } from 'react';

interface JsonSchemaEditorProps {
  value: Record<string, any>;
  onChange: (value: Record<string, any>) => void;
  label?: string;
  placeholder?: string;
}

export default function JsonSchemaEditor({
  value,
  onChange,
  label = 'JSON Schema',
  placeholder = 'Enter JSON schema...',
}: JsonSchemaEditorProps) {
  const [jsonText, setJsonText] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Initialize with formatted JSON
  useEffect(() => {
    try {
      setJsonText(JSON.stringify(value, null, 2));
      setError(null);
    } catch (e) {
      setError('Invalid JSON');
    }
  }, [value]);

  const handleChange = (text: string) => {
    setJsonText(text);

    try {
      const parsed = JSON.parse(text);
      setError(null);
      onChange(parsed);
    } catch (e) {
      if (text.trim()) {
        setError('Invalid JSON syntax');
      } else {
        setError(null);
      }
    }
  };

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        {label}
      </label>
      <textarea
        value={jsonText}
        onChange={(e) => handleChange(e.target.value)}
        placeholder={placeholder}
        className={`w-full h-64 p-3 border rounded-md font-mono text-sm text-gray-900 placeholder-gray-400 ${
          error ? 'border-red-500 focus:ring-red-500' : 'border-gray-300 focus:ring-blue-500'
        } focus:ring-2 focus:border-transparent`}
      />
      {error && (
        <p className="mt-2 text-sm text-red-600">{error}</p>
      )}
      <p className="mt-2 text-xs text-gray-500">
        Format: JSON Schema Draft 7
      </p>
    </div>
  );
}
