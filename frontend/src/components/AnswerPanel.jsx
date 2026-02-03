import React from "react";

export default function AnswerPanel({ answer, sources = [] }) {
  return (
    <div>
      <div>{answer}</div>
      <ul>
        {sources.map((s, i) => (
          <li key={i}>{s}</li>
        ))}
      </ul>
    </div>
  );
}
