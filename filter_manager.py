import json
from typing import List
from models import CasClinique

class ClinicalCaseFilter:
    def __init__(self, json_file_path: str):
        self.cases: List[CasClinique] = []
        self._load_data(json_file_path)

    def _load_data(self, path: str):
        """Charge le JSON et le convertit en objets Python manipulables"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # On convertit chaque entrée JSON en objet CasClinique (validation Pydantic)
                self.cases = [CasClinique(**item) for item in data]
            print(f"[*] Chargement réussi : {len(self.cases)} cas cliniques disponibles.")
        except FileNotFoundError:
            print(f"[-] Erreur : Le fichier {path} n'existe pas.")

    def filter_by_keyword(self, keyword: str) -> List[CasClinique]:
        keyword = keyword.lower()
        results = []
        for case in self.cases:
            # 1. Recherche dans le motif (ex: "Susplection Palu")
            if keyword in case.motif_consultation.lower():
                results.append(case)
                continue
            
            # 2. Recherche dans les examens (PLUS INTELLIGENT)
            for exam in case.examens_complementaires:
                text = exam.resultat.lower()
                # On veut que le mot clé soit là, MAIS PAS précédé de "négatif"
                if keyword in text and "négatif" not in text: 
                    results.append(case)
                    break
        return results

    def filter_by_age_group(self, min_age: int = 0, max_age: int = 120, subset: List[CasClinique] = None) -> List[CasClinique]:
        """
        Filtre par tranche d'âge.
        Peut s'appliquer sur la liste complète ou sur un sous-ensemble déjà filtré.
        """
        source = subset if subset is not None else self.cases
        results = []
        for case in source:
            # On gère le cas où l'âge est None (on l'exclut par sécurité)
            age = case.donnees_personnelles.age
            if age is not None and min_age <= age <= max_age:
                results.append(case)
        return results

    def export_selection(self, cases: List[CasClinique], filename: str):
        """Exporte les résultats filtrés"""
        data = [case.model_dump() for case in cases]
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"[+] Exporté {len(cases)} cas vers {filename}")

# --- SCÉNARIO DU DOCUMENT ---
if __name__ == "__main__":
    # 1. Initialisation
    manager = ClinicalCaseFilter("dataset_cas_cliniques_final.json")

    if manager.cases:
        print("\n--- Scénario 1 : Tous les malades du Paludisme ---")
        # On cherche les cas qui mentionnent "Palu" ou "Fièvre" (selon ta simulation)
        # Dans la simulation améliorée, le motif contient "Fièvre" ou "Palu"
        # Mais attention, la grippe a aussi de la fièvre. 
        # Filtrons plutôt sur les résultats d'examen contenant "Palu"
        malaria_cases = manager.filter_by_keyword("Palu")
        print(f"-> Résultat : {len(malaria_cases)} cas trouvés.")
        manager.export_selection(malaria_cases, "export_paludisme_tous.json")

        print("\n--- Scénario 2 : Paludisme chez les personnes âgées (> 60 ans) ---")
        # On applique le filtre d'âge SUR le résultat précédent (malaria_cases)
        # C'est le "Chainage" de filtres
        elderly_malaria = manager.filter_by_age_group(min_age=60, max_age=120, subset=malaria_cases)
        print(f"-> Résultat : {len(elderly_malaria)} cas critique(s) trouvé(s).")
        
        if elderly_malaria:
            patient = elderly_malaria[0].donnees_personnelles
            print(f"   Détails : Patient de {patient.age} ans, Profession: {patient.profession}")
            manager.export_selection(elderly_malaria, "export_paludisme_personnes_agees.json")