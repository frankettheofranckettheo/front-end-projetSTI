import json
import uuid
import random
from datetime import datetime
from typing import List, Dict

# On importe nos modèles définis à l'étape précédente
from models import (
    CasClinique, DonneesPersonnelles, ModeDeVie, AntecedentsMedicaux,
    Symptome, ExamenComplementaire, DiagnosticPhysique, TraitementEnCours,
    Maladie, TraitementMaladie, Voyage, ActivitePhysique
)

class ClinicalCaseTransformer:
    def __init__(self, raw_data: Dict):
        self.raw_data = raw_data
        self.patients = raw_data.get('patients', [])
        self.consultations = raw_data.get('consultations', [])
        self.exams_definitions = {e['id']: e for e in raw_data.get('exams', [])}
        
        # --- MODE SIMULATION (Si l'API est vide) ---
        if not self.patients:
            print("[!] ATTENTION: Listes patients vides. Utilisation de données simulées pour test.")
            self._simulate_data_for_testing()

    def _simulate_data_for_testing(self):
        """
        Simulation améliorée : Génère 3 patients pour tester le filtrage.
        """
        # 1. Patient Jeune (Palu)
        # 2. Patient Agé (Palu) -> Cible du filtre "Palu + Agé"
        # 3. Patient Autre (Grippe)
        
        self.patients = [
            {"id": 1, "birth_date": "1995-05-12", "gender": "M", "occupation": "Etudiant"}, # 30 ans
            {"id": 2, "birth_date": "1948-01-01", "gender": "F", "occupation": "Retraitée"}, # 77 ans (Vieux)
            {"id": 3, "birth_date": "1990-06-15", "gender": "M", "occupation": "Enseignant"} # Autre
        ]
        
        self.consultations = [
            # Cas 1 : Paludisme
            {"id": 101, "patient_id": 1, "reason": "Fièvre et fatigue", 
             "symptoms_text": "Fièvre élevée, frissons", "diagnosis": "Paludisme"},
            # Cas 2 : Paludisme sur personne âgée
            {"id": 102, "patient_id": 2, "reason": "Confusion et fièvre", 
             "symptoms_text": "Fièvre modérée, fatigue extrême, confusion", "diagnosis": "Paludisme grave"},
            # Cas 3 : Grippe
            {"id": 103, "patient_id": 3, "reason": "Nez qui coule", 
             "symptoms_text": "Toux sèche, rhinite", "diagnosis": "Grippe"}
        ]
        
        # Résultats d'examens simulés
        self.exam_results = [
            {"consultation_id": 101, "exam_id": 1, "result": "Positif Palu"},
            {"consultation_id": 102, "exam_id": 1, "result": "Positif Palu ++"},
            {"consultation_id": 103, "exam_id": 1, "result": "Négatif Palu"}
        ]

    def anonymize_id(self, original_id: int) -> str:
        """Crée un ID unique cryptique (ex: 'CASE-A1B2...') pour RGPD"""
        return f"CASE-{uuid.uuid5(uuid.NAMESPACE_DNS, str(original_id)).hex[:8].upper()}"

    def calculate_age(self, birth_date_str: str) -> int:
        # Calcul basique de l'âge
        if not birth_date_str: return 30 # Valeur par défaut
        b_date = datetime.strptime(birth_date_str, "%Y-%m-%d")
        return datetime.now().year - b_date.year

    def transform_single_case(self, consultation: Dict) -> CasClinique:
        """
        C'est ici que la magie opère : Mapping Données Brutes -> Modèle Figure 1
        """
        # 1. Retrouver le patient lié
        patient = next((p for p in self.patients if p['id'] == consultation['patient_id']), None)
        if not patient:
            return None

        # 2. Retrouver les examens liés (simulation simple ici car pas de table exam_results dans le JSON initial)
        # Dans le script réel, on filtrerait self.exam_results
        related_exams = getattr(self, 'exam_results', [])
        patient_exams = [e for e in related_exams if e['consultation_id'] == consultation['id']]

        # --- CONSTRUCTION DES BLOCS DE LA FIGURE 1 ---

        # Bloc: Données Personnelles
        donnees_perso = DonneesPersonnelles(
            age=self.calculate_age(patient.get('birth_date')),
            sexe=patient.get('gender', 'M'),
            profession=patient.get('occupation', 'Inconnu'),
            groupe_sanguin="O+" # Donnée simulée si absente
        )

        # Bloc: Mode de Vie (Exemple riche pour le contexte)
        mode_vie = ModeDeVie(
            qualite_eau="Eau du robinet non filtrée",
            moustiquaire=True, # Important pour Palu
            voyages=[Voyage(lieu="Village (Ouest)", duree="2 semaines")]
        )

        # Bloc: Symptômes (Parsing simple du texte)
        # Dans une vraie app, on utiliserait du NLP pour extraire ça proprement
        symptomes_list = []
        desc = consultation.get('symptoms_text', '')
        if 'Fièvre' in desc:
            symptomes_list.append(Symptome(nom="Fièvre", degre="39.5°C", duree="3 jours"))
        if 'courbatures' in desc:
            symptomes_list.append(Symptome(nom="Myalgies", localisation="Diffus"))

        # Bloc: Examens Complémentaires
        exams_list = []
        for res in patient_exams:
            # On récupère le nom de l'examen depuis la définition (table 'exams')
            def_exam = self.exams_definitions.get(res['exam_id'])
            exam_name = def_exam['examName'] if def_exam else "Examen Inconnu"
            
            exams_list.append(ExamenComplementaire(
                nom=exam_name,
                resultat=res['result'],
                anatomie="Sang" # Déduit
            ))

        # --- ASSEMBLAGE FINAL ---
        cas = CasClinique(
            id_unique=self.anonymize_id(consultation['id']),
            motif_consultation=consultation.get('reason', ''),
            donnees_personnelles=donnees_perso,
            mode_de_vie=mode_vie,
            antecedents_medicaux=AntecedentsMedicaux(), # Vide pour l'exemple
            symptomes=symptomes_list,
            diagnostic_physique=[DiagnosticPhysique(nom="Palpation splénique", resultat="Splénomégalie légère")],
            examens_complementaires=exams_list,
            traitement_en_cours=[]
        )
        
        return cas

    def process(self) -> List[CasClinique]:
        results = []
        print(f"[*] Début de la transformation de {len(self.consultations)} consultations...")
        
        for consult in self.consultations:
            try:
                cas = self.transform_single_case(consult)
                if cas:
                    results.append(cas)
            except Exception as e:
                print(f"[-] Erreur sur la consultation {consult.get('id')}: {e}")
        
        return results

# --- Exécution ---
if __name__ == "__main__":
    # 1. On charge les données brutes extraites à l'étape précédente
    # (Assure-toi d'avoir un fichier json généré par extractor.py, ou utilise le mode test)
    
    # Pour le test immédiat, on relance l'extracteur vite fait
    from extractor import FultangExtractor
    print("--- 1. Extraction ---")
    extractor = FultangExtractor()
    raw_json = extractor.fetch_data_from_api()
    
    if raw_json:
        print("\n--- 2. Transformation ---")
        transformer = ClinicalCaseTransformer(raw_json)
        cas_cliniques = transformer.process()
        
        print(f"\n[+] Succès ! {len(cas_cliniques)} cas cliniques générés au format Figure 1.")
        
        # 3. Export pour le LLM (Format final)
        output_filename = "dataset_cas_cliniques_final.json"
        
        # On convertit les objets Pydantic en dict pour le JSON
        final_data = [cas.model_dump() for cas in cas_cliniques]
        
        with open(output_filename, "w", encoding='utf-8') as f:
            json.dump(final_data, f, indent=4, ensure_ascii=False)
            
        print(f"[+] Fichier prêt pour le LLM : {output_filename}")
        
        # Aperçu du premier cas
        print("\n--- Aperçu du Cas 1 (Format JSON) ---")
        print(json.dumps(final_data[0], indent=2, ensure_ascii=False))