// Configuration module for environment-specific settings

/**
 * API configuration
 */
export const API_CONFIG = {
  /**
   * Base URL for the API
   * This can be overridden by setting the VITE_API_BASE_URL environment variable
   */
  baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  
  /**
   * Audio endpoint path
   */
  audioEndpoint: '/api/audio',
  
  /**
   * Get the full URL for the audio API endpoint
   */
  getAudioUrl: (prompt: string): string => {
    return `${API_CONFIG.baseUrl}${API_CONFIG.audioEndpoint}?prompt=${encodeURIComponent(prompt)}`;
  }
};