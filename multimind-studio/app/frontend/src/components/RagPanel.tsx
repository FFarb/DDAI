import { FormEvent, useState } from 'react';

interface RagResult {
  contexts: string[];
  answer: string;
}

const RagPanel = () => {
  const [collectionId, setCollectionId] = useState('default');
  const [query, setQuery] = useState('');
  const [result, setResult] = useState<RagResult | null>(null);
  const [status, setStatus] = useState('');

  const handleUpload = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const fileInput = form.elements.namedItem('file') as HTMLInputElement;
    if (!fileInput.files?.length) return;
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('collection_id', collectionId);
    const response = await fetch('/api/rag/upload', {
      method: 'POST',
      body: formData,
    });
    const data = await response.json();
    setStatus(`Uploaded: ${data.path}`);
    fileInput.value = '';
  };

  const handleIndex = async () => {
    setStatus('Indexing...');
    const response = await fetch('/api/rag/index', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ collection_id: collectionId }),
    });
    const data = await response.json();
    setStatus(`Indexed ${data.indexed} documents.`);
  };

  const handleQuery = async () => {
    const response = await fetch('/api/rag/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, collection_id: collectionId, top_k: 3 }),
    });
    const data = await response.json();
    setResult(data);
  };

  return (
    <div className="card">
      <h3>Retrieval Augmented Generation</h3>
      <div className="flex" style={{ alignItems: 'flex-end' }}>
        <label style={{ flex: 1 }}>
          Collection
          <input value={collectionId} onChange={(e) => setCollectionId(e.target.value)} />
        </label>
        <button onClick={handleIndex}>Rebuild Index</button>
      </div>
      <form onSubmit={handleUpload} style={{ marginTop: '16px' }}>
        <input type="file" name="file" />
        <button type="submit" style={{ marginLeft: '12px' }}>
          Upload
        </button>
      </form>
      {status && <p>{status}</p>}
      <div className="flex-column" style={{ marginTop: '16px' }}>
        <textarea
          rows={4}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask about your documents"
        />
        <button onClick={handleQuery}>Query</button>
      </div>
      {result && (
        <div style={{ marginTop: '16px' }}>
          <h4>Answer</h4>
          <p>{result.answer}</p>
          <h4>Contexts</h4>
          <ul>
            {result.contexts.map((context, index) => (
              <li key={index}>
                <pre style={{ whiteSpace: 'pre-wrap' }}>{context}</pre>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default RagPanel;
