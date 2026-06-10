import re
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.parsers.base_parser import BaseParser
from app.models.polygraphie_ppc import PolygraphiePPC

class PolygraphiePPCParser(BaseParser):
    def safe_float(self, val) -> float:
        if val is None:
            return None
        try:
            if isinstance(val, re.Match):
                group_val = None
                for g in reversed(val.groups()):
                    if g is not None and re.search(r"\d", g):
                        group_val = g
                        break
                val = group_val if group_val is not None else val.group(0)
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
            if isinstance(val, re.Match):
                group_val = None
                for g in reversed(val.groups()):
                    if g is not None and re.search(r"\d", g):
                        group_val = g
                        break
                val = group_val if group_val is not None else val.group(0)
            val = str(val).strip()
            match = re.search(r"[-+]?\d+", val)
            if match:
                return int(match.group())
            return None
        except Exception:
            return None

    async def parse(self, db: AsyncSession) -> PolygraphiePPC:
        text = self.extract_all_text()

        data = {}

        # 1. Patient Info
        # Try to find footer pattern first: "[Nom], [Prénom] Enregistrement du [Date]"
        match_footer = re.search(r"([A-Za-zÀ-ÿ \t-]+?),\s*([A-Za-zÀ-ÿ \t-]+?)\s+Enregistrement\s+du", text, re.IGNORECASE)
        if match_footer:
            data["patient_nom"] = match_footer.group(1).strip()
            data["patient_prenom"] = match_footer.group(2).strip()
        else:
            match_nom = re.search(r"nom\s*:?\s*([A-Za-zÀ-ÿ \t-]+?)(?=\s+(?:id|sexe|age|nom|pr[ée]nom|num[eé]ro|date|dob|taille|poids|genre|n[ée]|nais)\b|$)", text, re.IGNORECASE)
            match_prenom = re.search(r"pr[é|e]nom\s*:?\s*([A-Za-zÀ-ÿ \t-]+?)(?=\s+(?:id|sexe|age|nom|pr[ée]nom|num[eé]ro|date|dob|taille|poids|genre|n[ée]|nais)\b|$)", text, re.IGNORECASE)
            
            full_name = match_nom.group(1).strip() if match_nom and match_nom.group(1) else None
            prenom_val = match_prenom.group(1).strip() if match_prenom and match_prenom.group(1) else None
            
            if prenom_val:
                data["patient_prenom"] = prenom_val
                data["patient_nom"] = full_name
            elif full_name:
                if "," in full_name:
                    parts = full_name.split(",")
                    data["patient_nom"] = parts[0].strip()
                    data["patient_prenom"] = parts[1].strip()
                else:
                    parts = full_name.split()
                    if len(parts) >= 2:
                        # If one word is in ALL CAPS and the other is not, the ALL CAPS one is the Nom
                        caps_words = [w for w in parts if w.isupper() and len(w) > 1]
                        if len(caps_words) == 1:
                            data["patient_nom"] = caps_words[0]
                            data["patient_prenom"] = " ".join([w for w in parts if w != caps_words[0]])
                        else:
                            # Default to: first word is prenom, last word is nom
                            data["patient_prenom"] = parts[0]
                            data["patient_nom"] = " ".join(parts[1:])
                    else:
                        data["patient_nom"] = full_name
                        data["patient_prenom"] = None
            else:
                data["patient_nom"] = None
                data["patient_prenom"] = None

        # DOB extraction
        match_dob = re.search(r"(n[é|e]\s+le|date\s+de\s+naissance)\s*:?\s*([\d/]+)", text, re.IGNORECASE)
        if match_dob:
            data["patient_dob"] = match_dob.group(2).strip()
        else:
            match_age_dob = re.search(r"[âa]ge\s*:?\s*([\d/]{8,10})", text, re.IGNORECASE)
            data["patient_dob"] = match_age_dob.group(1).strip() if match_age_dob else None

        data["taille"] = self.safe_float(re.search(r"taille\s*:?\s*([\d,.]+)", text, re.IGNORECASE))
        data["poids"] = self.safe_float(re.search(r"poids\s*:?\s*([\d,.]+)", text, re.IGNORECASE))
        data["imc"] = self.safe_float(re.search(r"imc\s*:?\s*([\d,.]+)", text, re.IGNORECASE))

        if data["taille"] and data["taille"] > 3.0:
            data["taille"] = data["taille"] / 100.0

        # 2. Recording Info
        match_date = re.search(r"date\s*(?:de\s+)?l?[’']?\s*enregistrement\s*:?\s*([\d/-]+)", text, re.IGNORECASE)
        data["date_enregistrement"] = match_date.group(1).strip() if match_date and match_date.group(1) else None

        # 3. Respiratory Indices (Residual)
        data["iah_residuel"] = self.safe_float(re.search(r"iah\s*(?:r[é|e]siduel)?\s*:?\s*([\d,.]+)|index\s+apn[é|e]es\s+hypopn[é|e]es\s*:?\s*([\d,.]+)", text, re.IGNORECASE))
        data["ido"] = self.safe_float(re.search(r"\bido\b\s*:?\s*([\d,.]+)|index\s+de\s+d[é|e]saturations?\s*:?\s*([\d,.]+)", text, re.IGNORECASE))
        data["iah_dorsal"] = self.safe_float(re.search(r"iah\s+dorsal\s*:?\s*([\d,.]+)", text, re.IGNORECASE))
        data["iah_non_dorsal"] = self.safe_float(re.search(r"iah\s+non\s*[-|\s]*dorsal\s*:?\s*([\d,.]+)", text, re.IGNORECASE))

        data["apnees_obstructives_nb"] = self.safe_int(re.search(r"apn[é|e]es\s+obstructives\s*:?\s*(\d+)", text, re.IGNORECASE))
        data["apnees_centrales_nb"] = self.safe_int(re.search(r"apn[é|e]es\s+centrales\s*:?\s*(\d+)", text, re.IGNORECASE))
        data["hypopnees_nb"] = self.safe_int(re.search(r"hypopn[é|e]es\s*:?\s*(\d+)", text, re.IGNORECASE))

        # SpO2
        data["spo2_moyenne"] = self.safe_float(re.search(r"spo2\s+moyenne\s*:?\s*([\d,.]+)", text, re.IGNORECASE))
        data["spo2_minimale"] = self.safe_float(re.search(r"spo2\s+(?:minimale|la\s+plus\s+faible)\s*:?\s*([\d,.]+)", text, re.IGNORECASE))
        data["duree_spo2_sous_90_pct"] = self.safe_float(re.search(r"dur[é|e]e\s+spo2\s*<\s*90\s*%\s*:?\s*([\d,.]+)", text, re.IGNORECASE))

        # Pressures
        data["pression_mediane"] = self.safe_float(re.search(r"pression\s+m[é|e]diane\s*:?\s*([\d,.]+)", text, re.IGNORECASE))
        data["pression_moyenne"] = self.safe_float(re.search(r"pression\s+moyenne\s*:?\s*([\d,.]+)", text, re.IGNORECASE))
        data["pression_p95"] = self.safe_float(re.search(r"pression\s+(?:au\s+)?(?:p95|95e\s+percentile|95e\s+centile|95ème\s+centile|95ème\s+percentile)\s*:?\s*([\d,.]+)", text, re.IGNORECASE))

        # Sleep/Recording efficiency
        data["efficacite_sommeil_pct"] = self.safe_float(re.search(r"efficacit[é|e]\s+(?:du\s+)?sommeil\s*:?\s*([\d,.]+)", text, re.IGNORECASE))

        # Severity residuelle
        if data["iah_residuel"] is not None:
            if data["iah_residuel"] < 5:
                data["severite_residuelle"] = "Normal"
            elif data["iah_residuel"] < 15:
                data["severite_residuelle"] = "Léger"
            elif data["iah_residuel"] < 30:
                data["severite_residuelle"] = "Modéré"
            else:
                data["severite_residuelle"] = "Sévère"
        else:
            data["severite_residuelle"] = "Normal"

        match_conclusion = re.search(r"conclusion\s*:?\s*(.*)", text, re.IGNORECASE | re.DOTALL)
        data["conclusion_texte"] = match_conclusion.group(1).strip() if match_conclusion and match_conclusion.group(1) else None

        record = PolygraphiePPC(
            pdf_file_id=self.pdf_file_id,
            **data
        )
        db.add(record)
        await db.flush()
        return record
