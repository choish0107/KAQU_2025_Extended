#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from faster_whisper import WhisperModel
import pyaudio
import numpy as np
import time
import noisereduce as nr

class FasterWhisperSTTNode(Node):
    def __init__(self):
        super().__init__('my_stt_whisper')
        
        # Faster Whisper 모델 로드 (small 버전, CPU 사용)
        self.model = WhisperModel("small", device="cpu", compute_type="int8")
        
        # ROS Publisher 생성
        self.publisher_ = self.create_publisher(String, 'STT_topic', 10)
        
        # 오디오 설정
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = 1024
        self.RECORD_SECONDS = 60
        
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(format=self.FORMAT,
                                      channels=self.CHANNELS,
                                      rate=self.RATE,
                                      input=True,
                                      frames_per_buffer=self.CHUNK)
        self.get_logger().info("🎤 실시간 한국어 음성 인식 시작!")
        self.get_logger().info("시스템 활성화를 위해 '안녕'이라고 말해주세요.")
    
    def record_audio_segment(self, seconds):
        frames = []
        num_chunks = int(self.RATE / self.CHUNK * seconds)
        for _ in range(num_chunks):
            data = self.stream.read(self.CHUNK, exception_on_overflow=False)
            frames.append(data)
        
        audio_data = np.frombuffer(b''.join(frames), dtype=np.int16).astype(np.float32) / 32768.0

        # 노이즈 제거
        noise_duration = 0.2
        noise_samples = int(self.RATE * noise_duration)
        if len(audio_data) > noise_samples:
            noise_clip = audio_data[:noise_samples]
            audio_data = nr.reduce_noise(y=audio_data, sr=self.RATE, y_noise=noise_clip)
        
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            audio_data = audio_data / max_val
        
        return audio_data

    def transcribe_audio(self, audio_data):
        segments, _ = self.model.transcribe(audio_data, language="ko")
        return " ".join([segment.text for segment in segments]).strip()
    
    def publish_text(self, text):
        msg = String()
        msg.data = text
        self.publisher_.publish(msg)
        self.get_logger().info(f"퍼블리시된 텍스트: {text}")
    
    def run(self):
        activated = False
        while rclpy.ok():
            if not activated:
                audio_data = self.record_audio_segment(self.RECORD_SECONDS)
                recognized_text = self.transcribe_audio(audio_data)
                if "안녕" in recognized_text:
                    activated = True
                    self.get_logger().info("✅ 시스템 활성화됨. 이제 200초간 명령어를 수신합니다.")
                    self.publish_text("시스템 활성화됨")
                else:
                    self.get_logger().info("초기 활성화를 위해 '안녕'을 말해주세요.")
            else:
                start_time = time.time()
                while time.time() - start_time < 200:
                    audio_data = self.record_audio_segment(self.RECORD_SECONDS)
                    recognized_text = self.transcribe_audio(audio_data)
                    if recognized_text:
                        self.get_logger().info(f"명령어 인식: {recognized_text}")
                        self.publish_text(recognized_text)
                activated = False
                self.get_logger().info("⌛ 명령어 수신 시간이 종료되었습니다. 다시 '안녕'으로 활성화하세요.")
    
    def stop(self):
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()

def main(args=None):
    rclpy.init(args=args)
    node = FasterWhisperSTTNode()
    try:
        node.run()
    except KeyboardInterrupt:
        node.get_logger().info("🛑 음성 인식 종료!")
    finally:
        node.stop()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
