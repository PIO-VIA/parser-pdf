from pydantic import BaseModel
from typing import Optional

class PolysomnographieBase(BaseModel):
    patient_nom: Optional[str] = None
    patient_prenom: Optional[str] = None
    patient_dob: Optional[str] = None
    patient_age: Optional[int] = None
    taille: Optional[float] = None
    poids: Optional[float] = None
    imc: Optional[float] = None
    date_enregistrement: Optional[str] = None
    debut_enregistrement: Optional[str] = None
    fin_enregistrement: Optional[str] = None
    iah: Optional[float] = None
    ido: Optional[float] = None
    charge_hypoxique: Optional[float] = None
    iah_obstructif: Optional[float] = None
    iah_central: Optional[float] = None
    iah_mixte: Optional[float] = None
    iah_dorsal: Optional[float] = None
    iah_non_dorsal: Optional[float] = None
    apnees_obstructives_nb: Optional[int] = None
    apnees_centrales_nb: Optional[int] = None
    apnees_mixtes_nb: Optional[int] = None
    hypopnees_nb: Optional[int] = None
    duree_moyenne_apnees: Optional[float] = None
    duree_apnee_plus_longue: Optional[float] = None
    spo2_moyenne: Optional[float] = None
    spo2_minimale: Optional[float] = None
    duree_spo2_sous_90_pct: Optional[float] = None
    charge_hypoxique_valeur: Optional[float] = None
    index_desaturations: Optional[float] = None
    nb_desaturations: Optional[int] = None
    tts_min: Optional[float] = None
    efficacite_sommeil_pct: Optional[float] = None
    latence_endormissement_min: Optional[float] = None
    latence_rem_min: Optional[float] = None
    n1_min: Optional[float] = None
    n2_min: Optional[float] = None
    n3_min: Optional[float] = None
    rem_min: Optional[float] = None
    eveil_intra_min: Optional[float] = None
    micro_eveils_nb: Optional[int] = None
    micro_eveils_index: Optional[float] = None
    mpjs_nb: Optional[int] = None
    mpjs_index: Optional[float] = None
    ronflements_pct: Optional[float] = None
    volume_audio_moyen: Optional[float] = None
    volume_audio_max: Optional[float] = None
    severite: Optional[str] = None
    conclusion_texte: Optional[str] = None
    medecin: Optional[str] = None
    clinique: Optional[str] = None

class PolysomnographieOut(PolysomnographieBase):
    id: int
    pdf_file_id: int

    class Config:
        from_attributes = True
