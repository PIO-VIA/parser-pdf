import re
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.parsers.base_parser import BaseParser
from app.models.polysomnographie import Polysomnographie

class PolysomnographieParser(BaseParser):
    def safe_float(self, val) -> float:
        if val is None:
            return None
        try:
            val = str(val).replace(",", ".").strip()
            match = re.search(r"[-+]?\d*\.\d+|\d+", val)
            if match:
                return float(match.group())
            return None
        except Exception:
            return None

    def safe_int(self, val) -> int:
        if val is None:
            return None
        try:
            val = str(val).strip()
            match = re.search(r"[-+]?\d+", val)
            if match:
                return int(match.group())
            return None
        except Exception:
            return None

    async def parse(self, db: AsyncSession) -> Polysomnographie:
        text = self.extract_all_text()
        tables = self.extract_tables()

        data = {}

        # 1. Patient Info
        # Nom / Prenom / DOB
        match_nom = re.search(r"nom\s*:\s*([A-Za-zÀ-ÿ\s-]+)", text, re.IGNORECASE)
        match_prenom = re.search(r"pr[é|e]nom\s*:\s*([A-Za-zÀ-ÿ\s-]+)", text, re.IGNORECASE)
        match_dob = re.search(r"(n[é|e]\s+le|date\s+de\s+naissance)\s*:\s*([\d/]+)", text, re.IGNORECASE)
        
        data["patient_nom"] = match_nom.group(1).strip() if match_nom else None
        data["patient_prenom"] = match_prenom.group(1).strip() if match_prenom else None
        data["patient_dob"] = match_dob.group(2).strip() if match_dob else None

        # Age / Taille / Poids / IMC
        data["patient_age"] = self.safe_int(re.search(r"age\s*:\s*(\d+)", text, re.IGNORECASE))
        data["taille"] = self.safe_float(re.search(r"taille\s*:\s*([\d,.]+)\s*(cm|m)", text, re.IGNORECASE))
        data["poids"] = self.safe_float(re.search(r"poids\s*:\s*([\d,.]+)\s*kg", text, re.IGNORECASE))
        data["imc"] = self.safe_float(re.search(r"imc\s*:\s*([\d,.]+)", text, re.IGNORECASE))

        # Adjust height if it was in cm
        if data["taille"] and data["taille"] > 3.0:
            data["taille"] = data["taille"] / 100.0

        # 2. Recording Info
        match_date = re.search(r"date\s+enregistrement\s*:\s*([\d/-]+)", text, re.IGNORECASE)
        match_debut = re.search(r"d[é|e]but\s+enregistrement\s*:\s*([\d:]+)", text, re.IGNORECASE)
        match_fin = re.search(r"fin\s+enregistrement\s*:\s*([\d:]+)", text, re.IGNORECASE)

        data["date_enregistrement"] = match_date.group(1).strip() if match_date else None
        data["debut_enregistrement"] = match_debut.group(1).strip() if match_debut else None
        data["fin_enregistrement"] = match_fin.group(1).strip() if match_fin else None

        # 3. Respiratory Indices
        data["iah"] = self.safe_float(re.search(r"iah\s*:\s*([\d,.]+)|index\s+apn[é|e]es\s+hypopn[é|e]es\s*:\s*([\d,.]+)", text, re.IGNORECASE))
        data["ido"] = self.safe_float(re.search(r"ido\s*:\s*([\d,.]+)|index\s+de\s+d[é|e]saturation\s*:\s*([\d,.]+)", text, re.IGNORECASE))
        data["charge_hypoxique"] = self.safe_float(re.search(r"charge\s+hypoxique\s*:\s*([\d,.]+)", text, re.IGNORECASE))

        # Obstructive, Central, Mixed, Dorsal, Non-Dorsal IAH
        data["iah_obstructif"] = self.safe_float(re.search(r"iah\s+obstructif\s*:\s*([\d,.]+)|iaho\s*:\s*([\d,.]+)", text, re.IGNORECASE))
        data["iah_central"] = self.safe_float(re.search(r"iah\s+central\s*:\s*([\d,.]+)|iahc\s*:\s*([\d,.]+)", text, re.IGNORECASE))
        data["iah_mixte"] = self.safe_float(re.search(r"iah\s+mixte\s*:\s*([\d,.]+)|iahm\s*:\s*([\d,.]+)", text, re.IGNORECASE))
        data["iah_dorsal"] = self.safe_float(re.search(r"iah\s+dorsal\s*:\s*([\d,.]+)", text, re.IGNORECASE))
        data["iah_non_dorsal"] = self.safe_float(re.search(r"iah\s+non\s*[-|\s]*dorsal\s*:\s*([\d,.]+)", text, re.IGNORECASE))

        # Event Counts
        data["apnees_obstructives_nb"] = self.safe_int(re.search(r"apn[é|e]es\s+obstructives\s*:\s*(\d+)", text, re.IGNORECASE))
        data["apnees_centrales_nb"] = self.safe_int(re.search(r"apn[é|e]es\s+centrales\s*:\s*(\d+)", text, re.IGNORECASE))
        data["apnees_mixtes_nb"] = self.safe_int(re.search(r"apn[é|e]es\s+mixtes\s*:\s*(\d+)", text, re.IGNORECASE))
        data["hypopnees_nb"] = self.safe_int(re.search(r"hypopn[é|e]es\s*:\s*(\d+)", text, re.IGNORECASE))
        data["duree_moyenne_apnees"] = self.safe_float(re.search(r"dur[é|e]e\s+moyenne\s+apn[é|e]es\s*:\s*([\d,.]+)", text, re.IGNORECASE))
        data["duree_apnee_plus_longue"] = self.safe_float(re.search(r"apn[é|e]e\s+la\s+plus\s+longue\s*:\s*([\d,.]+)", text, re.IGNORECASE))

        # SpO2
        data["spo2_moyenne"] = self.safe_float(re.search(r"spo2\s+moyenne\s*:\s*([\d,.]+)", text, re.IGNORECASE))
        data["spo2_minimale"] = self.safe_float(re.search(r"spo2\s+minimale\s*:\s*([\d,.]+)", text, re.IGNORECASE))
        data["duree_spo2_sous_90_pct"] = self.safe_float(re.search(r"dur[é|e]e\s+spo2\s*<\s*90\s*%\s*:\s*([\d,.]+)", text, re.IGNORECASE))
        data["charge_hypoxique_valeur"] = self.safe_float(re.search(r"valeur\s+charge\s+hypoxique\s*:\s*([\d,.]+)", text, re.IGNORECASE))

        # Desaturations
        data["index_desaturations"] = self.safe_float(re.search(r"index\s+des\s+d[é|e]saturations\s*:\s*([\d,.]+)", text, re.IGNORECASE))
        data["nb_desaturations"] = self.safe_int(re.search(r"nombre\s+de\s+d[é|e]saturations\s*:\s*(\d+)", text, re.IGNORECASE))

        # 4. Sleep Stages / Sleep Structure
        # TTS min
        tts_match = re.search(r"dur[é|e]e\s+totale\s+de\s+sommeil\s*:\s*([\d,.]+)\s*(min|h)", text, re.IGNORECASE)
        if tts_match:
            val = self.safe_float(tts_match.group(1))
            unit = tts_match.group(2).lower()
            if "h" in unit:
                data["tts_min"] = val * 60.0
            else:
                data["tts_min"] = val
        else:
            data["tts_min"] = self.safe_float(re.search(r"tts\s*:\s*([\d,.]+)", text, re.IGNORECASE))

        data["efficacite_sommeil_pct"] = self.safe_float(re.search(r"efficacit[é|e]\s+(du\s+)?sommeil\s*:\s*([\d,.]+)", text, re.IGNORECASE))
        data["latence_endormissement_min"] = self.safe_float(re.search(r"latence\s+endormissement\s*:\s*([\d,.]+)", text, re.IGNORECASE))
        data["latence_rem_min"] = self.safe_float(re.search(r"latence\s+rem\s*:\s*([\d,.]+)", text, re.IGNORECASE))

        # Stages duration (min)
        data["n1_min"] = self.safe_float(re.search(r"n1\s*:\s*([\d,.]+)\s*min", text, re.IGNORECASE))
        data["n2_min"] = self.safe_float(re.search(r"n2\s*:\s*([\d,.]+)\s*min", text, re.IGNORECASE))
        data["n3_min"] = self.safe_float(re.search(r"n3\s*:\s*([\d,.]+)\s*min", text, re.IGNORECASE))
        data["rem_min"] = self.safe_float(re.search(r"rem\s*:\s*([\d,.]+)\s*min|sp\s*:\s*([\d,.]+)\s*min", text, re.IGNORECASE))
        data["eveil_intra_min"] = self.safe_float(re.search(r"eveil\s+intra\s*:\s*([\d,.]+)\s*min", text, re.IGNORECASE))

        # 5. Other Indices
        data["micro_eveils_nb"] = self.safe_int(re.search(r"micro-eveils\s*:\s*(\d+)", text, re.IGNORECASE))
        data["micro_eveils_index"] = self.safe_float(re.search(r"index\s+micro-eveils\s*:\s*([\d,.]+)", text, re.IGNORECASE))
        data["mpjs_nb"] = self.safe_int(re.search(r"mpjs\s*:\s*(\d+)", text, re.IGNORECASE))
        data["mpjs_index"] = self.safe_float(re.search(r"index\s+mpjs\s*:\s*([\d,.]+)", text, re.IGNORECASE))
        data["ronflements_pct"] = self.safe_float(re.search(r"ronflements\s*:\s*([\d,.]+)\s*%", text, re.IGNORECASE))
        data["volume_audio_moyen"] = self.safe_float(re.search(r"volume\s+audio\s+moyen\s*:\s*([\d,.]+)", text, re.IGNORECASE))
        data["volume_audio_max"] = self.safe_float(re.search(r"volume\s+audio\s+max\s*:\s*([\d,.]+)", text, re.IGNORECASE))

        # Severity
        if data["iah"] is not None:
            if data["iah"] < 5:
                data["severite"] = "Normal"
            elif data["iah"] < 15:
                data["severite"] = "Léger"
            elif data["iah"] < 30:
                data["severite"] = "Modéré"
            else:
                data["severite"] = "Sévère"
        else:
            data["severite"] = "Normal"

        # 6. Metadata / Header / Conclusion
        match_dr = re.search(r"(dr|docteur)\s+([A-Za-zÀ-ÿ\s-]+)", text, re.IGNORECASE)
        data["medecin"] = match_dr.group(2).strip() if match_dr else None
        
        match_clinique = re.search(r"clinique\s+([A-Za-zÀ-ÿ\s-]+)", text, re.IGNORECASE)
        data["clinique"] = match_clinique.group(1).strip() if match_clinique else None

        match_conclusion = re.search(r"conclusion\s*:\s*(.*)", text, re.IGNORECASE | re.DOTALL)
        data["conclusion_texte"] = match_conclusion.group(1).strip() if match_conclusion else None

        # Try to parse stages from tables if text regex failed
        for table in tables:
            for row in table:
                if not row:
                    continue
                row_str = " ".join([str(cell) for cell in row if cell is not None]).lower()
                if "n1" in row_str and not data["n1_min"]:
                    data["n1_min"] = self.safe_float(row_str)
                if "n2" in row_str and not data["n2_min"]:
                    data["n2_min"] = self.safe_float(row_str)
                if "n3" in row_str and not data["n3_min"]:
                    data["n3_min"] = self.safe_float(row_str)
                if ("rem" in row_str or "sommeil paradoxal" in row_str) and not data["rem_min"]:
                    data["rem_min"] = self.safe_float(row_str)

        # Save to DB
        record = Polysomnographie(
            pdf_file_id=self.pdf_file_id,
            **data
        )
        db.add(record)
        await db.flush()
        return record
