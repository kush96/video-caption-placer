import easyocr
from constants import _DEFAULT_Y_OFFSET, _DEFAULT_BG_OPACITY, _DEFAULT_TEXT_COLOR_RGB, _DEFAULT_BG_COLOR_RGB
import time
reader = easyocr.Reader(['en'])  # Initialize the EasyOCR reader with the language you need


class Model1:
    _MAX_OVERLAP_THRESHOLD = 90  # in percentage

    def get_text_bounding_boxes(self, frame):
        """Returns a list of bounding boxes for detected text using EasyOCR."""
        results = reader.readtext(frame)  # Returns a list of results with bounding boxes and text
        text_boxes = []
        for (bbox, text, prob) in results:
            (top_left, top_right, bottom_right, bottom_left) = bbox
            x = int(top_left[0])
            y = int(top_left[1])
            w = int(bottom_right[0] - top_left[0])
            h = int(bottom_right[1] - top_left[1])
            text_boxes.append((x, y, w, h))  # Append the bounding box (x, y, width, height)
        return text_boxes

    def get_subtitles_data(self, frame, subtitle_text_box):
        bg_opacity = _DEFAULT_BG_OPACITY
        text_color_rgb = _DEFAULT_TEXT_COLOR_RGB
        bg_color_rgb = _DEFAULT_BG_COLOR_RGB

        start_time = time.time()

        frame_text_boxes = self.get_text_bounding_boxes(frame)

        # End timer after the function call
        end_time = time.time()

        # Calculate and log the time taken
        elapsed_time = end_time - start_time
        print(f"Time taken to get text bounding boxes: {elapsed_time:.6f} seconds")
        print(f"text boxes found == {len(frame_text_boxes)}")
        # Adjust the subtitle box position if overlap > 90%
        y_offset = _DEFAULT_Y_OFFSET  # Initial offset, to be adjusted if overlap occurs
        for frame_text_box in frame_text_boxes:
            if self._is_overlap_greater_than_threshold(subtitle_text_box, frame_text_box):
                y_offset = self._adjust_subtitle_position(subtitle_text_box, frame_text_box)
                break  # Apply once for the first overlapping box

        return (bg_opacity, text_color_rgb, bg_color_rgb, y_offset)

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