import { useState } from 'react'

export default function FlexibleSelect({
  value,
  onChange,
  options,
  placeholder = 'Select an option',
  required = false,
  disabled = false,
  id,
  name,
  className = '',
}) {
  const [manualEntry, setManualEntry] = useState(false)
  const choices = options.map(option => Array.isArray(option)
    ? { value: option[0], label: option[1] }
    : { value: option, label: option })
  const isCustomValue = value !== '' && !choices.some(option => String(option.value) === String(value))

  const handleChange = event => onChange({ target: { name, value: event.target.value } })
  const toggleMode = () => setManualEntry(current => !current)

  return (
    <div className={`flexible-select ${className}`.trim()}>
      {manualEntry ? (
        <input
          id={id}
          name={name}
          value={value}
          required={required}
          disabled={disabled}
          placeholder={placeholder === 'Select an option' ? 'Enter a value' : placeholder}
          onChange={handleChange}
          aria-label={name ? `${name} manual entry` : 'Manual entry'}
        />
      ) : (
        <select
          id={id}
          name={name}
          value={value}
          required={required}
          disabled={disabled}
          onChange={handleChange}
        >
          <option value="">{placeholder}</option>
          {isCustomValue && <option value={value}>{value} (custom)</option>}
          {choices.map(option => (
            <option value={option.value} key={option.value}>{option.label}</option>
          ))}
        </select>
      )}
      <button
        className="flexible-select-toggle"
        type="button"
        onClick={toggleMode}
        disabled={disabled}
        aria-label={manualEntry ? 'Choose from the list' : 'Enter a custom value'}
      >
        {manualEntry ? 'Choose from list' : 'Enter manually'}
      </button>
    </div>
  )
}
