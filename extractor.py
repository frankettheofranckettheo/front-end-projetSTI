import requests
import json
import os
import hashlib
from datetime import datetime

class FultangExtractor:
    def __init__(self):
        # Configuration basée sur ta commande curl
        self.base_url = "http://fultang.ddns.net:8009/api/v1/medical/dataset/recent/"
        self.token = "OgDfge8Vumt1FyX8MXmgVHLuAX4Ver3FASycEYKXGUsLLhRfYG5zOdI8kYeXjTiW"
        self.headers = {
            "Authorization": f"Token {self.token}",
            "Content-Type": "application/json"
        }
        # Dossier pour stocker les preuves d'intégrité
        self.storage_dir = "raw_data_archive"
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)

    def fetch_data_from_api(self):
        """
        1. Se connecte à l'API Fultang.
        2. Récupère le JSON global.
        """
        print(f"[*] Tentative de connexion à {self.base_url}...")
        
        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"[+] Connexion réussie ! Données reçues.")
                print(f"    - Taille du contenu : {len(response.content)} octets")
                return data
            else:
                print(f"[-] Erreur API : {response.status_code}")
                print(f"[-] Détails : {response.text}")
                return None
                
        except requests.exceptions.ConnectionError:
            print("[-] Erreur : Impossible de se connecter au serveur (Vérifie ta connexion ou le VPN).")
            return None
        except Exception as e:
            print(f"[-] Erreur inattendue : {e}")
            return None

    def generate_integrity_proof(self, data):
        """
        Génère une signature SHA-256 unique pour ce lot de données.
        C'est l'exigence 'Preuve d'intégrité' du document.
        """
        # On convertit le dict en string triée pour garantir que le hash soit toujours le même pour les mêmes données
        json_bytes = json.dumps(data, sort_keys=True).encode('utf-8')
        signature = hashlib.sha256(json_bytes).hexdigest()
        return signature

    def save_raw_data(self, data):
        """
        Sauvegarde les données brutes sur le disque avec leur signature.
        """
        if not data:
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        signature = self.generate_integrity_proof(data)
        
        filename = f"fultang_extract_{timestamp}.json"
        filepath = os.path.join(self.storage_dir, filename)

        # On ajoute des métadonnées pour la traçabilité
        final_object = {
            "meta": {
                "extracted_at": timestamp,
                "integrity_hash_sha256": signature,
                "source": self.base_url
            },
            "payload": data # Les données réelles de l'API
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(final_object, f, indent=4, ensure_ascii=False)

        print(f"[+] Données sauvegardées dans : {filepath}")
        print(f"[+] Signature d'intégrité : {signature}")
        return filepath

# --- Zone de Test ---
if __name__ == "__main__":
    extractor = FultangExtractor()
    
    # 1. Extraction
    data = extractor.fetch_data_from_api()
    
    # 2. Sauvegarde sécurisée (Preuve)
    if data:
        extractor.save_raw_data(data)
        
        # Petit aperçu pour vérifier ce qu'on a reçu
        nb_staff = len(data.get("medical_staff", []))
        nb_exams = len(data.get("exams", []))
        nb_products = len(data.get("polyclinic_products", []))
        
        print("\n--- Résumé du contenu extrait ---")
        print(f"Personnel médical : {nb_staff}")
        print(f"Types d'examens   : {nb_exams}")
        print(f"Produits en stock : {nb_products}")
        print("Patients (vide?)  : ", len(data.get("patients", [])))