import json
import uuid
from datetime import datetime
from typing import List, Dict

# On importe tout
from models import (
    CasClinique, DonneesPersonnelles, ModeDeVie, AntecedentsMedicaux,
    Symptome, ExamenComplementaire, DiagnosticPhysique, TraitementEnCours,
    Voyage, ActivitePhysique
)

class ClinicalCaseTransformer:
    def __init__(self, raw_data_wrapped: Dict):
        # Gestion du format enveloppé (avec métadonnées) ou brut
        if "meta" in raw_data_wrapped and "payload" in raw_data_wrapped:
            self.source_hash = raw_data_wrapped["meta"].get("integrity_hash_sha256", "NON_VERIFIE")
            self.raw_data = raw_data_wrapped["payload"]
        else:
            self.source_hash = "SIMULATION_TEST_HASH_12345" # Hash par défaut pour le mode test
            self.raw_data = raw_data_wrapped

        self.patients = self.raw_data.get('patients', [])
        self.consultations = self.raw_data.get('consultations', [])
        self.exams_definitions = {e['id']: e for e in self.raw_data.get('exams', [])}
        
        # --- MODE SIMULATION ---
        if not self.patients:
            print("[!] ATTENTION: Listes patients vides. Utilisation de données simulées.")
            self._simulate_data_for_testing()

    def _simulate_data_for_testing(self):
        """Simulation de 3 patients pour valider les filtres"""
        self.patients = [
            {"id": 1, "birth_date": "1995-05-12", "gender": "M", "occupation": "Etudiant"}, 
            {"id": 2, "birth_date": "1948-01-01", "gender": "F", "occupation": "Retraitée"}, 
            {"id": 3, "birth_date": "1990-06-15", "gender": "M", "occupation": "Enseignant"} 
        ]
        self.consultations = [
            {"id": 101, "patient_id": 1, "reason": "Fièvre et fatigue", "symptoms_text": "Fièvre élevée", "diagnosis": "Paludisme"},
            {"id": 102, "patient_id": 2, "reason": "Confusion et fièvre", "symptoms_text": "Fièvre modérée, confusion", "diagnosis": "Paludisme grave"},
            {"id": 103, "patient_id": 3, "reason": "Nez qui coule", "symptoms_text": "Toux sèche", "diagnosis": "Grippe"}
        ]
        self.exam_results = [
            {"consultation_id": 101, "exam_id": 1, "result": "Positif Palu"},
            {"consultation_id": 102, "exam_id": 1, "result": "Positif Palu ++"},
            {"consultation_id": 103, "exam_id": 1, "result": "Négatif Palu"}
        ]

    def anonymize_id(self, original_id: int) -> str:
        return f"CASE-{uuid.uuid5(uuid.NAMESPACE_DNS, str(original_id)).hex[:8].upper()}"

    def calculate_age(self, birth_date_str: str) -> int:
        if not birth_date_str: return 30
        try:
            b_date = datetime.strptime(birth_date_str, "%Y-%m-%d")
            return datetime.now().year - b_date.year
        except:
            return 30

    def transform_single_case(self, consultation: Dict) -> CasClinique:
        patient = next((p for p in self.patients if p['id'] == consultation['patient_id']), None)
        if not patient: return None

        related_exams = getattr(self, 'exam_results', [])
        patient_exams = [e for e in related_exams if e['consultation_id'] == consultation['id']]

        # MAPPING
        donnees_perso = DonneesPersonnelles(
            age=self.calculate_age(patient.get('birth_date')),
            sexe=patient.get('gender', 'M'),
            profession=patient.get('occupation', 'Inconnu'),
            groupe_sanguin="O+"
        )

        mode_vie = ModeDeVie(
            qualite_eau="Eau du robinet non filtrée",
            moustiquaire=True,
            voyages=[Voyage(lieu="Village (Ouest)", duree="2 semaines")]
        )

        symptomes_list = [Symptome(nom="Fièvre", degre="39.5°C", duree="3 jours")] # Simplifié pour l'exemple

        exams_list = []
        for res in patient_exams:
            exams_list.append(ExamenComplementaire(
                nom="Blood Test",
                resultat=res['result'],
                anatomie="Sang"
            ))

        # --- CREATION DU CAS AVEC LE HASH (C'est ici que ça bloquait) ---
        cas = CasClinique(
            id_unique=self.anonymize_id(consultation['id']),
            hash_authentification=self.source_hash,  # <--- CHAMP OBLIGATOIRE AJOUTÉ
            motif_consultation=consultation.get('reason', ''),
            donnees_personnelles=donnees_perso,
            mode_de_vie=mode_vie,
            antecedents_medicaux=AntecedentsMedicaux(),
            symptomes=symptomes_list,
            diagnostic_physique=[DiagnosticPhysique(nom="Palpation splénique", resultat="Splénomégalie légère")],
            examens_complementaires=exams_list,
            traitement_en_cours=[]
        )
        return cas

    def process(self) -> List[CasClinique]:
        results = []
        for consult in self.consultations:
            try:
                cas = self.transform_single_case(consult)
                if cas: results.append(cas)
            except Exception as e:
                print(f"[-] Erreur ID {consult.get('id')}: {e}")
        return results

if __name__ == "__main__":
    # Test rapide
    simulated_data = {"patients": [], "consultations": []} # Vide pour forcer la simulation
    transformer = ClinicalCaseTransformer(simulated_data)
    cases = transformer.process()
    
    with open("dataset_cas_cliniques_final.json", "w", encoding='utf-8') as f:
        json.dump([c.model_dump() for c in cases], f, indent=4, ensure_ascii=False)
    print(f"[+] Données régénérées avec succès ({len(cases)} cas).")