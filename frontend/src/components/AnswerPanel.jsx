/**
 * Answer panel component - displays LLM answer with inline citations and sources
 */
import SourceCard from './SourceCard';

export default function AnswerPanel({ response }) {
  if (!response) return null;

  const { answer, sources, has_context, general_answer, timing, token_usage } = response;

  return (
    <div className="answer-panel">
      {/* Document-grounded answer */}
      {has_context ? (
        <div className="answer-section grounded">
          <div className="answer-header">
            <span className="answer-label">✓ Answer from Documents</span>
          </div>
          <div className="answer-text">{answer}</div>
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

      {/* Sources */}
      {sources && sources.length > 0 && (
        <div className="sources-section">
          <h3>📚 Sources</h3>
          <div className="sources-list">
            {sources.map((source) => (
              <SourceCard key={source.id} source={source} />
            ))}
          </div>
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