// controls.js
function navInput(action, boost = 1) {
    const step = (state.navigation.speed === 'fast' ? 3.0 : 1.5) * boost;

    if (state.imaging.mode === 'external' && state.imaging.externalImage) {
        const img = state.imaging.externalImage;
        const moveAmount = step * 10;
        const viewSize = 220 / state.imaging.zoom;

        if (action === 'forward') state.imaging.viewY -= moveAmount;
        if (action === 'backward') state.imaging.viewY += moveAmount;
        if (action === 'left') state.imaging.viewX -= moveAmount;
        if (action === 'right') state.imaging.viewX += moveAmount;

        // Boundaries
        state.imaging.viewX = Math.max(0, Math.min(img.width - viewSize, state.imaging.viewX));
        state.imaging.viewY = Math.max(0, Math.min(img.height - viewSize, state.imaging.viewY));
    } else {
        if (action === 'forward') state.navigation.depth += step;
        if (action === 'backward') state.navigation.depth -= step;
    }
}

// Listeners
document.getElementById('imageUploader').addEventListener('change', (e) => {
  const file = e.target.files[0];
  const reader = new FileReader();
  reader.onload = (event) => {
    const img = new Image();
    img.onload = () => {
      state.imaging.externalImage = img;
      state.imaging.mode = 'external';
      state.imaging.viewX = 0; state.imaging.viewY = 0;
      document.getElementById('toggleModeBtn').textContent = "Mode: External";
      document.getElementById('statMode').textContent = "External";
    };
    img.src = event.target.result;
  };
  reader.readAsDataURL(file);
});

document.getElementById('toggleModeBtn').addEventListener('click', () => {
    state.imaging.mode = (state.imaging.mode === 'synth' ? 'external' : 'synth');
    document.getElementById('toggleModeBtn').textContent = (state.imaging.mode === 'synth' ? "Mode: Synth" : "Mode: External");
    document.getElementById('statMode').textContent = state.imaging.mode.toUpperCase();
});

// Keyboard Listeners
window.addEventListener('keydown', (e) => {
  if (e.key === 'ArrowUp') navInput('forward');
  if (e.key === 'ArrowDown') navInput('backward');
  if (e.key === 'ArrowLeft') navInput('left');
  if (e.key === 'ArrowRight') navInput('right');
});