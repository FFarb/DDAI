import MonacoEditor from '@monaco-editor/react';

interface EditorProps {
  value: string;
  language: string;
  onChange: (value: string) => void;
}

const Editor = ({ value, language, onChange }: EditorProps) => {
  return (
    <div style={{ border: '1px solid #2a2a2a', borderRadius: '6px', overflow: 'hidden' }}>
      <MonacoEditor
        height="400px"
        language={language === 'js' ? 'javascript' : 'python'}
        theme="vs-dark"
        value={value}
        onChange={(val) => onChange(val ?? '')}
        options={{ minimap: { enabled: false }, fontSize: 14 }}
      />
    </div>
  );
};

export default Editor;
