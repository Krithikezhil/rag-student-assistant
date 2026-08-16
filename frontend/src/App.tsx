import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import type { AskResponse } from './types';
import './App.css';

function App() {
  const [question, setQuestion] = useState<string>('');
  const [result, setResult] = useState<AskResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  const handleAsk = async () => {
    setError('');
    setResult(null);

    if (!question.trim()) {
      setError('Please enter a question.');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      });
      if (!response.ok) throw new Error('Request failed');
      const data: AskResponse = await response.json();
      setResult(data);
    } catch (err) {
      setError('Something went wrong. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <div className="app-container">
        <div className="header">
          <div className="badge">🧠</div>
          <h1>RAG Student Assistant</h1>
          <p>Ask a question about your study notes</p>
        </div>

        <div className="card">
          <div className="field-group">
            <label>Your Question</label>
            <textarea
              rows={4}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g. How does binary search work?"
            />
          </div>

          <button className="ask-btn" onClick={handleAsk} disabled={loading}>
            {loading ? 'Thinking...' : 'Ask'}
          </button>

          {error && <p className="error-text">{error}</p>}
        </div>

        {result && (
          <div className="results">
            <div className="answer-section">
              <div className="answer-label">Answer</div>
              <div className="answer-text">
                <ReactMarkdown>{result.answer}</ReactMarkdown>
              </div>
            </div>

            <div className="sources-section">
              <div className="sources-label">
                {result.sources.length > 0 ? 'Sourced From Your Notes' : 'General Knowledge'}
              </div>
              <div className="tag-row">
                {result.sources.map((source, i) => (
                  <span className="tag" key={i}>{source}</span>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;