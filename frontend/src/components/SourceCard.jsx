import React from "react";

export default function SourceCard({ title, snippet }) {
  return (
    <div className="source-card">
      <strong>{title}</strong>
      <p>{snippet}</p>
    </div>
  );
}
