import matplotlib.pyplot as plt
import os
from datetime import datetime

def plot_weight_progress(workouts, exercise_name):
    """
    Belirli bir hareket için ağırlık gelişimi grafiği çizer.
    Girdi: workouts (list of dicts), exercise_name (str)
    Çıktı: PNG dosya yolu (str) veya None
    """
    if not workouts:
        return None

    # Tarihleri string'e çevir (Firestore'tan gelen datetime için)
    dates = []
    weights = []

    for w in workouts:
        created_at = w.get('created_at')
        if hasattr(created_at, 'strftime'):
            date_str = created_at.strftime('%d/%m')
        else:
            date_str = "Bilinmiyor"
        dates.append(date_str)
        weights.append(w.get('weight_kg', 0))

    plt.figure(figsize=(10, 5))
    plt.plot(dates, weights, marker='o', linestyle='-', color='#FF6B6B', linewidth=2, markersize=6)
    plt.title(f'{exercise_name.title()} - Ağırlık Gelişimi', fontsize=14, fontweight='bold')
    plt.xlabel('Tarih', fontsize=12)
    plt.ylabel('Ağırlık (kg)', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()

    filename = f"weight_progress_{exercise_name.replace(' ', '_')}.png"
    plt.savefig(filename, dpi=150)
    plt.close()
    return filename

def plot_body_measurements(measurements, metric_key, metric_label):
    """
    Vücut ölçümleri için grafik çizer (kilo, bel, göğüs vs.)
    Girdi: measurements (list), metric_key (str: 'weight_kg'), metric_label (str: 'Kilo (kg)')
    Çıktı: PNG dosya yolu (str) veya None
    """
    if not measurements:
        return None

    dates = []
    values = []

    for m in measurements:
        created_at = m.get('created_at')
        if hasattr(created_at, 'strftime'):
            date_str = created_at.strftime('%d/%m')
        else:
            date_str = "Bilinmiyor"
        dates.append(date_str)
        values.append(m['measurements'].get(metric_key, 0))

    plt.figure(figsize=(10, 5))
    plt.plot(dates, values, marker='s', linestyle='--', color='#4ECDC4', linewidth=2, markersize=6)
    plt.title(f'{metric_label} Gelişimi', fontsize=14, fontweight='bold')
    plt.xlabel('Tarih', fontsize=12)
    plt.ylabel(metric_label, fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()

    filename = f"body_{metric_key}.png"
    plt.savefig(filename, dpi=150)
    plt.close()
    return filename