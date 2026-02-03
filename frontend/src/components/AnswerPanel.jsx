/**
 * Answer panel component - displays LLM answer with inline citations and sources
 */
import { useState } from 'react';
import SourceCard from './SourceCard';

export default function AnswerPanel({ response }) {
  const [selectedSourceId, setSelectedSourceId] = useState(null);
  const [showAllSources, setShowAllSources] = useState(false);

  if (!response) return null;

  const { answer, sources, has_context, general_answer, timing, token_usage } = response;

  // Convert citations in answer to clickable links
  const renderAnswerWithClickableCitations = (text) => {
    // Match citations like [1], [2], [3]
    const parts = text.split(/(\[\d+\])/g);
    
    return parts.map((part, index) => {
      const match = part.match(/\[(\d+)\]/);
      if (match) {
        const citationId = parseInt(match[1]);
        return (
          <span
            key={index}
            className="citation-link"
            onClick={() => {
              setSelectedSourceId(citationId);
              setShowAllSources(true);
            }}
            title={`Click to see source ${citationId}`}
          >
            {part}
          </span>
        );
      }
      return <span key={index}>{part}</span>;
    });
  };

  return (
    <div className="answer-panel">
      {/* Document-grounded answer */}
      {has_context ? (
        <div className="answer-section grounded">
          <div className="answer-header">
            <span className="answer-label">✓ Answer from Documents</span>
          </div>
          <div className="answer-text">
            {renderAnswerWithClickableCitations(answer)}
          </div>
          <div className="citation-hint">
            💡 Click on citations like [1] to see the source
          </div>
        </div>
      ) : (
        <div className="answer-section no-context">
          <div className="answer-header">
            <span className="answer-label">⚠️ No Relevant Documents Found</span>
          </div>
          <div className="answer-text">{answer}</div>
        </div>
      )}

      {/* General knowledge answer (if applicable) */}
      {general_answer && (
        <div className="answer-section general">
          <div className="answer-header">
            <span className="answer-label">💡 General Knowledge (Not from Documents)</span>
          </div>
          <div className="answer-text">{general_answer}</div>
        </div>
      )}

      {/* Sources - Show/Hide Toggle */}
      {sources && sources.length > 0 && (
        <div className="sources-section">
          <div className="sources-header">
            <h3>📚 Sources ({sources.length})</h3>
            <button
              className="btn-toggle-sources"
              onClick={() => setShowAllSources(!showAllSources)}
            >
              {showAllSources ? '▼ Hide Sources' : '▶ Show All Sources'}
            </button>
          </div>
          
          {showAllSources && (
            <div className="sources-list">
              {sources.map((source) => (
                <SourceCard
                  key={source.id}
                  source={source}
                  isHighlighted={selectedSourceId === source.id}
                  onExpand={() => setSelectedSourceId(source.id)}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Metadata */}
      <div className="metadata">
        <div className="timing-info">
          <span>⏱️ Timing:</span>
          <span>Retrieval: {timing.retrieval_ms.toFixed(0)}ms</span>
          <span>Rerank: {timing.rerank_ms.toFixed(0)}ms</span>
          <span>LLM: {timing.llm_ms.toFixed(0)}ms</span>
          <span className="total">Total: {timing.total_ms.toFixed(0)}ms</span>
        </div>

        {token_usage && (
          <div className="token-info">
            <span>🎫 Tokens:</span>
            <span>{token_usage.total_tokens} total</span>
            <span>({token_usage.prompt_tokens} prompt + {token_usage.completion_tokens} completion)</span>
            <span className="cost">~${token_usage.estimated_cost_usd.toFixed(6)}</span>
          </div>
        )}
      </div>
    </div>
  );
}