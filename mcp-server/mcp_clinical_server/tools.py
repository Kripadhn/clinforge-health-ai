"""Clinical tools with patient-scope enforcement.

The EHR API is a trusted back-office service that would return any patient. This layer derives the
clinician from the session token and refuses any patient not assigned to that session.
"""
from typing import Any, Dict, List, Optional

from clinical_shared.ehr import AuthError, EHRApi


class ClinicalTools:
    def __init__(self, ehr: EHRApi) -> None:
        self.ehr = ehr

    def _session(self, token: Optional[str]) -> Dict[str, Any]:
        if not token:
            raise AuthError("missing bearer token")
        return self.ehr.introspect(token)

    def _authorize(self, token: Optional[str], patient_id: str) -> Dict[str, Any]:
        s = self._session(token)
        if patient_id not in s["patient_ids"]:
            raise AuthError("patient not in your care-team scope")
        return s

    def list_my_patients(self, token: Optional[str]) -> List[Dict[str, Any]]:
        s = self._session(token)
        keep = ("id", "first_name", "last_name", "gender", "birth_date")
        return [{k: p[k] for k in keep}
                for p in (self.ehr.get("/patients/%s" % pid) for pid in s["patient_ids"])]

    def get_patient_summary(self, token, patient_id):
        self._authorize(token, patient_id)
        return self.ehr.get("/patients/%s/summary" % patient_id)

    def _list(self, table, token, patient_id, **params):
        self._authorize(token, patient_id)
        return self.ehr.get("/patients/%s/%s" % (patient_id, table), **params)

    def list_conditions(self, token, patient_id, active_only=True):
        return self._list("conditions", token, patient_id, active=True if active_only else None)

    def list_medications(self, token, patient_id, active_only=True):
        return self._list("medications", token, patient_id, active=True if active_only else None)

    def list_careplans(self, token, patient_id, active_only=True):
        return self._list("careplans", token, patient_id, active=True if active_only else None)

    def list_observations(self, token, patient_id, code=None, since=None, limit=50):
        return self._list("observations", token, patient_id, code=code, since=since, limit=limit)

    def list_encounters(self, token, patient_id, since=None, limit=500):
        return self._list("encounters", token, patient_id, since=since, limit=limit)

    def list_claims(self, token, patient_id, status=None):
        return self._list("claims", token, patient_id,
                          extra=("claim_status=" + status) if status else None)

    def get_lab_trend(self, token, patient_id, code):
        self._authorize(token, patient_id)
        return self.ehr.get("/patients/%s/lab-trend" % patient_id, code=code)

    def get_patient_coverage(self, token, patient_id):
        self._authorize(token, patient_id)
        return self.ehr.get("/patients/%s/coverage" % patient_id)

    def get_encounter(self, token, encounter_id):
        s = self._session(token)
        enc = self.ehr.get("/encounters/%s" % encounter_id)
        if enc["patient_id"] not in s["patient_ids"]:
            raise AuthError("encounter belongs to a patient outside your care-team scope")
        return enc

    def find_observation_code(self, token, query):
        self._session(token)  # reference data, but still requires a valid session
        return self.ehr.get("/observation-codes", q=query)
