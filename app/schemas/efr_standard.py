from pydantic import BaseModel, ConfigDict
from typing import Optional

class EFRStandardBase(BaseModel):
    patient_nom: Optional[str] = None
    patient_prenom: Optional[str] = None
    patient_dob: Optional[str] = None
    genre: Optional[str] = None
    taille: Optional[float] = None
    poids: Optional[float] = None
    imc: Optional[float] = None
    date_examen: Optional[str] = None
    medecin: Optional[str] = None
    clinique: Optional[str] = None
    tabagisme: Optional[str] = None
    cvf_pre: Optional[float] = None
    cvf_post: Optional[float] = None
    cvf_pct_ref: Optional[float] = None
    vems_pre: Optional[float] = None
    vems_post: Optional[float] = None
    vems_pct_ref: Optional[float] = None
    vems_cvf_pre: Optional[float] = None
    vems_cvf_post: Optional[float] = None
    dep_pre: Optional[float] = None
    dep_post: Optional[float] = None
    dep_pct_ref: Optional[float] = None
    dem25_75_pre: Optional[float] = None
    dem25_75_post: Optional[float] = None
    dem75_pre: Optional[float] = None
    dem25_pre: Optional[float] = None
    dem50_pre: Optional[float] = None
    cpt: Optional[float] = None
    vr: Optional[float] = None
    vr_cpt_pct: Optional[float] = None
    rva_tot: Optional[float] = None
    srva_tot: Optional[float] = None
    reversibilite_bronchique: Optional[bool] = None
    traitement_utilise: Optional[str] = None
    interpretation_texte: Optional[str] = None

class EFRStandardOut(EFRStandardBase):
    id: int
    pdf_file_id: int

    model_config = ConfigDict(from_attributes=True)
