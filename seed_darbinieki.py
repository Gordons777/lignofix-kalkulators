"""
seed_darbinieki.py — palaid vienu reizi, lai pievienotu darbiniekus DB
Komanda: python seed_darbinieki.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.schema import init_db
from db.grafiks_db import add_worker

def seed():
    init_db()
    print("DB inicializēta.")

    pamata = [
        "Mārcis", "Aivars", "Jānis", "Vitālijs",
        "Jelena", "Tatjana",
    ]
    arpakalpojums = [
        "Ivan", "Vladimir", "Dmitri", "Grigorii", "Natalia",
    ]
    autoiekravaji = [
        "Mihails", "Andrejs",
    ]

    for v in pamata:
        ok = add_worker(v, "darbinieks")
        print(f"  {'✓' if ok else '—'} {v} (darbinieks)")

    for v in arpakalpojums:
        ok = add_worker(v, "darbinieks")
        print(f"  {'✓' if ok else '—'} {v} (darbinieks/ārpakalpojums)")

    for v in autoiekravaji:
        ok = add_worker(v, "autoiekravejs")
        print(f"  {'✓' if ok else '—'} {v} (autoiekrāvējs)")

    print("\nGatavs! Visi darbinieki pievienoti.")

if __name__ == "__main__":
    seed()
