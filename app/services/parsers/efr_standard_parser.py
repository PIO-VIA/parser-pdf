import re
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.parsers.base_parser import BaseParser
from app.models.efr_standard import EFRStandard

class EFRStandardParser(BaseParser):
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

    async def parse(self, db: AsyncSession) -> EFRStandard:
        text = self.extract_all_text()
        tables = self.extract_tables()

        data = {}

        # 1. Patient info
        match_nom = re.search(r"nom\s*:\s*([A-Za-zÀ-ÿ \t-]+)", text, re.IGNORECASE)
        match_prenom = re.search(r"pr[é|e]nom\s*:\s*([A-Za-zÀ-ÿ \t-]+)", text, re.IGNORECASE)
        match_dob = re.search(r"(n[é|e]\s+le|date\s+de\s+naissance)\s*:\s*([\d/]+)", text, re.IGNORECASE)
        match_genre = re.search(r"(?:genre|sexe)\s*:\s*([FfMm])", text, re.IGNORECASE)
        
        data["patient_nom"] = match_nom.group(1).strip() if match_nom else None
        data["patient_prenom"] = match_prenom.group(1).strip() if match_prenom else None
        data["patient_dob"] = match_dob.group(2).strip() if match_dob else None
        data["genre"] = match_genre.group(1).strip().upper() if match_genre and match_genre.group(1) else None

        data["taille"] = self.safe_float(re.search(r"taille\s*:\s*([\d,.]+)\s*(cm|m)", text, re.IGNORECASE))
        data["poids"] = self.safe_float(re.search(r"poids\s*:\s*([\d,.]+)\s*kg", text, re.IGNORECASE))
        data["imc"] = self.safe_float(re.search(r"imc\s*:\s*([\d,.]+)", text, re.IGNORECASE))

        if data["taille"] and data["taille"] > 3.0:
            data["taille"] = data["taille"] / 100.0

        # Exam info
        match_date = re.search(r"date\s+(examen|visite)\s*:\s*([\d/-]+)", text, re.IGNORECASE)
        data["date_examen"] = match_date.group(2).strip() if match_date else None

        match_dr = re.search(r"(dr|docteur)\s+([A-Za-zÀ-ÿ \t-]+)", text, re.IGNORECASE)
        data["medecin"] = match_dr.group(2).strip() if match_dr else None
        
        match_clinique = re.search(r"clinique\s+([A-Za-zÀ-ÿ \t-]+)", text, re.IGNORECASE)
        data["clinique"] = match_clinique.group(1).strip() if match_clinique else None

        match_tabac = re.search(r"tabagisme|tabac\s*:\s*([A-Za-zÀ-ÿ \t\d-]+)", text, re.IGNORECASE)
        data["tabagisme"] = match_tabac.group(1).strip() if match_tabac else None

        # Traitement
        match_traitement = re.search(r"traitement\s*:\s*([A-Za-zÀ-ÿ \t\d-]+)", text, re.IGNORECASE)
        data["traitement_utilise"] = match_traitement.group(1).strip() if match_traitement else None

        # Interpretation
        match_interp = re.search(r"interpr[é|e]tation\s*:\s*(.*)", text, re.IGNORECASE | re.DOTALL)
        data["interpretation_texte"] = match_interp.group(1).strip() if match_interp else None

        # Table values extraction
        row_mappings = {
            "cvf": "cvf",
            "vems": "vems",
            "vems/cvf": "vems_cvf",
            "vems_cvf": "vems_cvf",
            "dep": "dep",
            "dem25-75": "dem25_75",
            "dem25_75": "dem25_75",
            "dem75": "dem75",
            "dem50": "dem50",
            "dem25": "dem25",
            "cpt": "cpt",
            "vr": "vr",
            "vr/cpt": "vr_cpt_pct",
            "rva": "rva_tot",
            "srva": "srva_tot",
        }

        # Helper to extract numbers from row cells
        def extract_nums(row):
            nums = []
            for cell in row[1:]:
                if cell is None:
                    continue
                # Clean value
                cleaned = str(cell).replace(",", ".").replace("%", "").strip()
                # Find number
                match = re.search(r"[-+]?\d*\.\d+|\d+", cleaned)
                if match:
                    nums.append(float(match.group()))
            return nums

        for table in tables:
            for row in table:
                if not row or not row[0]:
                    continue
                label = str(row[0]).lower().strip()
                # Match label
                matched_key = None
                for k in sorted(row_mappings.keys(), key=len, reverse=True):
                    if k in label:
                        matched_key = row_mappings[k]
                        break
                
                if matched_key:
                    nums = extract_nums(row)
                    if len(nums) >= 2:
                        # Standard EFR table: [Ref, Pre, Pre%Ref, Post, Post%Ref] or similar
                        # Let's map dynamically:
                        if matched_key == "cvf":
                            data["cvf_pre"] = nums[1]
                            data["cvf_pct_ref"] = nums[2] if len(nums) > 2 else None
                            if len(nums) >= 4:
                                data["cvf_post"] = nums[3]
                        elif matched_key == "vems":
                            data["vems_pre"] = nums[1]
                            data["vems_pct_ref"] = nums[2] if len(nums) > 2 else None
                            if len(nums) >= 4:
                                data["vems_post"] = nums[3]
                        elif matched_key == "vems_cvf":
                            data["vems_cvf_pre"] = nums[1]
                            if len(nums) >= 4:
                                data["vems_cvf_post"] = nums[3]
                        elif matched_key == "dep":
                            data["dep_pre"] = nums[1]
                            data["dep_pct_ref"] = nums[2] if len(nums) > 2 else None
                            if len(nums) >= 4:
                                data["dep_post"] = nums[3]
                        elif matched_key == "dem25_75":
                            data["dem25_75_pre"] = nums[1]
                            if len(nums) >= 4:
                                data["dem25_75_post"] = nums[3]
                        elif matched_key == "dem75":
                            data["dem75_pre"] = nums[1]
                        elif matched_key == "dem50":
                            data["dem50_pre"] = nums[1]
                        elif matched_key == "dem25":
                            data["dem25_pre"] = nums[1]
                        elif matched_key == "cpt":
                            data["cpt"] = nums[1]
                        elif matched_key == "vr":
                            data["vr"] = nums[1]
                        elif matched_key == "vr_cpt_pct":
                            data["vr_cpt_pct"] = nums[1]
                        elif matched_key == "rva_tot":
                            data["rva_tot"] = nums[1]
                        elif matched_key == "srva_tot":
                            data["srva_tot"] = nums[1]

        # Calculate reversibility: improvement of VEMS >= 12% and 200ml (0.2L) post
        if data.get("vems_pre") and data.get("vems_post"):
            pre = data["vems_pre"]
            post = data["vems_post"]
            # post must be at least 1.12 * pre and diff >= 0.2
            pct_diff = (post - pre) / pre
            vol_diff = post - pre
            data["reversibilite_bronchique"] = (pct_diff >= 0.12) and (vol_diff >= 0.2)
        else:
            data["reversibilite_bronchique"] = False

        record = EFRStandard(
            pdf_file_id=self.pdf_file_id,
            **data
        )
        db.add(record)
        await db.flush()
        return record
