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
   * Speech endpoint path
   */
  speechEndpoint: '/api/speech',

  /**
   * Get the full URL for the audio API endpoint
   */
  getAudioUrl: (prompt: string, voice?: string): string => {
    const params = new URLSearchParams({
      prompt: prompt
    });
    if (voice) {
      params.append('voice', voice);
    }
    return `${API_CONFIG.baseUrl}${API_CONFIG.audioEndpoint}?${params.toString()}`;
  },

  /**
   * Get the full URL for the speech API endpoint
   */
  getSpeechUrl: (): string => {
    return `${API_CONFIG.baseUrl}${API_CONFIG.speechEndpoint}`;
  }
};
