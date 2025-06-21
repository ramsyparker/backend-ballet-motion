import tensorflow as tf
import numpy as np
import cv2
import os

class BalletPoseModel:
    def __init__(self, model_path=None):
        if model_path is None:
            # Use default path relative to current file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(current_dir, 'ballet_model.tflite')
        
        # Check if model file exists
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"TFLite model not found at: {model_path}")
            
        try:
            # Load TFLite model
            self.interpreter = tf.lite.Interpreter(model_path=model_path)
            self.interpreter.allocate_tensors()

            # Get input and output tensors
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            
            # Get input shape
            self.input_shape = self.input_details[0]['shape']
            
        except Exception as e:
            raise RuntimeError(f"Failed to load TFLite model: {str(e)}")
        
    def preprocess_image(self, frame):
        # Resize image to match model input shape
        input_img = cv2.resize(frame, (self.input_shape[1], self.input_shape[2]))
        # Expand dimensions and normalize
        input_img = np.expand_dims(input_img, axis=0)
        input_img = input_img.astype(np.float32) / 255.0
        return input_img

    def detect_pose(self, frame):
        # Preprocess the image
        processed_img = self.preprocess_image(frame)
        
        # Set input tensor
        self.interpreter.set_tensor(self.input_details[0]['index'], processed_img)
        
        # Run inference
        self.interpreter.invoke()
        
        # Get results
        outputs = {}
        for output_detail in self.output_details:
            output_data = self.interpreter.get_tensor(output_detail['index'])
            outputs[output_detail['name']] = output_data

        return outputs

    def close(self):
        # Clean up resources if needed
        pass