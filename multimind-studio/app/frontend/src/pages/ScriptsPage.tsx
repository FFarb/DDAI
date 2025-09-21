import { useEffect } from 'react';
import Console from '../components/Console';
import Editor from '../components/Editor';
import { useScriptsStore } from '../store/scripts';

const ScriptsPage = () => {
  const {
    scripts,
    fetchScripts,
    selectScript,
    selectedScript,
    currentContent,
    updateContent,
    saveScript,
    runScript,
    stopRun,
    isRunning,
    runLogs,
    artifacts,
    fetchArtifacts,
  } = useScriptsStore();

  useEffect(() => {
    fetchScripts();
  }, []);

  return (
    <div className="flex" style={{ alignItems: 'flex-start' }}>
      <div className="file-tree">
        <h3>Scripts</h3>
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {scripts.map((script) => (
            <li key={script.id}>
              <button
                style={{ width: '100%', textAlign: 'left', marginBottom: '8px' }}
                onClick={() => selectScript(script.id)}
              >
                {script.name}
              </button>
            </li>
          ))}
        </ul>
      </div>
      <div style={{ flex: 1 }}>
        <h1>Script Runner</h1>
        {selectedScript ? (
          <div className="flex-column">
            <div className="flex" style={{ justifyContent: 'space-between', alignItems: 'center' }}>
              <h2>{selectedScript.name}</h2>
              <span>Language: {selectedScript.language}</span>
            </div>
            <Editor
              value={currentContent}
              language={selectedScript.language}
              onChange={updateContent}
            />
            <div className="flex" style={{ justifyContent: 'flex-end' }}>
              <button onClick={saveScript}>Save</button>
              <button onClick={runScript} disabled={isRunning}>
                {isRunning ? 'Running...' : 'Run'}
              </button>
              <button onClick={stopRun} disabled={!isRunning}>
                Stop
              </button>
              <button onClick={fetchArtifacts}>Artifacts</button>
            </div>
            <div>
              <h3>Console</h3>
              <Console logs={runLogs} />
            </div>
            {artifacts.length > 0 && (
              <div>
                <h3>Artifacts</h3>
                <ul>
                  {artifacts.map((artifact) => (
                    <li key={artifact}>{artifact}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : (
          <p>Select a script to start editing.</p>
        )}
      </div>
    </div>
  );
};

export default ScriptsPage;
