import os
import tempfile
import logging
from typing import Optional

from PyQt6.QtCore import QObject, QUrl, pyqtSignal
from PyQt6.QtMultimedia import (
    QMediaCaptureSession,
    QAudioInput,
    QMediaRecorder,
    QMediaFormat
)

logger = logging.getLogger("NovaAgent.AudioRecorder")


class AudioRecorder(QObject):
    """
    Asynchronous microphone voice recorder using PyQt6 QtMultimedia.
    Records clean uncompressed Wave audio for direct Gemini ingestion.
    """
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal(str)   # emits path to recorded .wav file
    recording_failed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = QMediaCaptureSession()
        self.audio_input = QAudioInput()
        self.session.setAudioInput(self.audio_input)

        self.recorder = QMediaRecorder()
        self.session.setRecorder(self.recorder)

        # Configure Wave format
        media_format = QMediaFormat()
        media_format.setFileFormat(QMediaFormat.FileFormat.Wave)
        media_format.setAudioCodec(QMediaFormat.AudioCodec.Wave)
        self.recorder.setMediaFormat(media_format)

        self.current_output_path: Optional[str] = None
        self._is_recording = False

        # Connect errorChanged (safe across PyQt6 versions without scoped-enum unislot errors)
        try:
            self.recorder.errorChanged.connect(self._on_error_changed)
        except Exception as e:
            logger.debug(f"Could not connect errorChanged: {e}")

    def is_recording(self) -> bool:
        return self._is_recording

    def start_recording(self, save_path: Optional[str] = None) -> bool:
        """Starts recording audio from default microphone."""
        if self._is_recording:
            logger.warning("Recording already in progress.")
            return False

        try:
            if not save_path:
                temp_dir = tempfile.gettempdir()
                save_path = os.path.join(temp_dir, "nova_voice_prompt.wav")

            # Remove previous file if exists
            if os.path.exists(save_path):
                try:
                    os.remove(save_path)
                except Exception as e:
                    logger.debug(f"Could not remove stale recording: {e}")

            self.current_output_path = save_path
            self.recorder.setOutputLocation(QUrl.fromLocalFile(save_path))
            self.recorder.record()
            self._is_recording = True
            logger.info(f"Microphone recording started -> {save_path}")
            self.recording_started.emit()
            return True
        except Exception as exc:
            logger.error(f"Failed to start audio recording: {exc}", exc_info=True)
            self._is_recording = False
            self.recording_failed.emit(str(exc))
            return False

    def stop_recording(self) -> Optional[str]:
        """Stops recording and returns the path to the recorded WAV file."""
        if not self._is_recording:
            return None

        try:
            self.recorder.stop()
            self._is_recording = False
            saved_file = self.current_output_path
            logger.info(f"Microphone recording stopped. File: {saved_file}")
            if saved_file:
                self.recording_stopped.emit(saved_file)
            return saved_file
        except Exception as exc:
            logger.error(f"Error stopping audio recording: {exc}", exc_info=True)
            self._is_recording = False
            self.recording_failed.emit(str(exc))
            return None

    def _on_error_changed(self):
        err = self.recorder.error()
        if err != QMediaRecorder.Error.NoError:
            err_msg = self.recorder.errorString()
            logger.error(f"Recorder error ({err}): {err_msg}")
            self._is_recording = False
            self.recording_failed.emit(err_msg)
