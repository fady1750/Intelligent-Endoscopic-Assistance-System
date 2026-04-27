// engine.js
const simCanvas = document.createElement('canvas');
simCanvas.width = 220; simCanvas.height = 220;
const sctx = simCanvas.getContext('2d');

function renderTissue(time) {
  sctx.clearRect(0, 0, 220, 220);

  if (state.imaging.mode === 'external' && state.imaging.externalImage) {
    // DRAW LOADED PHOTO (MOWING)
    const img = state.imaging.externalImage;
    const z = state.imaging.zoom;
    const viewSize = 220 / z; 
    
    sctx.drawImage(
      img, 
      state.imaging.viewX, state.imaging.viewY, viewSize, viewSize, // Source crop
      0, 0, 220, 220 // Destination
    );
  } else {
    // DRAW PROCEDURAL NOISE
    sctx.fillStyle = '#2b1116';
    sctx.fillRect(0, 0, 220, 220);
    sctx.fillStyle = 'rgba(255,100,100,0.1)';
    sctx.beginPath();
    sctx.arc(110 + Math.sin(time)*30, 110, 60, 0, Math.PI*2);
    sctx.fill();
  }
}

function updateViewport() {
    const vctx = document.getElementById('viewportCanvas').getContext('2d');
    const pctx = document.getElementById('previewProcessed').getContext('2d');
    
    // Apply contrast filter from state
    vctx.filter = `contrast(${100 + state.processing.contrast}%)`;
    vctx.drawImage(simCanvas, 0, 0);

    // Update processing tab preview
    pctx.drawImage(simCanvas, 0, 0, 220, 220, 0, 0, 400, 200);
}