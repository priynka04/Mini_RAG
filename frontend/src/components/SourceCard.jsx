/**
 * Source card component - displays expandable source references
 */
import { useState, useEffect } from 'react';

export default function SourceCard({ source, isHighlighted, onExpand }) {
  const [expanded, setExpanded] = useState(false);

  // Auto-expand when highlighted
  useEffect(() => {
    if (isHighlighted) {
      setExpanded(true);
      // Scroll to this card
      setTimeout(() => {
        const element = document.getElementById(`source-${source.id}`);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
      }, 100);
    }
  }, [isHighlighted, source.id]);

  const handleClick = () => {
    setExpanded(!expanded);
    if (onExpand) onExpand();
  };

  return (
    <div
      id={`source-${source.id}`}
      className={`source-card ${isHighlighted ? 'highlighted' : ''}`}
    >
      <div 
        className="source-header"
        onClick={handleClick}
      >
        <span className="source-id">[{source.id}]</span>
        <span className="source-document">{source.document}</span>
        <span className="source-score">Score: {source.score.toFixed(3)}</span>
        <span className="expand-icon">{expanded ? '▼' : '▶'}</span>
      </div>

      {expanded && (
        <div className="source-body">
          <div className="source-text">
            {source.text}
          </div>

          {source.links && source.links.length > 0 && (
            <div className="source-links">
              <strong>🔗 Links:</strong>
              <ul>
                {source.links.map((link, idx) => (
                  <li key={idx}>
                    <a href={link} target="_blank" rel="noopener noreferrer">
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {source.images && source.images.length > 0 && (
            <div className="source-images">
              <strong>🖼️ Images:</strong>
              <ul>
                {source.images.map((img, idx) => (
                  <li key={idx}>{img}</li>
                ))}
              </ul>
            </div>
          )}

          {source.section && (
            <div className="source-section">
              <strong>Section:</strong> {source.section}
            </div>
          )}
        </div>
      )}
    </div>
  );
}