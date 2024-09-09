import cv2
from constants import _DEFAULT_Y_OFFSET, _DEFAULT_BG_OPACITY, _DEFAULT_TEXT_COLOR_RGB, _DEFAULT_BG_COLOR_RGB, \
    _DEFAULT_H_SPACE, _DEFAULT_V_SPACE
from pyshine import putBText

from model_1 import Model1


def parse_srt_file(subtitle_path):
    """Parses the SRT file and returns a list of subtitles with their timecodes."""
    subtitles = []
    with open(subtitle_path, 'r') as file:
        content = file.read()
        srt_blocks = content.strip().split('\n\n')

        for block in srt_blocks:
            lines = block.split('\n')
            index = int(lines[0])
            timecodes = lines[1].split(' --> ')
            start_time = timecodes[0]
            end_time = timecodes[1]
            text = ' '.join(lines[2:])

            subtitles.append({
                'index': index,
                'start_time': start_time,
                'end_time': end_time,
                'text': text
            })
    return subtitles


def time_to_seconds(time_str):
    """Converts a time string (HH:MM:SS,mmm) to seconds."""
    hours, minutes, seconds = time_str.split(':')
    seconds, milliseconds = seconds.split(',')
    total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000.0
    return total_seconds


def _get_subtitle_text_box(subtitle_text, font_scale, thickness, hspace, vspace, text_x, text_y):
    """returns (x,y,w,h)"""
    # Calculate the rectangle coordinates
    text_size = \
        cv2.getTextSize(subtitle_text, fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=font_scale, thickness=thickness)[0]
    rect_width = text_size[0] + 2 * hspace
    rect_height = text_size[1] + 2 * vspace
    return text_x, text_y, rect_width, rect_height


def add_subtitles_realtime(video_path, subtitle_path, text_color=_DEFAULT_TEXT_COLOR_RGB,
                           bg_color=_DEFAULT_BG_COLOR_RGB, bg_opacity=_DEFAULT_BG_OPACITY, y_offset=_DEFAULT_Y_OFFSET):
    # Load video using OpenCV
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Load and parse subtitles
    subtitles = parse_srt_file(subtitle_path)

    # Convert subtitle start and end times to seconds
    for subtitle in subtitles:
        subtitle['start_time_seconds'] = time_to_seconds(subtitle['start_time'])
        subtitle['end_time_seconds'] = time_to_seconds(subtitle['end_time'])

    # Define the font and text properties
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    thickness = 1

    # Initialize variables for processing
    frame_count = 0
    cur_idx = 0
    subtitle_text = ''  # Initialize subtitle text to be empty

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Calculate current time in video
        cur_time = frame_count / fps

        # Check if we need to update the subtitle
        if cur_idx < len(subtitles):
            # If current time exceeds end time of current subtitle, move to next
            if cur_time > subtitles[cur_idx]['end_time_seconds']:
                cur_idx += 1
                subtitle_text = ''  # Clear the subtitle text after the end time

            # Check if current time has reached the start time of the next subtitle
            if cur_idx < len(subtitles) and cur_time >= subtitles[cur_idx]['start_time_seconds']:
                subtitle_text = subtitles[cur_idx]['text']

        # Calculate position to center the text
        text_size = cv2.getTextSize(subtitle_text, font, font_scale, thickness)[0]
        text_x = (frame.shape[1] - text_size[0]) // 2
        text_y = frame.shape[0] - y_offset

        # Create a background rectangle with specified opacity
        if subtitle_text:
            # let's check if another text already present
            bg_opacity, text_color_rgb, bg_color_rgb, y_offset = Model1().get_subtitles_data(frame,
                                                                                             _get_subtitle_text_box(
                                                                                                 subtitle_text,
                                                                                                 font_scale, thickness,
                                                                                                 _DEFAULT_H_SPACE,
                                                                                                 _DEFAULT_V_SPACE,
                                                                                                 text_x, text_y))

            subtitled_frame = putBText(
                frame,  # The frame on which to draw the text
                text=subtitle_text,  # The subtitle text to display
                text_offset_x=text_x,  # X position of the text
                text_offset_y=text_y,  # Y position of the text
                vspace=_DEFAULT_V_SPACE,  # Vertical padding for the background
                hspace=_DEFAULT_H_SPACE,  # Horizontal padding for the background
                font_scale=font_scale,  # Font scale
                text_RGB=text_color,
                thickness=thickness,
                background_RGB=bg_color,
                alpha=bg_opacity,  # Opacity of the background (0: fully transparent, 1: fully opaque)
                font=cv2.FONT_HERSHEY_SIMPLEX  # Font style
            )
            frame = subtitled_frame
            # cv2.imshow("Result", frame)
            # cv2.waitKey(0)

        # Display the frame in a window
        cv2.imshow('Video with Subtitles', frame)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        frame_count += 1

    # Release resources
    cap.release()
    cv2.destroyAllWindows()


def main():
    # Example usage
    video_path = 'input_files/I Flew 10,000 km To Play Pro Events!.mp4'
    subtitle_path = 'input_files/I Flew 10,000 km To Play Pro Events!.srt'

    add_subtitles_realtime(video_path, subtitle_path, text_color=(255, 255, 255),
                           bg_color=(0, 0, 0), bg_opacity=0.5, y_offset=50)


if __name__ == "__main__":
    main()
