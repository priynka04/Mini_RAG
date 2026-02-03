import React from "react";

export default function MessageBubble({ text, from }) {
  return (
    <div className={`message ${from}`}>
      <p>{text}</p>
    </div>
  );
}
