from flask import Blueprint, Response, jsonify
import cv2
import numpy as np
from models.pose_model import BalletPoseModel
import queue

detection_bp = Blueprint('detection', __name__)

# Global variables
frame_queue = queue.Queue(maxsize=10)
stop_stream = False
pose_model = BalletPoseModel()

def generate_frames():
    # Initialize video capture
    cap = cv2.VideoCapture(0)  # Use 0 for webcam
    
    global stop_stream
    while not stop_stream:
        success, frame = cap.read()
        if not success:
            break
            
        # Process frame with TFLite model
        results = pose_model.detect_pose(frame)
        
        # Draw detections on frame
        annotated_frame = draw_detections(frame, results)
            
        try:
            frame_queue.put_nowait({
                'frame': annotated_frame,
                'predictions': results
            })
        except queue.Full:
            frame_queue.get()
            frame_queue.put({
                'frame': annotated_frame,
                'predictions': results
            })
        
        # Encode frame for streaming
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        frame_bytes = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    
    cap.release()

def draw_detections(frame, results):
    """
    Draw the pose detection results on the frame
    Modify this based on your model's output format
    """
    # Example: Draw keypoints if your model outputs them
    try:
        # Get keypoints from results
        keypoints = results.get('keypoints', [])
        
        # Draw each keypoint
        for point in keypoints:
            x, y = int(point[0]), int(point[1])
            cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
            
        # Draw connections between keypoints if needed
        # Add your connection drawing logic here
            
    except Exception as e:
        print(f"Error drawing detections: {str(e)}")
        
    return frame

@detection_bp.route('/video-feed')
def video_feed():
    """
    Route for streaming video with pose detection
    """
    global stop_stream
    stop_stream = False
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@detection_bp.route('/stop-stream', methods=['POST'])
def stop_video_stream():
    """
    Route to stop the video stream
    """
    global stop_stream
    stop_stream = True
    return jsonify({'message': 'Stream stopped'})

@detection_bp.route('/get-predictions')
def get_predictions():
    """
    Route to get the latest predictions
    """
    try:
        data = frame_queue.get_nowait()
        return jsonify({
            'success': True,
            'predictions': data['predictions']
        })
    except queue.Empty:
        return jsonify({
            'success': False,
            'message': 'No predictions available'
        })