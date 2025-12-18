from typing import List, Optional
from pydantic import BaseModel

# --- NIVEAU 4 : LES FEUILLES (DÉTAILS LES PLUS FINS) ---

class TraitementMaladie(BaseModel):
    duree: Optional[str] = None
    posologie: Optional[str] = None

# --- NIVEAU 3 : LES SOUS-CATÉGORIES ---

class Allergie(BaseModel):
    manifestation: Optional[str] = None
    declencheur: Optional[str] = None

class Maladie(BaseModel):
    nom: str
    date_debut_fin: Optional[str] = None # Correspond à "Date debut/fin"
    observation: Optional[str] = None
    traitement: Optional[TraitementMaladie] = None # Le lien vers la bulle bleue "Traitement"

class Chirurgie(BaseModel):
    nom: str
    date: Optional[str] = None

class AntecedentsObstetricaux(BaseModel):
    nombre_grossesse: Optional[int] = None
    date: Optional[str] = None

class Voyage(BaseModel):
    lieu: Optional[str] = None
    frequence: Optional[str] = None
    duree: Optional[str] = None

class ActivitePhysique(BaseModel):
    nom: Optional[str] = None
    frequence: Optional[str] = None

class Addiction(BaseModel):
    nom: str
    frequence: Optional[str] = None
    duree: Optional[str] = None

# --- NIVEAU 2 : LES BRANCHES PRINCIPALES ---

class DonneesPersonnelles(BaseModel):
    age: Optional[int] = None
    sexe: str
    etat_civil: Optional[str] = None
    profession: Optional[str] = None
    nombre_enfant: Optional[int] = None
    groupe_sanguin: Optional[str] = None

class ModeDeVie(BaseModel):
    qualite_eau: Optional[str] = None
    moustiquaire: Optional[bool] = None # Ou str selon la donnée
    animal_de_compagnie: Optional[str] = None
    # Relations vers les bulles filles
    voyages: List[Voyage] = [] 
    activites_physiques: List[ActivitePhysique] = []
    addictions: List[Addiction] = []

class AntecedentsMedicaux(BaseModel):
    antecedents_familiaux: List[str] = [] # La bulle n'a pas de fils, donc liste de strings
    allergies: List[Allergie] = []
    maladies: List[Maladie] = []
    chirurgies: List[Chirurgie] = []
    antecedents_obstetricaux: Optional[AntecedentsObstetricaux] = None

class Symptome(BaseModel):
    # Les 8 attributs exacts de l'image
    nom: str
    localisation: Optional[str] = None
    date_debut: Optional[str] = None
    frequence: Optional[str] = None
    duree: Optional[str] = None
    evolution: Optional[str] = None
    activite_declenchante: Optional[str] = None
    degre: Optional[str] = None # "degré" sur l'image

class DiagnosticPhysique(BaseModel):
    nom: str
    resultat: Optional[str] = None

class ExamenComplementaire(BaseModel):
    nom: str
    resultat: Optional[str] = None
    anatomie: Optional[str] = None # Spécifique à ton schéma

class TraitementEnCours(BaseModel):
    nom: str
    mode_de_transmission: Optional[str] = None
    date_debut: Optional[str] = None
    observation: Optional[str] = None
    efficacite: Optional[str] = None

# --- NIVEAU 1 : RACINE (CENTRE DE L'IMAGE) ---

class CasClinique(BaseModel):
    """
    Représentation exacte de la Figure 1.
    """
    id_unique: str # Pour gestion interne (Preuve d'intégrité)
    hash_authentification: str  # <--- AJOUT : La signature SHA-256 du fichier source
    
    # Les 7/8 branches connectées au cercle vert "Cas clinique"
    donnees_personnelles: DonneesPersonnelles
    motif_consultation: str # Bulle simple
    mode_de_vie: ModeDeVie
    antecedents_medicaux: AntecedentsMedicaux
    symptomes: List[Symptome]
    diagnostic_physique: List[DiagnosticPhysique] # Liste car un patient peut avoir plusieurs signes
    examens_complementaires: List[ExamenComplementaire]
    traitement_en_cours: List[TraitementEnCours]