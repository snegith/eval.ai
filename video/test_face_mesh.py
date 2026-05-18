import cv2
import mediapipe as mp

VIDEO_PATH = "data/sessions/session_763c54f7/video.mp4"

cap = cv2.VideoCapture(VIDEO_PATH)
ret, frame = cap.read()
cap.release()

print("Frame shape:", frame.shape)

mp_face = mp.solutions.face_mesh
face_mesh = mp_face.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True
)

# Try raw frame
rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
res = face_mesh.process(rgb)

print("Raw frame face detected:", bool(res.multi_face_landmarks))

# Try rotated frames
for name, rotated in {
    "90_cw": cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE),
    "90_ccw": cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE),
    "180": cv2.rotate(frame, cv2.ROTATE_180),
}.items():
    rgb_r = cv2.cvtColor(rotated, cv2.COLOR_BGR2RGB)
    res_r = face_mesh.process(rgb_r)
    print(f"{name} face detected:", bool(res_r.multi_face_landmarks))
