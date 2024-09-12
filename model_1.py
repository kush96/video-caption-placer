import easyocr
from constants import _DEFAULT_Y_OFFSET, _DEFAULT_BG_OPACITY, _DEFAULT_TEXT_COLOR_RGB, _DEFAULT_BG_COLOR_RGB
import time
import cv2

reader = easyocr.Reader(['en'])  # Initialize the EasyOCR reader with the language you need


class Model1:

    def __init__(self, padding=20, scale_factor=0.5):
        self.padding = padding  # Padding around the subtitle box
        self.scale_factor = scale_factor  # Downscale factor for the cropped frame

    def is_subtitle_obstructed_by_text(self, frame, subtitle_text_box):
        """
        Returns True if any detected text box covers 70% of the padded subtitle box, else False.
        Additionally, draws the padded subtitle box and detected text boxes on a debug frame.
        :param frame: The entire frame (image).
        :param subtitle_text_box: The subtitle box coordinates (x, y, width, height).
        """
        # Step 1: Create a padded subtitle box
        padded_box = self.get_padded_box(subtitle_text_box, frame.shape)

        # Step 2: Crop the frame to the padded subtitle box
        cropped_frame = self.crop_frame_to_box(frame, padded_box)

        # Step 3: Optionally downscale the cropped frame for faster OCR processing
        resized_frame = self.resize_frame(cropped_frame)

        cv2.imshow("Resized Frame", resized_frame)
        # Step 4: Run OCR on the smaller, downscaled cropped frame
        text_boxes = self.run_ocr_on_frame(resized_frame)

        # Step 5: Create a debug frame by copying the original frame
        debug_frame = frame.copy()

        # Step 6: Draw the padded subtitle box in blue
        self.draw_padded_box_on_debug_frame(debug_frame, padded_box)

        # Step 7: Draw the detected text boxes in red
        self.draw_text_boxes_on_debug_frame(debug_frame, text_boxes, padded_box)

        cv2.imshow("Debug Frame", debug_frame)
        # cv2.waitKey(0)

        # Step 8: Check if any detected text box covers 70% or more of the padded box
        if self.is_text_covering_threshold(text_boxes, padded_box):
            return True  # Return debug_frame for visualization
        return False

    def get_padded_box(self, subtitle_box, frame_shape):
        """
        Adds padding to the subtitle box and ensures it doesn't exceed frame boundaries.
        :param subtitle_box: Tuple (x, y, w, h) representing the subtitle box.
        :param frame_shape: The dimensions of the full frame (height, width).
        :return: A tuple representing the padded box (x, y, w, h).
        """
        frame_height, frame_width = frame_shape[:2]
        x, y, w, h = subtitle_box

        # Add padding
        x_padded = max(0, x - self.padding)
        y_padded = max(0, y - self.padding)
        w_padded = min(w + 2 * self.padding, frame_width - x_padded)
        h_padded = min(h + 2 * self.padding, frame_height - y_padded)

        return (x_padded, y_padded, w_padded, h_padded)

    def crop_frame_to_box(self, frame, box):
        """
        Crops the frame to the given box.
        :param frame: The full image frame.
        :param box: The bounding box (x, y, w, h) to crop to.
        :return: Cropped image frame.
        """
        x, y, w, h = box
        return frame[y:y + h, x:x + w]

    def resize_frame(self, frame):
        """
        Resizes the cropped frame by the scale factor to speed up OCR.
        :param frame: The cropped image frame.
        :return: Resized frame.
        """
        height, width = frame.shape[:2]
        new_size = (int(width * self.scale_factor), int(height * self.scale_factor))
        return cv2.resize(frame, new_size, interpolation=cv2.INTER_AREA)

    def run_ocr_on_frame(self, frame):
        """
        Runs OCR on the provided frame using EasyOCR.
        :param frame: Cropped and resized frame.
        :return: List of text bounding boxes detected by OCR.
        """
        results = reader.readtext(frame)
        text_boxes = []
        for (bbox, text, prob) in results:
            (top_left, top_right, bottom_right, bottom_left) = bbox
            x = int(top_left[0])
            y = int(top_left[1])
            w = int(bottom_right[0] - top_left[0])
            h = int(bottom_right[1] - top_left[1])
            text_boxes.append((x, y, w, h))
        return text_boxes

    def is_text_covering_threshold(self, text_boxes, padded_box):
        """
        Checks if any text box covers at least 70% of the padded subtitle box area.
        :param text_boxes: List of detected text boxes (x, y, w, h).
        :param padded_box: The padded subtitle box (x, y, w, h).
        :return: True if any text box covers >= 70% of the padded box area, else False.
        """
        _, _, w_padded, h_padded = padded_box
        padded_box_area = w_padded * h_padded

        for (x, y, w, h) in text_boxes:
            text_area = w * h
            coverage_percentage = (text_area / padded_box_area) * 100

            if coverage_percentage >= 70:
                return True
        return False

    def draw_padded_box_on_debug_frame(self, debug_frame, padded_box):
        """
        Draws the padded subtitle box on the debug frame.
        :param debug_frame: Copy of the original frame where debug info is drawn.
        :param padded_box: The padded subtitle box (x, y, w, h).
        """
        x, y, w, h = padded_box
        # Draw blue rectangle for the padded subtitle box
        cv2.rectangle(debug_frame, (x, y), (x + w, y + h), (255, 0, 0), 4)  # Blue color

    def draw_text_boxes_on_debug_frame(self, debug_frame, text_boxes, padded_box):
        """
        Draws the detected OCR text boxes on the debug frame, rescaling and adjusting
        them from the cropped resized frame back to the original frame.
        :param debug_frame: Copy of the original frame where debug info is drawn.
        :param text_boxes: List of text boxes detected by OCR.
        :param padded_box: The padded subtitle box (x, y, w, h) that was used for cropping.
        """
        # Get the top-left corner of the padded box to offset the coordinates
        x_padded, y_padded, _, _ = padded_box

        for (x, y, w, h) in text_boxes:
            # Scale the coordinates back to the original padded box size
            x = int(x / self.scale_factor) + x_padded
            y = int(y / self.scale_factor) + y_padded
            w = int(w / self.scale_factor)
            h = int(h / self.scale_factor)

            # Draw red rectangles for detected text boxes
            cv2.rectangle(debug_frame, (x, y), (x + w, y + h), (0, 0, 255), 2)  # Red color

    def get_subtitles_data(self, frame, subtitle_text_box):

        start_time = time.time()

        is_subtitle_obstructed_by_text = self.is_subtitle_obstructed_by_text(frame, subtitle_text_box)

        # End timer after the function call
        end_time = time.time()

        # Calculate and log the time taken
        elapsed_time = end_time - start_time
        print(f"Time taken to get text bounding boxes: {elapsed_time:.6f} seconds")
        # Adjust the subtitle box position if overlap > 90%
        y_offset = _DEFAULT_Y_OFFSET  # Initial offset, to be adjusted if overlap occurs

        if is_subtitle_obstructed_by_text:
            y_offset += 15

        return y_offset

    # Private method to check if the overlap between two rectangles is greater than 90%
    def _is_overlap_greater_than_threshold(self, subtitle_box, frame_box):
        # Unpack the rectangles: (x, y, w, h)
        x1, y1, w1, h1 = subtitle_box
        x2, y2, w2, h2 = frame_box

        # Calculate the area of the overlap
        overlap_width = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
        overlap_height = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
        overlap_area = overlap_width * overlap_height

        # Calculate the area of the subtitle box
        subtitle_area = w1 * h1

        # Calculate the percentage of the subtitle box covered by the frame text box
        overlap_percentage = (overlap_area / subtitle_area) * 100 if subtitle_area > 0 else 0

        return overlap_percentage > self._MAX_OVERLAP_THRESHOLD

    # Private method to adjust the subtitle box position if overlap is found
    def _adjust_subtitle_position(self, subtitle_box, frame_box):
        # Move the subtitle box by 10 pixels above the frame text box
        _, y2, _, h2 = frame_box  # Extract the y position and height of the frame text box
        y_offset = y2 - h2 - 10  # Adjust the subtitle y position to be 10 pixels above the frame text box

        return y_offset
