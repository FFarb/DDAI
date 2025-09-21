import { FormEvent, useEffect } from 'react';
import { useSettingsStore } from '../store/settings';

const SettingsPage = () => {
  const { data, loadSettings, updateField, saveSettings, isSaving } = useSettingsStore();

  useEffect(() => {
    loadSettings();
  }, []);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    saveSettings();
  };

  return (
    <div className="flex-column">
      <h1>Settings</h1>
      <form onSubmit={handleSubmit} className="flex-column">
        {Object.entries(data).map(([key, value]) => (
          <label key={key}>
            {key}
            <input value={value} onChange={(e) => updateField(key, e.target.value)} />
          </label>
        ))}
        <button type="submit" disabled={isSaving}>
          {isSaving ? 'Saving...' : 'Save'}
        </button>
      </form>
    </div>
  );
};

export default SettingsPage;
