// state.js
const state = {
  imaging: {
    mode: 'synth', // 'synth' or 'external'
    externalImage: null,
    viewX: 0, 
    viewY: 0,
    zoom: 1,
    frame: 0
  },
  navigation: {
    depth: 18.0,
    speed: 'normal'
  },
  processing: {
    contrast: 35
  },
  timerStart: Date.now()
};

function logAction(text) {
    console.log(`[LOG] ${text}`);
}