// app.js
function loop() {
    const time = Date.now() / 1000;
    
    renderTissue(time);
    updateViewport();
    
    // Update Stats UI
    document.getElementById('statDepth').textContent = state.navigation.depth.toFixed(1) + " cm";
    const elapsed = Math.floor((Date.now() - state.timerStart) / 1000);
    document.getElementById('statTimer').textContent = new Date(elapsed * 1000).toISOString().substr(11, 8);

    requestAnimationFrame(loop);
}

// Tab switcher
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const target = btn.dataset.tabTarget;
        document.querySelectorAll('.tab-btn, [data-tab-panel]').forEach(el => el.classList.remove('active'));
        btn.classList.add('active');
        document.querySelector(`[data-tab-panel="${target}"]`).classList.add('active');
    });
});

// Start
window.onload = loop;