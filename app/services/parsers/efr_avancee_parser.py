import re
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.parsers.base_parser import BaseParser
from app.models.efr_avancee import EFRAvancee

class EFRAvanceeParser(BaseParser):
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

    async def parse(self, db: AsyncSession) -> EFRAvancee:
        text = self.extract_all_text()
        tables = self.extract_tables()

        data = {}

        # 1. Patient info
        match_nom = re.search(r"nom\s*:\s*([A-Za-zÀ-ÿ\s-]+)", text, re.IGNORECASE)
        match_prenom = re.search(r"pr[é|e]nom\s*:\s*([A-Za-zÀ-ÿ\s-]+)", text, re.IGNORECASE)
        match_dob = re.search(r"(n[é|e]\s+le|date\s+de\s+naissance)\s*:\s*([\d/]+)", text, re.IGNORECASE)
        match_genre = re.search(r"genre|sexe\s*:\s*([FfMm])", text, re.IGNORECASE)
        
        data["patient_nom"] = match_nom.group(1).strip() if match_nom else None
        data["patient_prenom"] = match_prenom.group(1).strip() if match_prenom else None
        data["patient_dob"] = match_dob.group(2).strip() if match_dob else None
        data["genre"] = match_genre.group(1).strip().upper() if match_genre else None

        data["taille"] = self.safe_float(re.search(r"taille\s*:\s*([\d,.]+)\s*(cm|m)", text, re.IGNORECASE))
        data["poids"] = self.safe_float(re.search(r"poids\s*:\s*([\d,.]+)\s*kg", text, re.IGNORECASE))
        data["imc"] = self.safe_float(re.search(r"imc\s*:\s*([\d,.]+)", text, re.IGNORECASE))

        if data["taille"] and data["taille"] > 3.0:
            data["taille"] = data["taille"] / 100.0

        # Exam info
        match_date = re.search(r"date\s+(examen|visite)\s*:\s*([\d/-]+)", text, re.IGNORECASE)
        data["date_examen"] = match_date.group(2).strip() if match_date else None

        match_dr = re.search(r"(dr|docteur)\s+([A-Za-zÀ-ÿ\s-]+)", text, re.IGNORECASE)
        data["medecin"] = match_dr.group(2).strip() if match_dr else None
        
        match_clinique = re.search(r"clinique\s+([A-Za-zÀ-ÿ\s-]+)", text, re.IGNORECASE)
        data["clinique"] = match_clinique.group(1).strip() if match_clinique else None

        # Interpretation
        match_interp = re.search(r"interpr[é|e]tation|commentaires\s*:\s*(.*)", text, re.IGNORECASE | re.DOTALL)
        data["interpretation_texte"] = match_interp.group(1).strip() if match_interp else None

        # Table values extraction
        row_mappings = {
            "cv lente": "cv_lente",
            "cvl": "cv_lente",
            "vt": "vt",
            "vre": "vre",
            "ci": "ci",
            "ce": "ce",
            "sgaw": "sgaw",
            "gaw": "gaw",
            "sraw": "sraw",
            "raw": "raw",
            "vgt raw": "vgt_raw",
            "vgt pleth": "vgt_plethysmo",
            "cpt pleth": "cpt_plethysmo",
            "vr pleth": "vr_plethysmo",
            "cv/cpt": "cv_cpt",
            "vre/cpt": "vre_cpt",
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
                label = str(row[0]).lower().strip()
                matched_key = None
                for k, v in row_mappings.items():
                    if k in label:
                        matched_key = v
                        break
                
                if matched_key:
                    nums = extract_nums(row)
                    if len(nums) >= 2:
                        val = nums[1] # Pre/actual value
                        if matched_key == "cv_lente":
                            data["cv_lente"] = val
                        elif matched_key == "vt":
                            data["vt"] = val
                        elif matched_key == "vre":
                            data["vre"] = val
                        elif matched_key == "ci":
                            data["ci"] = val
                        elif matched_key == "ce":
                            data["ce"] = val
                        elif matched_key == "sgaw":
                            data["sgaw"] = val
                        elif matched_key == "gaw":
                            data["gaw"] = val
                        elif matched_key == "sraw":
                            data["sraw"] = val
                        elif matched_key == "raw":
                            data["raw"] = val
                        elif matched_key == "vgt_raw":
                            data["vgt_raw"] = val
                        elif matched_key == "vgt_plethysmo":
                            data["vgt_plethysmo"] = val
                        elif matched_key == "cpt_plethysmo":
                            data["cpt_plethysmo"] = val
                        elif matched_key == "vr_plethysmo":
                            data["vr_plethysmo"] = val
                        elif matched_key == "cv_cpt":
                            data["cv_cpt"] = val
                        elif matched_key == "vre_cpt":
                            data["vre_cpt"] = val
                        elif matched_key == "cvf":
                            data["cvf"] = val
                        elif matched_key == "vems":
                            data["vems"] = val
                        elif matched_key == "vems_cvf_pct":
                            data["vems_cvf_pct"] = val
                        elif matched_key == "dep":
                            data["dep"] = val
                        elif matched_key == "dem":
                            data["dem"] = val
                        elif matched_key == "dlco":
                            data["dlco"] = val
                            if len(nums) > 2:
                                data["dlco_pct"] = nums[2]
                        elif matched_key == "dlco_pct":
                            data["dlco_pct"] = val
                        elif matched_key == "kco":
                            data["kco"] = val
                            if len(nums) > 2:
                                data["kco_pct"] = nums[2]
                        elif matched_key == "kco_pct":
                            data["kco_pct"] = val
                        elif matched_key == "vi":
                            data["vi"] = val
                        elif matched_key == "va":
                            data["va"] = val

        record = EFRAvancee(
            pdf_file_id=self.pdf_file_id,
            **data
        )
        db.add(record)
        await db.flush()
        return record
