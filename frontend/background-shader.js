// background-shader.js
// Implements the provided Three.js shader-based background inside #shader
(function () {
    const container = document.getElementById('shader');
    if (!container) return;

    // If Three.js is not available (CSP blocks CDN or failed to load), show a visible fallback
    if (typeof THREE === 'undefined') {
        console.warn('Three.js not loaded, shader background will not run. Showing fallback.');
        // create fallback node so user can see something and detect the issue
        const fallback = document.createElement('div');
        fallback.className = 'shader-fallback';
        fallback.textContent = 'Shader unavailable — Three.js not loaded';
        // keep pointer-events none so it doesn't block UI
        fallback.style.pointerEvents = 'none';
        container.appendChild(fallback);
        // mark container for debugging
        container.dataset.shader = 'missing';
        return;
    }

    let camera, scene, renderer, clock, uniforms;

    function init() {
        clock = new THREE.Clock();
        camera = new THREE.Camera();
        camera.position.z = 1;

        scene = new THREE.Scene();

        const geometry = new THREE.PlaneBufferGeometry(2, 2);

        uniforms = {
            u_time: { value: 1.0 },
            u_resolution: { value: new THREE.Vector2() }
        };

        const vert = document.getElementById('vertex').textContent;
        const frag = document.getElementById('fragment').textContent;

        const material = new THREE.ShaderMaterial({
            uniforms,
            vertexShader: vert,
            fragmentShader: frag
        });

        const mesh = new THREE.Mesh(geometry, material);
        scene.add(mesh);

        renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        // Cap pixel ratio for performance
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

        container.appendChild(renderer.domElement);

        onWindowResize();
        window.addEventListener('resize', onWindowResize);
    }

    function onWindowResize() {
        // Make renderer match the container size (popup may be 350px width)
        const rect = container.getBoundingClientRect();
        const w = Math.max(1, Math.floor(rect.width));
        const h = Math.max(1, Math.floor(rect.height));
        renderer.setSize(w, h, false);
        uniforms.u_resolution.value.x = w;
        uniforms.u_resolution.value.y = h;
    }

    function render() {
        uniforms.u_time.value = clock.getElapsedTime();
        renderer.render(scene, camera);
    }

    function animate() {
        render();
        requestAnimationFrame(animate);
    }

    try {
        init();
        animate();
    } catch (err) {
        console.error('Error initializing shader background:', err);
    }
})();
