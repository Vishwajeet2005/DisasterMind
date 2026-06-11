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
          backgroundColor: 'rgba(10, 15, 30, 0.8)',
          backdropFilter: 'blur(10px)',
          border: '1px solid var(--color-critical)',
          boxShadow: '0 0 15px rgba(255, 0, 60, 0.3)',
          borderRadius: 'var(--radius-md)',
          overflow: 'hidden'
        }}
      >
        <div style={{
          padding: '12px 16px',
          display: 'flex',
          alignItems: 'center',
          backgroundColor: 'rgba(255, 0, 60, 0.1)',
          color: 'var(--color-critical)'
        }}>
          <MapPin size={18} />
        </div>
        <input 
          type="text" 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="ENTER TARGET COORDINATES OR REGION..."
          style={{
            flex: 1,
            padding: '12px 16px',
            border: 'none',
            outline: 'none',
            backgroundColor: 'transparent',
            color: '#FFFFFF',
            fontFamily: 'var(--font-mono)',
            fontSize: 13,
            fontWeight: 600,
            letterSpacing: 1,
            textShadow: '0 0 5px rgba(255,255,255,0.3)'
          }}
        />
        <button 
          type="submit" 
          disabled={isSearching}
          style={{
            padding: '0 20px',
            backgroundColor: 'transparent',
            color: 'var(--color-low)', // Cyan
            borderLeft: '1px solid rgba(0, 229, 255, 0.3)',
            borderTop: 'none',
            borderRight: 'none',
            borderBottom: 'none',
            cursor: isSearching ? 'wait' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s ease',
            textShadow: '0 0 8px rgba(0,229,255,0.6)'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = 'rgba(0, 229, 255, 0.1)';
            e.currentTarget.style.boxShadow = 'inset 0 0 10px rgba(0,229,255,0.2)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'transparent';
            e.currentTarget.style.boxShadow = 'none';
          }}
        >
          {isSearching ? <Loader size={18} className="spin" /> : <Search size={18} />}
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
