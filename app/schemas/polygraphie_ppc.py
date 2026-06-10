from pydantic import BaseModel, ConfigDict
from typing import Optional

class PolygraphiePPCBase(BaseModel):
    patient_nom: Optional[str] = None
    patient_prenom: Optional[str] = None
    patient_dob: Optional[str] = None
    taille: Optional[float] = None
    poids: Optional[float] = None
    imc: Optional[float] = None
    date_enregistrement: Optional[str] = None
    iah_residuel: Optional[float] = None
    ido: Optional[float] = None
    iah_dorsal: Optional[float] = None
    iah_non_dorsal: Optional[float] = None
    apnees_obstructives_nb: Optional[int] = None
    apnees_centrales_nb: Optional[int] = None
    hypopnees_nb: Optional[int] = None
    spo2_moyenne: Optional[float] = None
    spo2_minimale: Optional[float] = None
    duree_spo2_sous_90_pct: Optional[float] = None
    pression_mediane: Optional[float] = None
    pression_moyenne: Optional[float] = None
    pression_p95: Optional[float] = None
    efficacite_sommeil_pct: Optional[float] = None
    severite_residuelle: Optional[str] = None
    conclusion_texte: Optional[str] = None

class PolygraphiePPCOut(PolygraphiePPCBase):
    id: int
    pdf_file_id: int

    model_config = ConfigDict(from_attributes=True)
