// File: src/components/chat/WelcomeScreen.js
// Description: Displays a welcome message and suggestion prompts on a new chat screen.

import styles from './WelcomeScreen.module.scss';

// Example queries for the user to click
const suggestions = [
  {
    title: "Analyze thermal anomaly",
    query: "Show me the thermal anomaly data for the North Atlantic region for Q3 2024."
  },
  {
    title: "Track vessel",
    query: "Track the current location and trajectory of vessel IMO 9432123."
  },
  {
    title: "Forecast conditions",
    query: "Forecast the wave height and wind speed for the coast of California for the next 48 hours."
  },
  {
    title: "Identify coral bleaching",
    query: "Identify areas with a high probability of coral bleaching in the Great Barrier Reef."
  }
];


export default function WelcomeScreen({ onSuggestionClick }) {
  return (
    <div className={styles.welcomeContainer}>
      <div className={styles.welcomeMessage}>
        <h1 className={styles.title}>Ocean AI Analytics</h1>
        <p className={styles.subtitle}>Welcome to the analytics interface. How can I assist you today?</p>
      </div>
      <div className={styles.suggestionsGrid}>
        {suggestions.map((suggestion, index) => (
          <button
            key={index}
            className={styles.suggestionBox}
            onClick={() => onSuggestionClick(suggestion.query)}
          >
            <strong>{suggestion.title}</strong>
            <p>{suggestion.query}</p>
          </button>
        ))}
      </div>
    </div>
  );
}