export class OCCTLoader {
    constructor() {
        this.THREE = null;
    }

    async ensureThreeLoaded() {
        if (!this.THREE) {
            this.THREE = await import("three");
        }
    }

    BuildMesh(geometryMesh, showEdges) {
        const THREE = this.THREE;

        let geometry = new THREE.BufferGeometry();

        showEdges = false;

        geometry.setAttribute(
            "position",
            new THREE.Float32BufferAttribute(
                geometryMesh.attributes.position.array,
                3
            )
        );

        if (geometryMesh.attributes.normal) {
            geometry.setAttribute(
                "normal",
                new THREE.Float32BufferAttribute(
                    geometryMesh.attributes.normal.array,
                    3
                )
            );
        } else {
            geometry.computeVertexNormals();
        }

        geometry.name = geometryMesh.name;

        const index = Uint32Array.from(geometryMesh.index.array);
        geometry.setIndex(new THREE.BufferAttribute(index, 1));

        const outlineMaterial = new THREE.LineBasicMaterial({
            color: 0x000000,
            transparent: true,
            opacity: 0.4,
            depthTest: false
        });

        const defaultMaterial = new THREE.MeshPhongMaterial({
            color: geometryMesh.color
                ? new THREE.Color(
                      geometryMesh.color[0],
                      geometryMesh.color[1],
                      geometryMesh.color[2]
                  )
                : 0xcccccc,
            specular: 0,
        });

        const mesh = new THREE.Mesh(geometry, defaultMaterial);
        mesh.name = geometryMesh.name;

        let materials = [defaultMaterial];
        const edges = showEdges ? new THREE.Group() : null;
        if (geometryMesh.brep_faces && geometryMesh.brep_faces.some(f => f.color)) {
            for (let faceColor of geometryMesh.brep_faces) {
                const color = faceColor.color
                    ? new THREE.Color(
                          faceColor.color[0],
                          faceColor.color[1],
                          faceColor.color[2]
                      )
                    : defaultMaterial.color;
                materials.push(
                    new THREE.MeshPhongMaterial({
                        color: color,
                        specular: 0,
                    })
                );
            }
            const triangleCount = geometryMesh.index.array.length / 3;
            let triangleIndex = 0;
            let faceColorGroupIndex = 0;
            while (triangleIndex < triangleCount) {
                const firstIndex = triangleIndex;
                let lastIndex = null;
                let materialIndex = null;
                if (faceColorGroupIndex >= geometryMesh.brep_faces.length) {
                    lastIndex = triangleCount;
                    materialIndex = 0;
                } else if (
                    triangleIndex <
                    geometryMesh.brep_faces[faceColorGroupIndex].first
                ) {
                    lastIndex =
                        geometryMesh.brep_faces[faceColorGroupIndex].first;
                    materialIndex = 0;
                } else {
                    lastIndex =
                        geometryMesh.brep_faces[faceColorGroupIndex].last +
                        1;
                    materialIndex = faceColorGroupIndex + 1;
                    faceColorGroupIndex++;
                }
                geometry.addGroup(
                    firstIndex * 3,
                    (lastIndex - firstIndex) * 3,
                    materialIndex
                );
                triangleIndex = lastIndex;
    
                if (edges) {
                    const innerGeometry = new THREE.BufferGeometry();

                    innerGeometry.setAttribute("position", geometry.attributes.position);

                    if (geometryMesh.attributes.normal) {
                        innerGeometry.setAttribute(
                            "normal",
                            new THREE.Float32BufferAttribute(
                                geometryMesh.attributes.normal.array,
                                3
                            )
                        );
                    }
                    innerGeometry.setIndex(
                        new THREE.BufferAttribute(
                            index.slice(firstIndex * 3, lastIndex * 3),
                            1
                        )
                    );
                    const innerEdgesGeometry = new THREE.EdgesGeometry(
                        innerGeometry,
                        180
                    );
                    const edge = new THREE.LineSegments(
                        innerEdgesGeometry,
                        outlineMaterial
                    );
                    edges.add(edge);
                }
            }
        }
        if (edges) {
            edges.renderOrder = mesh.renderOrder + 1;
        }

        return { mesh, geometry, edges };
    }

    async load(fileUrl, resultCallback) {
        console.log('OCCTLoader: load called', fileUrl);
        await this.ensureThreeLoaded();

        console.log('OCCTLoader: Importing occt-import-js...');
        const OCCT = (await import("occt-import-js")).default;

        console.log('OCCTLoader: Initializing OCCT WASM...');
        const occt = await OCCT({
            locateFile: (file) => {
                console.log('OCCTLoader: locateFile called for', file);
                if (file.endsWith(".wasm")) {
                    return "/occt-import-js.wasm";
                }
                return file;
            }
        });

        try {
            console.log('OCCTLoader: Fetching file from', fileUrl);
            const response = await fetch(fileUrl);
            const buffer = await response.arrayBuffer();
            const fileBuffer = new Uint8Array(buffer);

            console.log('OCCTLoader: Reading STEP file buffer...', fileBuffer.length);
            const occtShape = occt.ReadStepFile(fileBuffer, null);
            console.log('OCCTLoader: STEP file read result:', occtShape);

            resultCallback(occtShape, this.BuildMesh.bind(this));
        } catch (error) {
            console.error("OCCTLoader: Error loading STEP file:", error);
        }
    }
}
