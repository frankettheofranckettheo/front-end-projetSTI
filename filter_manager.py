import json
from typing import List, Optional
from models import CasClinique

class ClinicalCaseFilter:
    def __init__(self, json_file_path: str):
        self.cases: List[CasClinique] = []
        self._load_data(json_file_path)

    def _load_data(self, path: str):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.cases = [CasClinique(**item) for item in data]
            print(f"[*] Chargement réussi : {len(self.cases)} cas cliniques disponibles.")
        except FileNotFoundError:
            print(f"[-] Erreur : Le fichier {path} n'existe pas.")
            self.cases = []

    # --- FILTRE 1 : MOT-CLÉ (Déjà existant, amélioré) ---
    def filter_by_keyword(self, keyword: str, subset: List[CasClinique] = None) -> List[CasClinique]:
        source = subset if subset is not None else self.cases
        keyword = keyword.lower()
        results = []
        for case in source:
            # Cherche dans le motif
            if keyword in case.motif_consultation.lower():
                results.append(case)
                continue
            # Cherche dans les examens (en excluant les négatifs)
            for exam in case.examens_complementaires:
                text = exam.resultat.lower() if exam.resultat else ""
                if keyword in text and "négatif" not in text:
                    results.append(case)
                    break
        return results

    # --- FILTRE 2 : TRANCHE D'ÂGE (Déjà existant) ---
    def filter_by_age_group(self, min_age: int = 0, max_age: int = 120, subset: List[CasClinique] = None) -> List[CasClinique]:
        source = subset if subset is not None else self.cases
        results = []
        for case in source:
            age = case.donnees_personnelles.age
            if age is not None and min_age <= age <= max_age:
                results.append(case)
        return results

    # --- FILTRE 3 : SEXE (Nouveau) ---
    def filter_by_gender(self, gender: str, subset: List[CasClinique] = None) -> List[CasClinique]:
        """Filtre par sexe : 'M' ou 'F'"""
        source = subset if subset is not None else self.cases
        target = gender.upper()
        return [c for c in source if c.donnees_personnelles.sexe == target]

    # --- FILTRE 4 : PROFESSION (Nouveau) ---
    def filter_by_profession(self, job_keyword: str, subset: List[CasClinique] = None) -> List[CasClinique]:
        """Ex: 'Agriculteur', 'Etudiant'"""
        source = subset if subset is not None else self.cases
        keyword = job_keyword.lower()
        results = []
        for c in source:
            prof = c.donnees_personnelles.profession
            if prof and keyword in prof.lower():
                results.append(c)
        return results

    # --- FILTRE 5 : SYMPTÔME SPÉCIFIQUE (Nouveau) ---
    def filter_by_symptom_name(self, symptom_name: str, subset: List[CasClinique] = None) -> List[CasClinique]:
        """Cherche si le patient a déclaré un symptôme précis (ex: 'Toux')"""
        source = subset if subset is not None else self.cases
        keyword = symptom_name.lower()
        results = []
        for c in source:
            # On vérifie si l'un des symptômes correspond
            for s in c.symptomes:
                if keyword in s.nom.lower():
                    results.append(c)
                    break
        return results

    # --- MÉTHODES POUR RÉCUPÉRER LES OPTIONS DE FILTRE ---
    def get_unique_symptoms(self) -> List[str]:
        """Retourne une liste triée de tous les noms de symptômes uniques."""
        symptoms = set()
        for case in self.cases:
            for symptom in case.symptomes:
                if symptom.nom:
                    symptoms.add(symptom.nom.strip())
        return sorted(list(symptoms))

    def get_unique_professions(self) -> List[str]:
        """Retourne une liste triée de toutes les professions uniques."""
        professions = set()
        for case in self.cases:
            if case.donnees_personnelles.profession:
                professions.add(case.donnees_personnelles.profession.strip())
        return sorted(list(professions))

    def get_unique_genders(self) -> List[str]:
        """Retourne une liste triée des sexes uniques."""
        genders = set()
        for case in self.cases:
            if case.donnees_personnelles.sexe:
                genders.add(case.donnees_personnelles.sexe.strip())
        return sorted(list(genders))

    def export_selection(self, cases: List[CasClinique], filename: str):
        data = [case.model_dump() for case in cases]
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"[+] Exporté {len(cases)} cas vers {filename}")

# --- ZONE DE TEST LOCALE ---
if __name__ == "__main__":
    manager = ClinicalCaseFilter("dataset_cas_cliniques_final.json")
    
    if manager.cases:
        print("\n--- Test des Nouveaux Filtres ---")
        
        # Exemple : Hommes qui sont Agriculteurs
        hommes = manager.filter_by_gender("M")
        agriculteurs_hommes = manager.filter_by_profession("Agriculteur", subset=hommes)
        print(f"Hommes Agriculteurs trouvés : {len(agriculteurs_hommes)}")

        # Exemple : Patients avec de la Fièvre
        fievreux = manager.filter_by_symptom_name("Fièvre")
        print(f"Patients avec symptôme 'Fièvre' : {len(fievreux)}")