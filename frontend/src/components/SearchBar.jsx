import React, { useState } from 'react';
import { Search, Loader, MapPin } from 'lucide-react';

const SearchBar = ({ onSearch }) => {
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    setError('');

    try {
      // Use Nominatim OSM API for geocoding
      const response = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=1`);
      const data = await response.json();

      if (!data || data.length === 0) {
        throw new Error("Target region not found. Verify coordinates/name.");
      }

      const result = data[0];
      const lat = parseFloat(result.lat);
      const lon = parseFloat(result.lon);
      
      // Nominatim boundingbox: [lat_min, lat_max, lon_min, lon_max]
      // We need: [lat_min, lon_min, lat_max, lon_max]
      const bb = result.boundingbox;
      const bbox = [
        parseFloat(bb[0]), // lat_min
        parseFloat(bb[2]), // lon_min
        parseFloat(bb[1]), // lat_max
        parseFloat(bb[3])  // lon_max
      ];

      onSearch({
        id: result.place_id.toString(),
        name: result.display_name.split(',')[0], // Take primary name
        fullName: result.display_name,
        lat,
        lon,
        bbox
      });
      setQuery('');
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div style={{
      position: 'absolute',
      top: 20,
      left: 20,
      zIndex: 1000,
      width: 320,
      display: 'flex',
      flexDirection: 'column',
      gap: 8
    }}>
      <form 
        onSubmit={handleSearch}
        style={{
          display: 'flex',
          backgroundColor: 'var(--bg-surface)',
          border: '2px solid var(--color-critical)',
          boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
          borderRadius: 2
        }}
      >
        <div style={{
          padding: '8px 12px',
          display: 'flex',
          alignItems: 'center',
          backgroundColor: 'var(--bg-sidebar)',
          color: 'var(--text-inverse)'
        }}>
          <MapPin size={16} />
        </div>
        <input 
          type="text" 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="ENTER TARGET COORDINATES OR REGION..."
          style={{
            flex: 1,
            padding: '10px 12px',
            border: 'none',
            outline: 'none',
            backgroundColor: 'var(--bg-surface)',
            color: 'var(--text-primary)',
            fontFamily: 'var(--font-mono)',
            fontSize: 12,
            fontWeight: 600,
            letterSpacing: 0.5
          }}
        />
        <button 
          type="submit" 
          disabled={isSearching}
          style={{
            padding: '0 16px',
            backgroundColor: 'var(--color-critical)',
            color: 'white',
            border: 'none',
            cursor: isSearching ? 'wait' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          {isSearching ? <Loader size={16} className="spin" /> : <Search size={16} />}
        </button>
      </form>
      {error && (
        <div style={{
          padding: '6px 12px',
          backgroundColor: 'var(--bg-critical)',
          color: 'var(--color-critical)',
          border: '1px solid var(--border-critical)',
          fontSize: 11,
          fontFamily: 'var(--font-mono)',
          fontWeight: 600
        }}>
          [ERROR] {error}
        </div>
      )}
    </div>
  );
};

export default SearchBar;
