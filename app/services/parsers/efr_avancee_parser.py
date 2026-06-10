import re
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.parsers.base_parser import BaseParser
from app.models.efr_avancee import EFRAvancee

class EFRAvanceeParser(BaseParser):
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

    async def parse(self, db: AsyncSession) -> EFRAvancee:
        text = self.extract_all_text()
        tables = self.extract_tables()

        data = {}

        # 1. Patient info
        # 1. Patient info with lookahead to prevent adjacent labels collision
        match_nom = re.search(r"nom\s*:\s*([A-Za-zÀ-ÿ \t-]+?)(?=\s+(?:sexe|age|nom|pr[ée]nom|num[eé]ro|date|dob|taille|poids)\b|$)", text, re.IGNORECASE)
        match_prenom = re.search(r"pr[é|e]nom\s*:\s*([A-Za-zÀ-ÿ \t-]+?)(?=\s+(?:sexe|age|nom|pr[ée]nom|num[eé]ro|date|dob|taille|poids)\b|$)", text, re.IGNORECASE)
        match_dob = re.search(r"(n[é|e]\s+le|date\s+de\s+naissance)\s*:\s*([\d/]+)", text, re.IGNORECASE)
        match_genre = re.search(r"(?:genre|sexe)\s*:\s*([FfMm])", text, re.IGNORECASE)
        
        data["patient_nom"] = match_nom.group(1).strip() if match_nom else None
        data["patient_prenom"] = match_prenom.group(1).strip() if match_prenom else None
        data["patient_dob"] = match_dob.group(2).strip() if match_dob else None
        data["genre"] = match_genre.group(1).strip().upper() if match_genre and match_genre.group(1) else None

        data["taille"] = self.safe_float(re.search(r"taille(?:\(cm\))?\s*:\s*([\d,.]+)", text, re.IGNORECASE))
        data["poids"] = self.safe_float(re.search(r"poids(?:\(kg\))?\s*:\s*([\d,.]+)", text, re.IGNORECASE))
        data["imc"] = self.safe_float(re.search(r"imc\s*:\s*([\d,.]+)", text, re.IGNORECASE))

        if data["taille"] and data["taille"] > 3.0:
            data["taille"] = data["taille"] / 100.0

        # Exam info
        match_date = re.search(r"date\s+(examen|visite)\s*:\s*([\d/-]+)", text, re.IGNORECASE)
        if match_date:
            data["date_examen"] = match_date.group(2).strip()
        else:
            # Fallback to finding any DD/MM/YYYY date that is NOT the patient's DOB
            all_dates = re.findall(r"\b\d{2}/\d{2}/\d{4}\b", text)
            dob = data.get("patient_dob")
            for d in all_dates:
                if d != dob:
                    data["date_examen"] = d
                    break

        match_dr = re.search(r"(?:dr|docteur)\s+([A-Za-zÀ-ÿ \t-]+?)(?=\s+(?:sexe|age|nom|pr[ée]nom|num[eé]ro|date|dob|taille|poids|clinique)\b|$)", text, re.IGNORECASE)
        data["medecin"] = match_dr.group(1).strip() if match_dr else None
        
        match_clinique = re.search(r"(?:clinique|polyclinique)\s+([A-Za-zÀ-ÿ \t-]+)", text, re.IGNORECASE)
        data["clinique"] = match_clinique.group(1).strip() if match_clinique else None

        # Interpretation
        match_interp = re.search(r"interpr[é|e]tation|commentaires\s*:\s*(.*)", text, re.IGNORECASE | re.DOTALL)
        data["interpretation_texte"] = match_interp.group(1).strip() if match_interp else None

        # Table values extraction
        row_mappings = {
            "cv lente": "cv_lente",
            "cvl": "cv_lente",
            "cv": "cv_lente",
            "vt": "vt",
            "vre": "vre",
            "ci": "ci",
            "ce": "ce",
            "sgaw": "sgaw",
            "gaw": "gaw",
            "sraw": "sraw",
            "raw": "raw",
            "vgt raw": "vgt_raw",
            "vgt (raw)": "vgt_raw",
            "vgt pleth": "vgt_plethysmo",
            "vgt": "vgt_plethysmo",
            "cpt pleth": "cpt_plethysmo",
            "cpt": "cpt_plethysmo",
            "vr pleth": "vr_plethysmo",
            "vr": "vr_plethysmo",
            "cv/cpt": "cv_cpt",
            "cv (cpt)": "cv_cpt",
            "vre/cpt": "vre_cpt",
            "vre (cpt)": "vre_cpt",
            "vre(cpt)": "vre_cpt",
            "cvf": "cvf",
            "vems": "vems",
            "vems/cvf": "vems_cvf_pct",
            "dep": "dep",
            "dem": "dem",
            "dlco": "dlco",
            "dlco %": "dlco_pct",
            "kco": "kco",
            "kco %": "kco_pct",
            "vi": "vi",
            "va": "va",
        }

        def extract_nums(row):
            nums = []
            for cell in row[1:]:
                if cell is None:
                    continue
                cleaned = str(cell).replace(",", ".").replace("%", "").strip()
                match = re.search(r"[-+]?\d*\.\d+|\d+", cleaned)
                if match:
                    nums.append(float(match.group()))
            return nums

        for table in tables:
            for row in table:
                if not row or not row[0]:
                    continue
                # Normalize label
                label = str(row[0]).lower().strip()
                label = label.replace("{", "(").replace("}", ")").replace("[", "(").replace("]", ")")
                # Remove unit suffixes in parentheses
                label = re.sub(
                    r"\((?:l|l/s|%|ml/mmhg/min|ml/mmhg/mi|dlco/l|cmh2o/l/s|1/s\*cmh2o|l/s\*cmh2o|cmh2o\*s|kg|cm|m)\)", 
                    "", 
                    label, 
                    flags=re.IGNORECASE
                ).strip()
                # Clean leading non-alphanumeric chars
                label = re.sub(r"^[^a-z0-9]+", "", label)
                
                matched_key = None
                for k in sorted(row_mappings.keys(), key=len, reverse=True):
                    if label.startswith(k):
                        matched_key = row_mappings[k]
                        break
                
                if matched_key:
                    nums = extract_nums(row)
                    if len(nums) >= 2:
                        val = nums[1]
                        data[matched_key] = val
                        if matched_key == "dlco" and len(nums) > 2:
                            data["dlco_pct"] = nums[2]
                        elif matched_key == "kco" and len(nums) > 2:
                            data["kco_pct"] = nums[2]

        record = EFRAvancee(
            pdf_file_id=self.pdf_file_id,
            **data
        )
        db.add(record)
        await db.flush()
        return record
