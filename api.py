from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import json

# IMPORTATIONS COMPLÈTES (Pour éviter les erreurs "NameError")
from models import (
    CasClinique, DonneesPersonnelles, ModeDeVie, 
    Symptome, DiagnosticPhysique, ExamenComplementaire
)
from filter_manager import ClinicalCaseFilter

app = FastAPI(
    title="API Générateur Cas Cliniques (Fultang)",
    description="API pour extraire, filtrer et servir les cas cliniques.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JSON_SOURCE = "dataset_cas_cliniques_final.json"

@app.get("/")
def read_root():
    return {"status": "online", "message": "API prête."}

@app.get("/api/cases", response_model=List[CasClinique])
def get_all_cases(
    keyword: Optional[str] = Query(None),
    min_age: Optional[int] = Query(None),
    max_age: Optional[int] = Query(None)
):
    # On recharge à chaque appel pour voir les mises à jour
    try:
        manager = ClinicalCaseFilter(JSON_SOURCE)
    except Exception:
        # Si le fichier est cassé ou absent
        return []
        
    results = manager.cases

    if keyword:
        results = manager.filter_by_keyword(keyword)
    
    if min_age is not None or max_age is not None:
        low = min_age if min_age is not None else 0
        high = max_age if max_age is not None else 120
        results = manager.filter_by_age_group(low, high, subset=results)

    return results

@app.get("/api/cases/{case_id}", response_model=CasClinique)
def get_case_detail(case_id: str):
    manager = ClinicalCaseFilter(JSON_SOURCE)
    case = next((c for c in manager.cases if c.id_unique == case_id), None)
    if not case:
        raise HTTPException(status_code=404, detail="Cas clinique non trouvé")
    return case

@app.post("/api/extract/refresh")
def trigger_extraction():
    try:
        from extractor import FultangExtractor
        from transformer import ClinicalCaseTransformer
        
        # 1. Extraction
        ext = FultangExtractor()
        raw = ext.fetch_data_from_api() # Retourne un dict ou None
        
        if not raw:
            raise HTTPException(status_code=502, detail="Impossible de joindre Fultang API")

        # 2. Sauvegarde brute et récupération du path
        filepath = ext.save_raw_data(raw)
        
        # 3. Relecture du fichier brut sauvegardé (pour avoir le wrapper avec 'meta' et le HASH)
        with open(filepath, 'r', encoding='utf-8') as f:
            wrapped_data = json.load(f)

        # 4. Transformation (en passant l'objet wrappé qui contient le hash)
        trans = ClinicalCaseTransformer(wrapped_data)
        cases = trans.process()

        # 5. Sauvegarde Finale
        final_data = [cas.model_dump() for cas in cases]
        with open(JSON_SOURCE, "w", encoding='utf-8') as f:
            json.dump(final_data, f, indent=4, ensure_ascii=False)
            
        return {"status": "success", "message": f"{len(cases)} cas mis à jour."}

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


# --- ENDPOINT PÉDAGOGIQUE ---

class CasPedagogique(BaseModel):
    id_unique: str
    niveau: str
    motif_consultation: str
    donnees_personnelles: DonneesPersonnelles
    mode_de_vie: ModeDeVie
    symptomes: List[Symptome]
    # Optionnels
    diagnostic_physique: Optional[List[DiagnosticPhysique]] = None
    examens_complementaires: Optional[List[ExamenComplementaire]] = None
    message_pedagogique: str

@app.get("/api/cases/{case_id}/learning", response_model=CasPedagogique)
def get_case_for_learning(
    case_id: str, 
    level: str = Query("debutant", enum=["debutant", "intermediaire", "expert"])
):
    manager = ClinicalCaseFilter(JSON_SOURCE)
    case = next((c for c in manager.cases if c.id_unique == case_id), None)
    
    if not case:
        raise HTTPException(status_code=404, detail="Cas non trouvé")

    # On construit la réponse partielle
    response = CasPedagogique(
        id_unique=case.id_unique,
        niveau=level,
        motif_consultation=case.motif_consultation,
        donnees_personnelles=case.donnees_personnelles,
        mode_de_vie=case.mode_de_vie,
        symptomes=case.symptomes,
        diagnostic_physique=case.diagnostic_physique,
        examens_complementaires=case.examens_complementaires,
        message_pedagogique=""
    )

    if level == "intermediaire":
        response.examens_complementaires = None
        response.message_pedagogique = "Intermédiaire : Prescrivez les examens."

    elif level == "expert":
        response.examens_complementaires = None
        response.diagnostic_physique = None
        response.message_pedagogique = "Expert : Hypothèses basées sur l'interrogatoire ?"

    else:
        response.message_pedagogique = "Débutant : Observation complète."

    return response

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)