import pytest
from unittest.mock import MagicMock, AsyncMock
from app.services.parsers.polysomnographie_parser import PolysomnographieParser
from app.services.parsers.polygraphie_ppc_parser import PolygraphiePPCParser
from app.services.parsers.efr_standard_parser import EFRStandardParser
from app.services.parsers.efr_avancee_parser import EFRAvanceeParser

@pytest.mark.asyncio
async def test_polysomnographie_parser():
    parser = PolysomnographieParser(filepath="dummy.pdf", pdf_file_id=1)
    
    mock_text = """
    Rapport de Polysomnographie
    Nom: DUPONT
    Prénom: Jean
    Né le: 12/04/1984
    Age: 42
    Taille: 180 cm
    Poids: 85 kg
    IMC: 26.2
    Date Enregistrement: 10/05/2026
    Index Apnées Hypopnées: 32.5/h
    Index de désaturations: 24.1/h
    SpO2 moyenne: 94.2 %
    SpO2 minimale: 82.0 %
    Efficacité du sommeil: 88.5 %
    Conclusion: Syndrome d'apnées sévère du sommeil.
    """
    
    parser.extract_all_text = MagicMock(return_value=mock_text)
    parser.extract_tables = MagicMock(return_value=[])
    
    db = AsyncMock()
    record = await parser.parse(db)
    
    assert record.patient_nom == "DUPONT"
    assert record.patient_prenom == "Jean"
    assert record.patient_dob == "12/04/1984"
    assert record.patient_age == 42
    assert record.taille == 1.8
    assert record.poids == 85.0
    assert record.imc == 26.2
    assert record.iah == 32.5
    assert record.ido == 24.1
    assert record.spo2_moyenne == 94.2
    assert record.spo2_minimale == 82.0
    assert record.efficacite_sommeil_pct == 88.5
    assert record.severite == "Sévère"
    assert "Syndrome d'apnées" in record.conclusion_texte

@pytest.mark.asyncio
async def test_polygraphie_ppc_parser():
    parser = PolygraphiePPCParser(filepath="dummy.pdf", pdf_file_id=1)
    
    mock_text = """
    Rapport de Polygraphie sous PPC
    Nom: MARTIN
    Prénom: Julie
    Date de naissance: 15/09/1972
    Taille: 165 cm
    Poids: 70 kg
    IMC: 25.7
    Date Enregistrement: 15/05/2026
    IAH résiduel: 2.4/h
    IDO: 3.1/h
    Pression médiane: 8.5 cm H2O
    Pression moyenne: 9.0 cm H2O
    Pression p95: 11.2 cm H2O
    Conclusion: Efficacité PPC satisfaisante.
    """
    
    parser.extract_all_text = MagicMock(return_value=mock_text)
    
    db = AsyncMock()
    record = await parser.parse(db)
    
    assert record.patient_nom == "MARTIN"
    assert record.patient_prenom == "Julie"
    assert record.patient_dob == "15/09/1972"
    assert record.taille == 1.65
    assert record.poids == 70.0
    assert record.imc == 25.7
    assert record.iah_residuel == 2.4
    assert record.ido == 3.1
    assert record.pression_mediane == 8.5
    assert record.pression_moyenne == 9.0
    assert record.pression_p95 == 11.2
    assert record.severite_residuelle == "Normal"

@pytest.mark.asyncio
async def test_efr_standard_parser():
    parser = EFRStandardParser(filepath="dummy.pdf", pdf_file_id=1)
    
    mock_text = """
    Spirométrie standard
    Nom: LOPEZ
    Prénom: Mateo
    Date de naissance: 22/02/1990
    Sexe: M
    Taille: 175 cm
    Poids: 78 kg
    Date examen: 20/05/2026
    Dr Martin
    Clinique Bellevue
    Traitement: Ventolin 100mg
    Interprétation: Tracé normal.
    """
    
    # Mock EFR Table
    # Rows: Parameter, Ref, Pre, Pre%Ref, Post, Post%Ref
    mock_tables = [
        [
            ["VEMS", "4.10", "3.20", "78", "3.80", "92"],
            ["CVF", "4.90", "4.20", "85", "4.70", "95"],
            ["VEMS/CVF", "83", "76", "91", "80", "96"]
        ]
    ]
    
    parser.extract_all_text = MagicMock(return_value=mock_text)
    parser.extract_tables = MagicMock(return_value=mock_tables)
    
    db = AsyncMock()
    record = await parser.parse(db)
    
    assert record.patient_nom == "LOPEZ"
    assert record.patient_prenom == "Mateo"
    assert record.patient_dob == "22/02/1990"
    assert record.genre == "M"
    assert record.taille == 1.75
    assert record.poids == 78.0
    assert record.vems_pre == 3.2
    assert record.vems_pct_ref == 78.0
    assert record.vems_post == 3.8
    assert record.cvf_pre == 4.2
    assert record.cvf_pct_ref == 85.0
    assert record.cvf_post == 4.7
    assert record.vems_cvf_pre == 76.0
    assert record.vems_cvf_post == 80.0
    assert record.traitement_utilise == "Ventolin 100mg"
    # Reversibility: vems_post (3.8) is 18.75% higher than vems_pre (3.2), difference is 0.6L
    assert record.reversibilite_bronchique is True

@pytest.mark.asyncio
async def test_efr_avancee_parser():
    parser = EFRAvanceeParser(filepath="dummy.pdf", pdf_file_id=1)
    
    mock_text = """
    EFR Pléthysmographie
    Nom: SMITH
    Prénom: John
    Date de naissance: 10/10/1980
    Taille: 180 cm
    Poids: 80 kg
    Date examen: 25/05/2026
    Commentaires: Obstruction modérée.
    """
    
    mock_tables = [
        [
            ["CV Lente", "4.50", "4.20"],
            ["VT", "0.60", "0.58"],
            ["VRE", "1.20", "1.10"],
            ["RAW", "1.50", "1.80"],
            ["DLCO", "30.0", "24.0", "80%"],
            ["KCO", "4.50", "4.00", "88%"]
        ]
    ]
    
    parser.extract_all_text = MagicMock(return_value=mock_text)
    parser.extract_tables = MagicMock(return_value=mock_tables)
    
    db = AsyncMock()
    record = await parser.parse(db)
    
    assert record.patient_nom == "SMITH"
    assert record.patient_prenom == "John"
    assert record.patient_dob == "10/10/1980"
    assert record.taille == 1.8
    assert record.poids == 80.0
    assert record.cv_lente == 4.2
    assert record.vt == 0.58
    assert record.vre == 1.10
    assert record.raw == 1.80
    assert record.dlco == 24.0
    assert record.dlco_pct == 80.0
    assert record.kco == 4.0
    assert record.kco_pct == 88.0
