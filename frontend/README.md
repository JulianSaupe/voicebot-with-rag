# AI Voicebot Frontend

A modern, futuristic chatbot frontend built with SvelteKit featuring a dark theme and animated speech bubble that responds to audio levels.

## Features

- **🎨 Modern Dark Theme**: Sleek gradient backgrounds with cyan/teal accent colors
- **🎤 Animated Speech Bubble**: Dynamic speech bubble that changes shape based on audio output levels
- **⚡ Toggle Control**: Futuristic toggle switch to enable/disable the voicebot
- **📱 Responsive Design**: Optimized for desktop and mobile devices
- **✨ Rich Animations**: Particles, glowing effects, and smooth transitions

## Components

### SpeechBubble.svelte
The main visual centerpiece featuring:
- Dynamic scaling based on audio levels
- Animated sound waves that respond to audio intensity
- Floating particles around the bubble when active
- Different visual states (inactive, active, listening)
- Smooth glow effects and pulsing animations

### ToggleSwitch.svelte
A custom toggle component with:
- Smooth thumb animation
- Glowing effects when enabled
- Icons to indicate on/off states
- Hover and focus states
- Fully accessible with ARIA labels

## Development

### Prerequisites
- Node.js 18+ 
- npm or pnpm

### Getting Started

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open your browser to `http://localhost:5173`

### Building for Production

```bash
npm run build
```

### Testing

```bash
npm run test
```

## Customization

### Colors
The main color scheme uses cyan/teal colors. To customize:
- Primary: `#40e0d0` (turquoise)
- Secondary: `#00bcd4` (cyan) 
- Accent: `#0097a7` (dark cyan)

### Audio Integration
Currently uses mock audio levels for demonstration. To integrate with real audio:

1. Replace the `audioLevel` simulation in `+page.svelte`
2. Connect to your audio processing pipeline

### Speech Bubble Behavior
Customize the speech bubble animation by modifying:
- `bubbleScale`: Controls size changes (based on audio level)
- `glowIntensity`: Controls glow effect intensity
- `pulseSpeed`: Controls animation speed

## Architecture

```
src/
├── routes/
│   └── +page.svelte          # Main page
├── lib/
│   ├── SpeechBubble.svelte    # Animated speech bubble
│   └── ToggleSwitch.svelte    # Toggle control
└── app.html                   # Base HTML template
```

## Browser Support

- Modern browsers with ES2020+ support
- CSS Grid and Flexbox support
- CSS custom properties (variables)
- Backdrop-filter support for blur effects

## Future Enhancements

- [ ] Real-time speech recognition integration
- [ ] Multiple voice profiles
- [ ] Conversation history
- [ ] Voice activity detection
- [ ] Custom color themes
- [ ] Sound visualization improvements

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

Built with ❤️ using SvelteKit and modern web technologies.
