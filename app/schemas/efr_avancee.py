from pydantic import BaseModel
from typing import Optional

class EFRAvanceeBase(BaseModel):
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
    cv_lente: Optional[float] = None
    vt: Optional[float] = None
    vre: Optional[float] = None
    ci: Optional[float] = None
    ce: Optional[float] = None
    sgaw: Optional[float] = None
    gaw: Optional[float] = None
    sraw: Optional[float] = None
    raw: Optional[float] = None
    vgt_raw: Optional[float] = None
    vgt_plethysmo: Optional[float] = None
    cpt_plethysmo: Optional[float] = None
    vr_plethysmo: Optional[float] = None
    cv_cpt: Optional[float] = None
    vre_cpt: Optional[float] = None
    cvf: Optional[float] = None
    vems: Optional[float] = None
    vems_cvf_pct: Optional[float] = None
    dep: Optional[float] = None
    dem: Optional[float] = None
    dlco: Optional[float] = None
    dlco_pct: Optional[float] = None
    kco: Optional[float] = None
    kco_pct: Optional[float] = None
    vi: Optional[float] = None
    va: Optional[float] = None
    interpretation_texte: Optional[str] = None

class EFRAvanceeOut(EFRAvanceeBase):
    id: int
    pdf_file_id: int

    class Config:
        from_attributes = True
