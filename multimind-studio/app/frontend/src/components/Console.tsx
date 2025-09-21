interface ConsoleProps {
  logs: string[];
}

const Console = ({ logs }: ConsoleProps) => {
  return (
    <div className="console">
      {logs.length ? logs.map((log, index) => <div key={index}>{log}</div>) : <p>No logs yet.</p>}
    </div>
  );
};

export default Console;
