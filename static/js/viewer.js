import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { OCCTLoader } from './view/OCCTLoader.js';

export class DFMViewer {
    constructor(elementId) {
        this.container = document.getElementById(elementId);
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(45, this.container.clientWidth / this.container.clientHeight, 0.1, 10000);
        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.container.appendChild(this.renderer.domElement);

        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;

        const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        this.scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
        directionalLight.position.set(10, 10, 10);
        this.scene.add(directionalLight);

        this.modelGroup = new THREE.Group();
        this.scene.add(this.modelGroup);

        this.markers = new THREE.Group();
        this.scene.add(this.markers);

        this.loader = new OCCTLoader();
        this.currentData = null;

        window.addEventListener('resize', () => this.onWindowResize());
        this.animate();
    }

    onWindowResize() {
        this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }

    async loadModel(url, analysisData) {
        console.log('ThreeJS: loadModel called', { url, analysisData });
        this.currentData = analysisData;
        
        // Clear previous
        console.log('ThreeJS: Clearing scene...');
        while(this.modelGroup.children.length > 0) this.modelGroup.remove(this.modelGroup.children[0]);
        while(this.markers.children.length > 0) this.markers.remove(this.markers.children[0]);

        console.log('ThreeJS: Starting OCCTLoader.load()...');
        this.loader.load(url, (occtResult, buildMeshFunc) => {
            console.log('ThreeJS: OCCTLoader callback received', occtResult);
            if (occtResult && occtResult.success && occtResult.meshes) {
                console.log(`ThreeJS: Building ${occtResult.meshes.length} meshes...`);
                occtResult.meshes.forEach(meshData => {
                    const { mesh, edges } = buildMeshFunc(meshData, true);
                    this.modelGroup.add(mesh);
                    if (edges) this.modelGroup.add(edges);
                });

                // Center camera
                const box = new THREE.Box3().setFromObject(this.modelGroup);
                const center = box.getCenter(new THREE.Vector3());
                const size = box.getSize(new THREE.Vector3());
                
                const maxDim = Math.max(size.x, size.y, size.z);
                const fov = this.camera.fov * (Math.PI / 180);
                let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2)) * 1.5;

                this.camera.position.set(center.x + cameraZ, center.y + cameraZ, center.z + cameraZ);
                this.controls.target.copy(center);
                this.controls.update();

                // Add DFM Markers
                this.addDFMMarkers();
            }
        });
    }

    addDFMMarkers() {
        if (!this.currentData || !this.currentData.dfm_feedback) return;

        this.currentData.dfm_feedback.forEach(feedback => {
            const color = this.getSeverityColor(feedback.severity);
            
            feedback.geometric_references.forEach(ref => {
                if (ref.type === 'face' && this.currentData.geometry_index.faces[ref.id]) {
                    const face = this.currentData.geometry_index.faces[ref.id];
                    this.createMarker(face.centroid, color, feedback.message);
                }
            });
        });
    }

    createMarker(pos, color, message) {
        const geometry = new THREE.SphereGeometry(2, 16, 16);
        const material = new THREE.MeshPhongMaterial({ 
            color: color, 
            emissive: color,
            emissiveIntensity: 0.5,
            transparent: true,
            opacity: 0.8
        });
        const sphere = new THREE.Mesh(geometry, material);
        sphere.position.set(pos[0], pos[1], pos[2]);
        sphere.userData = { message: message };
        this.markers.add(sphere);
    }

    getSeverityColor(severity) {
        switch(severity) {
            case 'high': return 0xef4444;
            case 'medium': return 0xf59e0b;
            case 'low': return 0x10b981;
            default: return 0x3b82f6;
        }
    }

    highlightRule(feedback) {
        // Clear highlight highlight?
        // For now, let's pulse the markers related to this feedback
        this.markers.children.forEach(marker => {
            marker.scale.set(1, 1, 1);
            marker.material.opacity = 0.8;
        });

        feedback.geometric_references.forEach(ref => {
            if (ref.type === 'face' && this.currentData.geometry_index.faces[ref.id]) {
                const pos = this.currentData.geometry_index.faces[ref.id].centroid;
                const marker = this.markers.children.find(m => 
                    Math.abs(m.position.x - pos[0]) < 0.1 && 
                    Math.abs(m.position.y - pos[1]) < 0.1 && 
                    Math.abs(m.position.z - pos[2]) < 0.1
                );
                if (marker) {
                    marker.scale.set(3, 3, 3);
                    marker.material.opacity = 1.0;
                    
                    // Smoothly move camera to target
                    // Simple version: just jump
                    // this.controls.target.set(pos[0], pos[1], pos[2]);
                }
            }
        });
    }
}
