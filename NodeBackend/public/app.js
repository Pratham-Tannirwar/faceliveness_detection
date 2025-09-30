class FaceLiveApp {
    constructor() {
        this.video = document.getElementById('video');
        this.canvas = document.getElementById('canvas');
        this.ctx = this.canvas.getContext('2d');
        this.faceOverlay = document.getElementById('face-overlay');
        
        this.socket = null;
        this.stream = null;
        this.isDetecting = false;
        this.isStreaming = false;
        this.currentRoom = null;
        
        this.initializeElements();
        this.setupEventListeners();
        this.initializeSocket();
        this.loadFaceAPI();
    }

    initializeElements() {
        this.startBtn = document.getElementById('startBtn');
        this.stopBtn = document.getElementById('stopBtn');
        this.detectBtn = document.getElementById('detectBtn');
        this.streamBtn = document.getElementById('streamBtn');
        this.joinRoomBtn = document.getElementById('joinRoom');
        this.roomIdInput = document.getElementById('roomId');
        
        this.cameraStatus = document.getElementById('cameraStatus');
        this.detectionStatus = document.getElementById('detectionStatus');
        this.faceCount = document.getElementById('faceCount');
        this.connectionStatus = document.getElementById('connectionStatus');
    }

    setupEventListeners() {
        this.startBtn.addEventListener('click', () => this.startCamera());
        this.stopBtn.addEventListener('click', () => this.stopCamera());
        this.detectBtn.addEventListener('click', () => this.toggleDetection());
        this.streamBtn.addEventListener('click', () => this.toggleStreaming());
        this.joinRoomBtn.addEventListener('click', () => this.joinRoom());
    }

    initializeSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            this.updateConnectionStatus('Connected', 'success');
        });
        
        this.socket.on('disconnect', () => {
            this.updateConnectionStatus('Disconnected', 'error');
        });
        
        this.socket.on('face-detection-update', (data) => {
            this.handleRemoteFaceDetection(data);
        });
        
        this.socket.on('stream-update', (data) => {
            this.handleRemoteStream(data);
        });
    }

    async loadFaceAPI() {
        try {
            await Promise.all([
                faceapi.nets.tinyFaceDetector.loadFromUri('/models'),
                faceapi.nets.faceLandmark68Net.loadFromUri('/models'),
                faceapi.nets.faceRecognitionNet.loadFromUri('/models'),
                faceapi.nets.faceExpressionNet.loadFromUri('/models')
            ]);
            console.log('Face-API models loaded successfully');
        } catch (error) {
            console.error('Error loading Face-API models:', error);
            // Fallback: use basic face detection without models
        }
    }

    async startCamera() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: 'user'
                }
            });
            
            this.video.srcObject = this.stream;
            this.video.play();
            
            this.startBtn.disabled = true;
            this.stopBtn.disabled = false;
            this.detectBtn.disabled = false;
            this.streamBtn.disabled = false;
            
            this.updateCameraStatus('Active', 'success');
            
            // Set canvas dimensions to match video
            this.video.addEventListener('loadedmetadata', () => {
                this.canvas.width = this.video.videoWidth;
                this.canvas.height = this.video.videoHeight;
            });
            
        } catch (error) {
            console.error('Error accessing camera:', error);
            alert('Camera access denied. Please allow camera access and refresh the page.');
        }
    }

    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        
        this.video.srcObject = null;
        this.isDetecting = false;
        this.isStreaming = false;
        
        this.startBtn.disabled = false;
        this.stopBtn.disabled = true;
        this.detectBtn.disabled = true;
        this.streamBtn.disabled = true;
        
        this.updateCameraStatus('Stopped', 'error');
        this.updateDetectionStatus('Inactive', 'error');
        this.updateFaceCount(0);
        
        this.clearFaceOverlay();
    }

    async toggleDetection() {
        if (!this.isDetecting) {
            this.startDetection();
        } else {
            this.stopDetection();
        }
    }

    startDetection() {
        this.isDetecting = true;
        this.detectBtn.textContent = 'Stop Detection';
        this.detectBtn.classList.remove('btn-success');
        this.detectBtn.classList.add('btn-secondary');
        this.updateDetectionStatus('Active', 'success');
        
        this.detectFaces();
    }

    stopDetection() {
        this.isDetecting = false;
        this.detectBtn.textContent = 'Start Detection';
        this.detectBtn.classList.remove('btn-secondary');
        this.detectBtn.classList.add('btn-success');
        this.updateDetectionStatus('Inactive', 'error');
        
        this.clearFaceOverlay();
        this.updateFaceCount(0);
    }

    async detectFaces() {
        if (!this.isDetecting || !this.video.videoWidth) {
            return;
        }

        try {
            // Draw current video frame to canvas
            this.ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
            
            // Detect faces using Face-API.js
            const detections = await faceapi.detectAllFaces(
                this.canvas,
                new faceapi.TinyFaceDetectorOptions()
            ).withFaceLandmarks().withFaceExpressions();

            this.updateFaceCount(detections.length);
            this.drawFaceBoxes(detections);
            
            // Send detection data to server if in a room
            if (this.currentRoom && this.socket) {
                this.socket.emit('face-detection', {
                    roomId: this.currentRoom,
                    detections: detections.map(detection => ({
                        box: detection.detection.box,
                        landmarks: detection.landmarks,
                        expressions: detection.expressions
                    })),
                    timestamp: Date.now()
                });
            }
            
        } catch (error) {
            console.error('Face detection error:', error);
        }
        
        // Continue detection loop
        if (this.isDetecting) {
            requestAnimationFrame(() => this.detectFaces());
        }
    }

    drawFaceBoxes(detections) {
        this.clearFaceOverlay();
        
        detections.forEach(detection => {
            const { x, y, width, height } = detection.detection.box;
            const scaleX = this.video.offsetWidth / this.video.videoWidth;
            const scaleY = this.video.offsetHeight / this.video.videoHeight;
            
            const faceBox = document.createElement('div');
            faceBox.className = 'face-box';
            faceBox.style.left = `${x * scaleX}px`;
            faceBox.style.top = `${y * scaleY}px`;
            faceBox.style.width = `${width * scaleX}px`;
            faceBox.style.height = `${height * scaleY}px`;
            
            this.faceOverlay.appendChild(faceBox);
        });
    }

    clearFaceOverlay() {
        this.faceOverlay.innerHTML = '';
    }

    toggleStreaming() {
        if (!this.isStreaming) {
            this.startStreaming();
        } else {
            this.stopStreaming();
        }
    }

    startStreaming() {
        this.isStreaming = true;
        this.streamBtn.textContent = 'Stop Streaming';
        this.streamBtn.classList.remove('btn-info');
        this.streamBtn.classList.add('btn-secondary');
        
        // Start streaming loop
        this.streamLoop();
    }

    stopStreaming() {
        this.isStreaming = false;
        this.streamBtn.textContent = 'Start Streaming';
        this.streamBtn.classList.remove('btn-secondary');
        this.streamBtn.classList.add('btn-info');
    }

    streamLoop() {
        if (!this.isStreaming) return;
        
        // Capture frame and send to server
        if (this.currentRoom && this.socket) {
            this.ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
            const imageData = this.canvas.toDataURL('image/jpeg', 0.8);
            
            this.socket.emit('stream-data', {
                roomId: this.currentRoom,
                imageData: imageData,
                timestamp: Date.now()
            });
        }
        
        // Continue streaming
        setTimeout(() => this.streamLoop(), 100); // 10 FPS
    }

    joinRoom() {
        const roomId = this.roomIdInput.value.trim();
        if (!roomId) {
            alert('Please enter a room ID');
            return;
        }
        
        this.currentRoom = roomId;
        this.socket.emit('join-room', roomId);
        this.joinRoomBtn.textContent = 'Leave Room';
        this.joinRoomBtn.classList.remove('btn-outline');
        this.joinRoomBtn.classList.add('btn-secondary');
        
        console.log(`Joined room: ${roomId}`);
    }

    handleRemoteFaceDetection(data) {
        // Handle face detection data from other users
        console.log('Remote face detection:', data);
    }

    handleRemoteStream(data) {
        // Handle stream data from other users
        console.log('Remote stream data:', data);
    }

    updateCameraStatus(status, type) {
        this.cameraStatus.textContent = status;
        this.cameraStatus.className = `status ${type}`;
    }

    updateDetectionStatus(status, type) {
        this.detectionStatus.textContent = status;
        this.detectionStatus.className = `status ${type}`;
    }

    updateFaceCount(count) {
        this.faceCount.textContent = count;
    }

    updateConnectionStatus(status, type) {
        this.connectionStatus.textContent = status;
        this.connectionStatus.className = `status ${type}`;
    }
}

// Initialize the app when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new FaceLiveApp();
});

