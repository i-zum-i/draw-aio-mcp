'use client';

import { useState } from 'react';
import ErrorMessage from './ErrorMessage';

interface InputFormProps {
  onSubmit: (text: string) => void;
  onClear: () => void;
  isLoading: boolean;
  hasResult: boolean;
}

export default function InputForm({ onSubmit, onClear, isLoading, hasResult }: InputFormProps) {
  const [inputText, setInputText] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Input validation
    setValidationError(null);
    
    if (!inputText.trim()) {
      setValidationError('Please enter a description for the diagram.');
      return;
    }
    
    if (inputText.length > 10000) {
      setValidationError('Input text is too long. Please keep it within 10,000 characters.');
      return;
    }
    
    onSubmit(inputText.trim());
  };

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputText(e.target.value);
    // Clear validation error while typing
    if (validationError) {
      setValidationError(null);
    }
  };

  const handleClear = () => {
    setInputText('');
    setValidationError(null);
    onClear();
  };

  return (
    <div className="input-section">
      {validationError && (
        <ErrorMessage 
          error={validationError}
          type="warning"
          onDismiss={() => setValidationError(null)}
          showDismiss={true}
        />
      )}
      <form onSubmit={handleSubmit} className="input-form">
        <label htmlFor="diagram-input" className="input-label">
          Enter diagram description
        </label>
        <textarea
          id="diagram-input"
          className="diagram-input"
          placeholder="Example: Create a flowchart from user registration to login. Include user information input, validation, and database storage flow."
          rows={6}
          value={inputText}
          onChange={handleTextChange}
          disabled={isLoading}
        />
        <div className="input-info">
          <span className="char-count">
            {inputText.length}/10,000 characters
          </span>
        </div>
        <div className="button-container">
          <button 
            className={`generate-button ${isLoading ? 'loading' : ''}`}
            type="submit"
            disabled={isLoading || !inputText.trim()}
          >
            {isLoading ? (
              <>
                <span className="spinner"></span>
                Generating...
              </>
            ) : (
              'Create Diagram'
            )}
          </button>
          <button
            className="clear-button"
            type="button"
            onClick={handleClear}
            disabled={isLoading || !hasResult}
          >
            Clear
          </button>
        </div>
      </form>
      
      <style jsx>{`
        .input-section {
          background: white;
          border-radius: 8px;
          padding: 2rem;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
          margin-bottom: 2rem;
        }
        
        .input-form {
          max-width: 800px;
          margin: 0 auto;
        }
        
        .input-label {
          display: block;
          font-size: 1.1rem;
          font-weight: 500;
          color: #333;
          margin-bottom: 0.5rem;
        }
        
        .diagram-input {
          width: 100%;
          padding: 1rem;
          border: 2px solid #e0e0e0;
          border-radius: 6px;
          font-size: 1rem;
          font-family: inherit;
          line-height: 1.5;
          resize: vertical;
          min-height: 120px;
          transition: border-color 0.2s ease;
          box-sizing: border-box;
        }
        
        .diagram-input:focus {
          outline: none;
          border-color: #007bff;
          box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
        }
        
        .diagram-input:disabled {
          background-color: #f8f9fa;
          cursor: not-allowed;
          opacity: 0.7;
        }
        
        .diagram-input::placeholder {
          color: #999;
        }
        
        .input-info {
          display: flex;
          justify-content: flex-end;
          margin-top: 0.5rem;
          margin-bottom: 1rem;
        }
        
        .char-count {
          font-size: 0.875rem;
          color: #666;
        }
        
        .button-container {
          display: flex;
          gap: 1rem;
          justify-content: center;
          align-items: center;
          margin: 0.5rem auto 0;
        }
        
        .generate-button {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
          flex: 1;
          max-width: 200px;
          padding: 0.75rem 1.5rem;
          background: #007bff;
          color: white;
          border: none;
          border-radius: 6px;
          font-size: 1rem;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
          min-height: 44px;
        }
        
        .generate-button:hover:not(:disabled) {
          background: #0056b3;
        }
        
        .generate-button:active:not(:disabled) {
          transform: translateY(1px);
        }
        
        .generate-button:disabled {
          background: #6c757d;
          cursor: not-allowed;
          transform: none;
        }
        
        .generate-button.loading {
          background: #6c757d;
        }
        
        .spinner {
          width: 16px;
          height: 16px;
          border: 2px solid transparent;
          border-top: 2px solid white;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        
        .clear-button {
          display: flex;
          align-items: center;
          justify-content: center;
          flex: 1;
          max-width: 200px;
          padding: 0.75rem 1.5rem;
          background: #6c757d;
          color: white;
          border: none;
          border-radius: 6px;
          font-size: 1rem;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
          min-height: 44px;
        }
        
        .clear-button:hover:not(:disabled) {
          background: #5a6268;
        }
        
        .clear-button:active:not(:disabled) {
          transform: translateY(1px);
        }
        
        .clear-button:disabled {
          background: #adb5bd;
          cursor: not-allowed;
          opacity: 0.6;
          transform: none;
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
          .input-section {
            padding: 1.5rem;
            margin-bottom: 1.5rem;
          }
          
          .diagram-input {
            font-size: 16px; /* Prevents zoom on iOS */
          }
          
          .button-container {
            flex-direction: column;
            gap: 0.75rem;
          }
          
          .generate-button,
          .clear-button {
            max-width: none;
            width: 100%;
          }
        }
        
        @media (max-width: 480px) {
          .input-section {
            padding: 1rem;
            border-radius: 6px;
          }
          
          .input-label {
            font-size: 1rem;
          }
        }
      `}</style>
    </div>
  );
}