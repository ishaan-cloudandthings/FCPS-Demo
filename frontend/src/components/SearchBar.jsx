/**
 * SearchBar — controlled search input.
 *
 * Stays presentational — debounce / filter logic lives in the caller.
 */
export function SearchBar({ value, onChange, label = "Search vendors", placeholder = "Search…" }) {
  return (
    <label className="block">
      <span className="visually-hidden">{label}</span>
      <input
        type="search"
        role="searchbox"
        aria-label={label}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full max-w-md rounded-md border border-gray-300 bg-white px-3 py-2 text-sm shadow-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-blue-500"
      />
    </label>
  );
}
