import firebase_admin
from firebase_admin import credentials, firestore
from config import FIREBASE_CRED_PATH

# Firebase'i başlat
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CRED_PATH)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# --- KULLANICI İŞLEMLERİ ---
def get_user(telegram_id):
    doc = db.collection('users').document(str(telegram_id)).get()
    return doc.to_dict() if doc.exists else None

def create_user(telegram_id, username):
    db.collection('users').document(str(telegram_id)).set({
        'telegram_id': telegram_id,
        'username': username or '',
        'created_at': firestore.SERVER_TIMESTAMP,
        'last_active': firestore.SERVER_TIMESTAMP
    })

def update_last_active(telegram_id):
    db.collection('users').document(str(telegram_id)).update({
        'last_active': firestore.SERVER_TIMESTAMP
    })

# --- ANTRENMAN İŞLEMLERİ ---
def log_workout(telegram_id, exercise_name, sets, reps, weight_kg, video_file_id=None, notes=None):
    workout_data = {
        'user_id': str(telegram_id),
        'exercise_name': exercise_name,
        'sets': sets,
        'reps': reps,
        'weight_kg': weight_kg,
        'video_file_id': video_file_id,
        'notes': notes,
        'created_at': firestore.SERVER_TIMESTAMP
    }
    doc_ref = db.collection('workouts').document()
    doc_ref.set(workout_data)
    return doc_ref.id

# --- VİDEO İŞLEMLERİ ---
def save_video_metadata(telegram_id, file_id, exercise_name, notes=None):
    video_data = {
        'user_id': str(telegram_id),
        'file_id': file_id,
        'exercise_name': exercise_name,
        'notes': notes,
        'created_at': firestore.SERVER_TIMESTAMP
    }
    doc_ref = db.collection('videos').document()
    doc_ref.set(video_data)
    return doc_ref.id

# --- VÜCUT ÖLÇÜMLERİ ---
def log_measurement(telegram_id, measurements):
    # measurements: dict, ör: {'weight': 75.5, 'waist': 85, 'chest': 100}
    measurement_data = {
        'user_id': str(telegram_id),
        'measurements': measurements,
        'created_at': firestore.SERVER_TIMESTAMP
    }
    doc_ref = db.collection('measurements').document()
    doc_ref.set(measurement_data)
    return doc_ref.id

# --- VERİLERİ ÇEKMEK ---
def get_user_workouts(telegram_id, exercise_name=None):
    ref = db.collection('workouts').where('user_id', '==', str(telegram_id))
    if exercise_name:
        ref = ref.where('exercise_name', '==', exercise_name)
    docs = ref.order_by('created_at').stream()
    return [doc.to_dict() | {'id': doc.id} for doc in docs]

def get_user_measurements(telegram_id):
    docs = db.collection('measurements') \
             .where('user_id', '==', str(telegram_id)) \
             .order_by('created_at') \
             .stream()
    return [doc.to_dict() | {'id': doc.id} for doc in docs]

def get_user_videos(telegram_id, exercise_name=None):
    ref = db.collection('videos').where('user_id', '==', str(telegram_id))
    if exercise_name:
        ref = ref.where('exercise_name', '==', exercise_name)
    docs = ref.order_by('created_at').stream()
    result = []
    for doc in docs:
        data = doc.to_dict()
        # Firestore timestamp → datetime
        if 'created_at' in data and hasattr(data['created_at'], 'to_datetime'):
            data['created_at'] = data['created_at'].to_datetime()
        # ID'yi ekle
        data['id'] = doc.id
        result.append(data)
    return result  # 👉 HER ELEMAN BİR DICT!

__all__ = ['get_user', 'create_user', 'update_last_active', 'log_workout', 'save_video_metadata', 'log_measurement', 'get_user_workouts', 'get_user_measurements', 'get_user_videos', 'db']